import common

_DEFAULT_BLOCKSIZE = 4096


"""
Receives a readable stream
Returns
	1 - The total number of blocks,
	2 - A dictionary of dictionaries, like so:
	{ weakhash : {
		stronghash1 : [ offset1, offset3, ... ]
		stronghash2 : [ offset2 ]
		}
	}
Consider that a weak hash can have several matching strong hashes, and every
(weak hash, strong hash) block pair can occur on several parts of the file,
but we only need one offset for retrieving that block
"""
async def block_checksums(instream, blocksize=_DEFAULT_BLOCKSIZE):
	hashes = {}
	block = await instream.read(blocksize)
	offset = 0

	while block:
		common.populate_block_checksums(block, hashes, offset)
		offset += blocksize
		block = await instream.read(blocksize)

	return offset/blocksize, hashes


"""
Used by the system with an unpatched file upon receiving a hash blueprint of the patched file
Receives an aiofiles input stream and set of hashes for a patched file
Returns:
	1 - A list of tuples where the first element is the local offset and the second
	    is a list of final offsets
	    [ (0, [352, 368, 384, 400, 416, 432]) ]
	2 - A dictionary where each key is a missing block's first offset and the values are
	    tuples with its (weak, strong, offsets)
	    464 : (598213681, b'\x80\xfd\xa7T[\x1f\xc3\xf7\n\xf9V\xe7\xcb\xdf3\xbf', [464, 480]) 
The blocks needed to request can be obtained with list(remote_instructions.keys())
"""


async def get_instructions(datastream, remote_hashes, blocksize=_DEFAULT_BLOCKSIZE):
	match = True
	local_offset = -blocksize
	local_instructions = []

	while True:
		if match and datastream is not None:
			# Whenever there is a match or the loop is running for the first
			# time, populate the window using weakchecksum instead of rolling
			# through every single byte which takes at least twice as long.
			block = bytearray(await datastream.read(blocksize))
			local_offset += blocksize
			checksum = common.adler32(block)
		#match = False

		match = common.check_block(block, checksum, remote_hashes, local_instructions, local_offset)

		if not match:
			# The current block wasn't matched
			if datastream:
				try:
					# Get the next byte and affix to the window
					newbyte = ord(await datastream.read(1))
					block.append(newbyte)
				except TypeError:
					# No more data from the file; the window will slowly shrink.
					# "newbyte" needs to be zero from here on to keep the checksum correct.
					newbyte = 0  # Not necessary to add to the window
					tailsize = await datastream.tell() % blocksize
					datastream = None

			if datastream is None and len(block) <= tailsize:
				# The likelihood that any blocks will match after this is
				# nearly nil so call it quits.
				break

			# Remove the first byte from the window and cheaply calculate
			# the new checksum for it using the previous checksum
			oldbyte = block.pop(0)
			local_offset += 1
			checksum = common.adler32_roll(checksum, oldbyte, newbyte, blocksize)

	# Now put the block offsets in a dictionary where the key is the first offset
	remote_instructions = {offsets[0]: (weak, strong, offsets)
						   for weak, strongs in remote_hashes.items()
						   for strong, offsets in strongs.items()}

	return local_instructions, remote_instructions


"""
! This function is a generator !
Receives an instream and a list of offsets
Yields the blocks in that instream at those offsets
"""
async def get_blocks(datastream, requests, blocksize=_DEFAULT_BLOCKSIZE):
	for offset in requests:
		await datastream.seek(offset)
		content = await datastream.read(blocksize)
		yield (offset, content)


"""
Receives a readable instream, a writable outstream, a list of instructions and a blocksize
Sets outstream to the expected size with the blocks from instream in their positions according to the blueprint
WARNING: There is a possibility that a local block will overwrite another
if the instream and outstream are the same. Avoid this by using different streams.
"""
async def patch_local_blocks(instream, outstream, local_instructions, blocksize=_DEFAULT_BLOCKSIZE):
	for instruction in local_instructions:
		local_offset = instruction[0]
		final_offsets = instruction[1]

		await instream.seek(local_offset)
		block = await instream.read(blocksize)

		for offset in final_offsets:
			await outstream.seek(offset)
			await outstream.write(block)


"""
Receives a list of tuples of missing blocks in the form (offset, content),
a dictionary with remote instructions (2nd result of get_instructions) and a writable outstream
Sets those those offsets in the outstream to their expected content according to the instructions
If check_hashes is set to True, it will also confirm that both the weak and strong hash match the expected
"""
async def patch_remote_blocks(remote_blocks, outstream, remote_instructions, check_hashes=False):
	for first_offset, block in remote_blocks:
		# Optionally check if this block's hashes match the expected hashes
		instruction = remote_instructions[first_offset]
		if check_hashes and (common.adler32(block) != instruction[0] or common.stronghash(block) != instruction[1]):
			#print(str(first_offset)+" had an error:\n"+str(common.adler32(block))+" != "+str(instruction[0])+" or "+str(common.stronghash(block))+" != "+str(instruction[1]))
			raise Exception
		for offset in instruction[2]:
			await outstream.seek(offset)
			await outstream.write(block)

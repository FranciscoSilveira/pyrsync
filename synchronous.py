from zsync_hashing import adler32, adler32_roll, stronghash

_DEFAULT_BLOCKSIZE = 4096


"""
Receives a readable stream
Returns a dictionary of dictionaries, like so:
	{ weakhash : {
		stronghash1 : [ offset1, offset3, ... ]
		stronghash2 : [ offset2 ]
		}
	}
Consider that a weak hash can have several matching strong hashes, and every
(weak hash, strong hash) block pair can occur on several parts of the file,
but we only need one offset for retrieving that block
"""
def block_checksums(instream, blocksize=_DEFAULT_BLOCKSIZE):
	"""
	Generator of (weak hash (int), strong hash(bytes)) tuples
	for each block of the defined size for the given data stream.
	"""
	hashes = {}
	read = instream.read(blocksize)
	offset = 0
	while read:
		weak = adler32(read)
		strong = stronghash(read)
		try:
			hashes[weak][strong]
		except KeyError:
			hashes[weak] = {}

		try:
			hashes[weak][strong].append(offset)
		except KeyError:
			hashes[weak][strong] = [offset]

		offset += blocksize
		read = instream.read(blocksize)

	return offset/blocksize,hashes


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
def get_instructions(datastream, remote_hashes, blocksize=_DEFAULT_BLOCKSIZE):
	match = True
	local_offset = -blocksize
	local_instructions = []

	while True:
		if match and datastream is not None:
			# Whenever there is a match or the loop is running for the first
			# time, populate the window using weakchecksum instead of rolling
			# through every single byte which takes at least twice as long.
			window = bytearray(datastream.read(blocksize))
			local_offset += blocksize
			checksum = adler32(window)
		
		match = False

		if checksum in remote_hashes:
			# Matched the weak hash
			strong = stronghash(window)
			try:
				remote_offset = remote_hashes[checksum][strong]
				# Matched the strong hash too, so the local block matches to a remote block
				match = True
				local_instructions.append((local_offset, remote_offset))

				# After the block match we don't care about this block anymore,
				# so remove it from the dictionary
				del remote_hashes[checksum][strong]
				if not remote_hashes[checksum]: # empty dicts evaluate to false
					del remote_hashes[checksum]
			except KeyError:
				# Did not match the strong hash
				pass

		if not match:
			# The current block wasn't matched
			if datastream:
				try:
					# Get the next byte and affix to the window
					newbyte = ord(datastream.read(1))
					window.append(newbyte)
				except TypeError:
					# No more data from the file; the window will slowly shrink.
					# "newbyte" needs to be zero from here on to keep the checksum correct.
					newbyte = 0 # Not necessary to add to the window
					tailsize = datastream.tell() % blocksize
					datastream = None

			if datastream is None and len(window) <= tailsize:
				# The likelihood that any blocks will match after this is
				# nearly nil so call it quits.
				break

			# Remove the first byte from the window and cheaply calculate 
			# the new checksum for it using the previous checksum
			oldbyte = window.pop(0)
			local_offset += 1
			checksum = adler32_roll(checksum, oldbyte, newbyte, blocksize)

	# Now put the block offsets in a dictionary where the key is the first offset
	remote_instructions = { offsets[0] : (weak, strong, offsets)
		for weak, strongs in remote_hashes.items()
		for strong, offsets in strongs.items() }

	return local_instructions, remote_instructions


"""
! This function is a generator !
Receives an instream and a list of offsets
Yields the blocks in that instream at those offsets
"""
def get_blocks(datastream, requests, blocksize=_DEFAULT_BLOCKSIZE):
	for offset in requests:
		datastream.seek(offset)
		content = datastream.read(blocksize)
		yield (offset, content)


"""
Receives a readable instream, a writable outstream, a list of instructions and a blocksize
Sets outstream to the expected size with the blocks from instream in their positions according to the blueprint
WARNING: There is a possibility that a local block will overwrite another
if the instream and outstream are the same. Avoid this by using different streams.
"""
def patch_local_blocks(instream, outstream, local_instructions, blocksize=_DEFAULT_BLOCKSIZE):
	for instruction in local_instructions:
		local_offset = instruction[0]
		final_offsets = instruction[1]

		instream.seek(local_offset)
		block = instream.read(blocksize)

		for offset in final_offsets:
			outstream.seek(offset)
			outstream.write(block)


"""
Receives a list of tuples of missing blocks in the form (offset, content),
a dictionary with remote instructions (2nd result of get_instructions) and a writable outstream
Sets those those offsets in the outstream to their expected content according to the instructions
If check_hashes is set to True, it will also confirm that both the weak and strong hash match the expected
"""
def patch_remote_blocks(remote_blocks, outstream, remote_instructions, check_hashes=False):
	for first_offset, block in remote_blocks:
		# Optionally check if this block's hashes match the expected hashes
		instruction = remote_instructions[first_offset]
		if check_hashes and (adler32(block) != instruction[0] or stronghash(block) != instruction[1]):
			#print(str(first_offset)+" had an error:\n"+str(adler32(block))+" != "+str(instruction[0])+" or "+str(stronghash(block))+" != "+str(instruction[1]))
			raise Exception
		for offset in instruction[2]:
			outstream.seek(offset)
			outstream.write(block)

from zsync_hashing import adler32, adler32_roll, stronghash

_DEFAULT_BLOCKSIZE = 4096


"""
Receives a readable stream
Returns a dictionary of dictionaries, like so:
	{ weakhash : {
		stronghash1 : index1,
		stronghash2 : index2
		}
	}
Consider that a weakhash can have several matching stronghashes, and every
weakhash,stronghash pair can occur on several indexes of the file,
but we only need one index for retrieving that block
"""
def block_checksums(instream, blocksize=_DEFAULT_BLOCKSIZE):
	"""
	Generator of (weak hash (int), strong hash(bytes)) tuples
	for each block of the defined size for the given data stream.
	"""
	hashes = {}
	read = instream.read(blocksize)
	index = 0

	while read:
		weak = adler32(read)
		strong = stronghash(read).digest()
		if weak in hashes:
			if strong in hashes[weak]:
				hashes[weak][strong].append(index)
			else:
				hashes[weak][strong] = [ index ]
		else:
			hashes[weak] = {}
			hashes[weak][strong] = [ index ]
		index += 1
		read = instream.read(blocksize)

	return index,hashes


"""
Used by the system with an unpatched file upon receiving a hash blueprint of the patched file
Receives an input stream and set of hashes for a patched file
Returns a dictionary of checksums in the form of:
{
	weakhash1 : {
		stronghash1 : [block1, block2]   <= When a remote block has no local match
		stronghash2 : (local_offset,      <= When a remote block matched a local block
			[ block3, block4 ])
}

Example:
{
	876414430 : {b"\xf4\xdc\xc7'v\xc8L\x11G\xa5\xa2C9\x10\xbe\xce": [43]},
	848365122 : {b'\xa8g\xa5\x16\xe5\xd7\x81\xf3\x11\xaa\x1b\xb5\x8f\xc9\xa2K': (2320, [23, 2548])}
}
"""
def zsync_delta(datastream, remote_hashes, blocksize=_DEFAULT_BLOCKSIZE):
	match = True
	local_offset = -blocksize

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
			strong = stronghash(window).digest()
			if strong in remote_hashes[checksum]:				
				# Matched the weak and strong hashes (block match)
				match = True
				
				remote_offset = remote_hashes[checksum][strong]
				if type(remote_offset) == list:
					# This local block hadn't been matched to a remote block yet
					remote_hashes[checksum][strong] = (local_offset, remote_offset)
				# No need to check otherwise because it's a local block that already matched the remote blocks
				#else: # tuple
				#	# This local block was matched to a remote block already
				#	remote_offset[1].append(local_offset)

		if not match:
			# The current block wasn't matched
			if datastream:
				try:
					# Get the next byte and affix to the window
					newbyte = ord(datastream.read(1))
					window.append(newbyte)
				except TypeError:
					# No more data from the file; the window will slowly shrink.
					# newbyte needs to be zero from here on to keep the checksum
					# correct.
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
	
	# Order the results into a proper blueprint+requestlist tuple and return it
	#return get_instructions(remote_hashes, num_blocks, blocksize)
	return remote_hashes


"""
Receives a dictionary of checksums like the output of zsync_delta
Returns a list that represents a blueprint for patching the file and a list of block indexes missing (the output of get_instructions):

"""
def get_blueprint(remote_hashes, num_blocks, blocksize=_DEFAULT_BLOCKSIZE):
	instructions = [None] * num_blocks
	missing = []
	for weak in remote_hashes:
		for strong in remote_hashes[weak]:
			blocks = remote_hashes[weak][strong]
			if type(blocks) == list:
				# Missing block, just add the checksums
				missing.append(blocks[0])
				for position in blocks:
					instructions[position] = (blocks[0], weak, strong)
					
			else: # Tuple
				# Local block
				for position in blocks[1]:
					local_offset = blocks[0]
					instructions[position] = local_offset
	return instructions, missing


def get_blocks(datastream, requests, blocksize=_DEFAULT_BLOCKSIZE):
	#blocks = []
	for index in requests:
		offset = index*blocksize
		datastream.seek(offset)
		content = datastream.read(blocksize)
		#blocks.append((offset, block))
		yield (index, content)


"""
Receives a readable instream, a writable outstream, a list of instructions and a blocksize
Sets outstream to the expected size with the local blocks in their positions
WARNING: There is a remote possibility that a local block will overwrite another
if the instream and outstream are the same
"""
def patch_local_blocks(instream, outstream, local_blocks, blocksize=_DEFAULT_BLOCKSIZE):
	for element in local_blocks:
		if type(element) == int and blocksize:
			instream.seek(element)
			block = instream.read(blocksize)
			outstream.write(block)
		else:
			# Advance 1 block from current position so the file has the correct size
			outstream.seek(blocksize, 1)

"""
Receives a writable outstream, a list of tuples of missing blocks in the form (block, content) and a blocksize
Sets those blocks to their expected content
"""
def patch_remote_blocks(outstream, remote_blocks, blocksize=_DEFAULT_BLOCKSIZE):
	for index,block in remote_blocks:
		if isinstance(index, int) and isinstance(block, bytes):
			outstream.seek(index*blocksize)
			outstream.write(block)
"""
DEPRECATED I guess
"""
def easy_patch(instream, outstream, local_blocks, remote_blocks, blocksize=_DEFAULT_BLOCKSIZE):
	patch_local_blocks(instream, outstream, local_blocks, blocksize)
	patch_remote_blocks(outstream, remote_blocks, blocksize)


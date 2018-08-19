import filecmp
import argparse

unpatched_file = "tests/loremipsum" # "tests/BABD"
patched_file = "tests/loremipsum_modified" # "tests/ABC"
result_file = "tests/loremipsum_result"
blocksize = 16
verbose = False
very_verbose = False

def print_hashes(num, hashlist):
	print(str(num)+" blocks")
	for h in hashlist:
		print(str(h)+" : "+str(hashlist[h]))
	print()

def print_delta(delta):
	for h in delta:
		print(str(h)+" : "+str(delta[h]))
	print()

def print_instructions(local_instructions, remote_instructions, missing):
	print("Local instructions:")
	for i in local_instructions:
		print(i)
	print("Remote instructions:")
	for i in remote_instructions:
		print(str(i)+" : "+str(remote_instructions[i]))
	print("I need the following blocks: \n"+str(missing)+"\n")

def print_missing(blocks):
	for b in blocks:
		print(b)
	print()

async def asynchronous_test():
	import aiofiles
	
	# Clear result file
	if verbose: print("Clearing result file "+result_file)
	async with aiofiles.open(result_file, "wb") as f:
		f.write()
	
	# Get hashlist from patched file
	async with aiofiles.open(patched_file, "rb") as f:
		num,hashes = await zsync.block_checksums(f, blocksize=blocksize)
	print_hashes(hashes)
	
	# Get the hash delta from the unmodified file
	async with aiofiles.open(unpatched_file, "rb") as f:
		delta = await zsync.zsync_delta(f, hashes, blocksize=blocksize)
	instructions,missing = zsync.get_blueprint(delta, num)
	
	# Get the missing blocks from the patched file
	with open(patched_file, "rb") as f:
		blocks = [b for b in zsync.get_blocks(f, missing, size)]
	
	# Patch the result file
	with open(unpatched_file, "rb") as unpatched, \
				open(patched_file, "rb") as patched, \
				open(result_file, "wb") as result:
		zsync.easy_patch(unpatched, result, instructions, blocks, blocksize)
	
	print("Comparing input and patched")
	async with aiofiles.open(result_file, "rb") as result,\
			aiofiles.open(patched_file, "rb") as patched:
		a = await result.read(blocksize)
		b = await patched.read(blocksize)
		if a != b:
			if verbose: print("Mismatch")
			return False
		if verbose: print("Match")
		return True


def synchronous_test():

	# Clear result file
	if verbose: print("Clearing result file "+result_file)
	with open(result_file, "wb"):
		pass

	# Generate the hash list for the main file
	if verbose: print("Getting hashlist from "+patched_file)
	with open(patched_file, "rb") as f:
		num, hashes = zsync.block_checksums(f, blocksize=blocksize)
	if very_verbose: print_hashes(num, hashes)

	# Get the delta
	if verbose: print("Getting delta from "+unpatched_file)
	with open(unpatched_file, "rb") as f:
		local, remote = zsync.get_instructions(f, hashes, blocksize=blocksize)
	missing = list(remote.keys())
	if very_verbose: print_instructions(local, remote, missing)

	# Get the blocks from the local file and write them to the result file
	if verbose: print("Getting existing blocks from "+unpatched_file+" and writing them to " +result_file)
	with open(unpatched_file, "rb") as unpatched, \
			open(result_file, "wb") as result:
		zsync.patch_local_blocks(unpatched, result, local, blocksize)

	# Get the missing blocks from the patched file
	if verbose: print("Getting missing blocks from "+patched_file)
	with open(patched_file, "rb") as f:
		blocks = [b for b in zsync.get_blocks(f, missing, blocksize)]
	if very_verbose: print_missing(blocks)

	# Patch the result file with the missing blocks
	if verbose: print("Writing missing blocks from "+patched_file+" to "+result_file)
	with open(result_file, "r+b") as result: # This opens the result file for updating in binary
		zsync.patch_remote_blocks(blocks, result, remote, check_hashes=True)

	# Compare the results
	if (filecmp.cmp(patched_file, result_file, shallow=False)):
		print("Success")
		return True
	else:
		print("Failure")
		return False

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-a", "--async", "--asynchronous", action="store_true", dest="asynchronous")
	parser.add_argument("-b", "--blocksize", action="store", dest="blocksize")
	parser.add_argument("-v", "--verbose", action="store_true", dest="verbose")
	parser.add_argument("-vv", "--very-verbose", action="store_true", dest="very_verbose")
	args = parser.parse_args()
	if args.blocksize:
		blocksize = args.blocksize
	very_verbose = args.very_verbose
	verbose = (args.verbose or very_verbose)
	
	if verbose:
		print("Blocksize: "+str(blocksize))
	
	if args.asynchronous:
		import asyncio
		import asynchronous as zsync
		loop = asyncio.get_event_loop()
		loop.run_until_complete(asynchronous_test())
	else:
		import synchronous as zsync
		synchronous_test()

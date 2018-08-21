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
	# Clear result file
	if verbose: print("Clearing result file " + result_file)
	async with aiofiles.open(result_file, "wb") as f:
		pass

	# Get hashlist from patched file
	if verbose: print("Getting hashlist from " + patched_file)
	async with aiofiles.open(patched_file, "rb") as f:
		num,hashes = await zsync.block_checksums(f, blocksize=blocksize)
	if very_verbose: print_hashes(num, hashes)

	# Get the instructions
	if verbose: print("Getting instructions from " + unpatched_file)
	async with aiofiles.open(unpatched_file, "rb") as f:
		local, remote = await zsync.get_instructions(f, hashes, blocksize=blocksize)
	missing = list(remote.keys())
	if very_verbose: print_instructions(local, remote, missing)

	# Get the blocks from the local file and write them to the result file
	if verbose: print("Getting existing blocks from " + unpatched_file + " and writing them to " + result_file)
	async with aiofiles.open(unpatched_file, "rb") as unpatched, \
			aiofiles.open(result_file, "wb") as result:
		await zsync.patch_local_blocks(unpatched, result, local, blocksize)

	# Get the missing blocks from the patched file
	if verbose: print("Getting missing blocks from " + patched_file)
	async with aiofiles.open(patched_file, "rb") as f:
		blocks = [ b async for b in zsync.get_blocks(f, missing, blocksize) ]
	if very_verbose: print_missing(blocks)

	# Patch the result file with the missing blocks
	if verbose: print("Writing missing blocks from " + patched_file + " to " + result_file)
	async with aiofiles.open(result_file, "r+b") as result:  # This opens the result file for updating in binary
		await zsync.patch_remote_blocks(blocks, result, remote, check_hashes=True)


def synchronous_test():
	# Clear result file
	if verbose: print("Clearing result file "+result_file)
	with open(result_file, "wb"):
		pass

	# Generate the hash list for the patched file
	if verbose: print("Getting hashlist from "+patched_file)
	with open(patched_file, "rb") as f:
		num, hashes = zsync.block_checksums(f, blocksize=blocksize)
	if very_verbose: print_hashes(num, hashes)

	# Get the instructions
	if verbose: print("Getting instructions from "+unpatched_file)
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
		import aiofiles
		print("Running asynchronous test")
		loop = asyncio.get_event_loop()
		loop.run_until_complete(asynchronous_test())
	else:
		import synchronous as zsync
		print("Running synchronous test")
		synchronous_test()
	if (filecmp.cmp(patched_file, result_file, shallow=False)):
		print("Success")
		exit(0)
	else:
		print("Failure")
		exit(1)

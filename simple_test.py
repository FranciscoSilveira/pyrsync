import pyzsync
import aiofiles
import asyncio

unpatched_file = "/home/francisco/loremipsum"
patched_file = "/home/francisco/loremipsum_modified"
result_file = "/home/francisco/loremipsum_result"
size = 16

async def sync_files():
	print("Clearing "+result_file)
	async with aiofiles.open(result_file, "wb") as f:
		f.write()
	print("Getting hashlist from "+patched_file)
	async with aiofiles.open(patched_file, "rb") as f:
		num,hashes = await pyzsync.block_checksums(f, blocksize=size)
	print(str(num)+" hashes")
	for h in hashes:
		print(str(h)+" : "+str(hashes[h]))
	for h in hashes:
		for l in hashes[h]:
			if len(l) != 2:
				print("Short: "+str(hashes[h]))

	print("\nGetting delta from "+unpatched_file)
	async with aiofiles.open(unpatched_file, "rb") as f:
		delta = await pyzsync.zsync_delta(f, hashes, blocksize=size)
	instructions,missing = pyzsync.get_blueprint(delta, num)
	print("Blueprint: "+str(instructions))
	print("I need the following blocks: "+str(missing))

	print("Getting missing blocks from "+result_file)
	with open(patched_file, "rb") as f:
		blocks = [b for b in pyzsync.get_blocks(f, missing, size)]
	print("Missing blocks: "+str(blocks))

	print("Patching "+result_file)
	with open(unpatched_file, "rb") as unpatched, \
				open(patched_file, "rb") as patched, \
				open(result_file, "wb") as result:
		pyzsync.easy_patch(unpatched, result, instructions, blocks, size)
	
	print("Comparing input and patched")
	async with aiofiles.open(result_file, "rb") as result,\
			aiofiles.open(patched_file, "rb") as patched:
		a = await result.read(size)
		b = await patched.read(size)
		if a != b:
			print("Mismatch")
			return
		print("Match")

loop = asyncio.get_event_loop()
loop.run_until_complete(sync_files())

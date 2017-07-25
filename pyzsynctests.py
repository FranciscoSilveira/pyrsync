import pyzsync
import filecmp

unpatched_file = "/home/francisco/loremipsum"
patched_file = "/home/francisco/loremipsum_modified"
resulting_file = "/home/francisco/loremipsum_result" # this one gets cleared by the open(...,"wb") call
blocksize = 32
with open(unpatched_file, "rb") as unpatched, open(patched_file, "rb") as patched, open(resulting_file, "wb") as result:
	hashes = pyzsync.block_checksums(patched, blocksize=blocksize)

	instructions, to_request = pyzsync.zsync_delta(unpatched, hashes, blocksize=blocksize)
	#print("Instructions for new file:")
	#for i in instructions:
	#	print("  "+str(i))
	#print("I need to request the following blocks:")
	#for r in to_request:
	#	print("  "+str(r))

	blocks = pyzsync.get_blocks(patched, to_request, blocksize)
	#print("Obtained blocks:")
	#for block in blocks:
	#	print(str(block))
	instructions = pyzsync.merge_instructions_blocks(instructions, blocks, blocksize)
	#print("Final instructions:")
	#for i in instructions:
	#	print("  "+str(i))

	print("Patching file...")
	pyzsync.patchstream(unpatched, result, instructions, blocksize)

if filecmp.cmp(patched_file, resulting_file, shallow=False):
	print("pyzsync works")
else:
	print("pyzsync sucks")
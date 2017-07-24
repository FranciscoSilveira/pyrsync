import pyrsync2

unpatched_file = "/home/francisco/loremipsum"
patched_file = "/home/francisco/loremipsum_modified"
blocksize = 32
with open(unpatched_file, "rb") as unpatched, open(patched_file, "rb") as patched:
	hashes = pyrsync2.blockchecksums(patched, blocksize=blocksize)
	instructions, to_request = pyrsync2.zsyncdelta(unpatched, hashes, blocksize=blocksize)
	print("Instructions for new file:")
	for i in instructions:
		print("  "+str(i))
	print("I need to request the following blocks:")
	for r in to_request:
		print("  "+str(r))
	#	count += 1
	#print(str(count*blocksize)+" bytes")
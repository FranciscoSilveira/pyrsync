import pyrsync2

unpatched_file = "/home/francisco/loremipsum"
patched_file = "/home/francisco/loremipsum_modified"
blocksize = 32
with open(unpatched_file, "rb") as unpatched, open(patched_file, "rb") as patched:
	hashes = pyrsync2.blockchecksums(patched, blocksize=blocksize)
	delta = pyrsync2.zsyncdelta(unpatched, hashes, blocksize=blocksize)
	count = 0
	#for d in delta:
		#print(str(d))
	#	count += 1
	#print(str(count*blocksize)+" bytes")
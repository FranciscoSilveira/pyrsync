import sync
import filecmp

unpatched_file = "loremipsum"
patched_file = "loremipsum_modified"
result_file = "loremipsum_result"
size = 16

print("Getting hashlist from "+patched_file)
with open(patched_file, "rb") as f:
	num,hashes = sync.block_checksums(f, blocksize=size)
print(num)
for h in hashes:
	print(str(h)+" : "+str(hashes[h]))
for h in hashes:
	for l in hashes[h]:
		if len(l) < 2:
			print("Short: "+str(hashes[h]))

print("\nGetting delta from "+unpatched_file)
with open(unpatched_file, "rb") as f:
	delta = sync.zsync_delta(f, hashes, blocksize=size)
instructions,missing = sync.get_blueprint(delta, num)
print("Blueprint: "+str(instructions))
print("I need the following blocks: "+str(missing))

print("Getting missing blocks from "+result_file)
with open(patched_file, "rb") as f:
	blocks = [b for b in sync.get_blocks(f, missing, size)]
print("Missing blocks: "+str(blocks))

print("Patching "+result_file)
with open(unpatched_file, "rb") as unpatched, \
			open(patched_file, "rb") as patched, \
			open(result_file, "wb") as result:
	sync.easy_patch(unpatched, result, instructions, blocks, size)

if (filecmp.cmp(patched_file, result_file, shallow=False)):
	print("Patched properly")
else:
	print("Not patched properly")

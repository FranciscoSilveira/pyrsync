===============================
#pyzsync
===============================
This is a fork of the `pyrsync2` package with the intention of implementing the zsync algorithm based on its code.

A lot of the work done here, and certainly the hardest one, comes from [Georgy Angelov's](https://github.com/georgyangelov/pyrsync) and [Eric Pruitt's](http://code.activestate.com/recipes/577518-rsync-algorithm/) excellent work on pyrsync. I adapted their work to implement zsync, as described here.

## Usage
Obtain hashlist for patched file:
```
with open(patched_file, "rb") as patched:
	hashes = pyzsync.block_checksums(patched)
```
Find which blocks are missing on the unpatched file:
```
with open(unpatched_file, "rb") as unpatched:
	instructions, request = pyzsync.zsync_delta(unpatched, hashes)
```
Obtain the missing blocks from the patched file:
```
blocks = pyzsync.get_blocks(patched, to_request)
```
Patch the file:
```
instructions = pyzsync.merge_instructions_blocks(instructions, blocks)
pyzsync.patchstream(unpatched, result, instructions)
```

## Theory
### Rsync vs Zsync
Zsync differs from rsync in the delegation of tasks. Let's assume B just modified their file and A needs to modify their version accordingly. Rsync works somewhat like this:

* A sends B a list of hashes for blocks of their unpatched file
* B calculates the difference in relation to their patched file and send back the blocks A is missing
* A patches their file according to their unpatched file and the received blocks

Meanwhile zsync has an extra step:

* B sends A a list of hashes for their **patched** file
* A calculates which blocks it's missing and requests them from B
* B sends those blocks
* A patches their file

So rsync has one hashlist message and one blocklist message, while zsync has two hashlist messages and one blocklist message. 2 is less than 3 and so rsync wins there. But the blocklist message is going to be the largest one in most cases, and by a few orders of magnitude, so adding a hashlist message isn't a huge deal. And rsync requires that the party with a patched file must calculate the missing blocks for each individual party with an unpatched file. Imagine a cloud-storage server with 1000 clients all watching a file waiting for modifications. Zsync on the other hand makes every client calculate their own missing blocks and request them. The calculation itself isn't heavy for a single client, but it becomes a burden to centralize it on a single node.

### Optimizing

You could argue for a rsync optimization where you could just calculate the missing blocks for one unpatched file, and from there onwards check that it's identical for all (for example with timestamps or hashing the hashlist, since we expect all clients to have their unpatched files be equal) for each and send that, but the basic algorithm is still fairly crude. Also, the same sort of optimization is possible with zsync: after the first client requests the missing blocks, simply send the other clients the patched file's hashlist and those missing blocks.

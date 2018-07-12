===============================
#pyzsync
===============================
This is a fork of the `pyrsync2` package with the intention of implementing the [zsync](http://zsync.moria.org.uk/) algorithm based on its code using asynchronous file access.

A lot of the work done here, and certainly the hardest one, comes from [Georgy Angelov's](https://github.com/georgyangelov/pyrsync) and [Eric Pruitt's](http://code.activestate.com/recipes/577518-rsync-algorithm/) excellent work on pyrsync. I adapted their work to implement zsync with asyncio. Also Mark Adler, creator of the [Adler32 checksum algorithm](https://en.wikipedia.org/wiki/Adler-32) who's online documentation was essential.
## Requirements
The only dependencies are `hashlib` for generating the strong hash (MD5) and `aiofiles`, a library that provides non-blocking file I/O using asyncio which you can get from pip:
```
$ pip install aiofiles
```

## Usage
Obtain hashlist for patched file:
```
async with aiofiles.open(patched_file, "rb") as patched:
	num, hashes = await pyzsync.block_checksums(patched)
```
Find which blocks are missing on the unpatched file:
```
async with aiofiles.open(unpatched_file, "rb") as unpatched:
	delta = await pyzsync.zsync_delta(unpatched, hashes)
```
Obtain a blueprint from that delta:
```
instructions,missing = pyzsync.get_blueprint(delta, num)
```
**From here on out there is blocking I/O, I'm working on it**
Obtain the missing blocks from the patched file:
```
with open(patched_file, "rb") as patched:
	blocks = pyzsync.get_blocks(patched, missing)
```
Patch the file:
```
with open(unpatched_file, "rb") as unpatched, open(resulting_file, "wb") as result:
    pyzsync.easy_patch(unpatched, result, instructions, blocks)
```

### Partial patches
The easy_patch function doesn't force you to have the entire block list from the patched file.
The first call should have the full "instructions" list, regardless of whether "blocks" is None, full or partial.
Subsequent calls should have Instructions as None and a full or partial "blocks"
This is useful if you're sending over large files. This way, not only can you start working on a part right away
before the others arrive, you also don't have to keep all the blocks in memory until they all arrive.
Example where blocks is a big list dividided in 2 parts:
```
with open(unpatched_file, "rb") as unpatched, open(resulting_file, "wb") as result:
    pyzsync.easy_patch(unpatched, result, instructions, None, blocksize)
    # Received blocks part 1 from remote
    pyzsync.easy_patch(unpatched, result, None, blocks1, blocksize)
    # Later receive blocks part 2
    pyzsync.easy_patch(unpatched, result, None, blocks2, blocksize)
```

## Testing
The current test suite included `pyzsync_tests.py` hasn't been updated for asyncio, but the `simple_test.py` should work fine.

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

### Blocksize

I did a quick test with several blocksizes, from 8B to 1M.
Anything below 8B didn't work at all, and I didn't bother to find out why because I wouldn't use that anyway.
```
Blocksize 8 : 0:00:04.076282
Blocksize 16 : 0:00:02.119228
Blocksize 32 : 0:00:01.291154
Blocksize 64 : 0:00:00.900765
Blocksize 128 : 0:00:00.736413
Blocksize 256 : 0:00:00.704903
Blocksize 512 : 0:00:00.632211
Blocksize 1024 : 0:00:00.628492
Blocksize 2048 : 0:00:00.622903
Blocksize 4096 : 0:00:00.623649
Blocksize 8192 : 0:00:00.663440
Blocksize 16384 : 0:00:00.675972
Blocksize 32768 : 0:00:00.659214
Blocksize 65536 : 0:00:00.704928
Blocksize 131072 : 0:00:00.625354
Blocksize 262144 : 0:00:00.696357
Blocksize 524288 : 0:00:00.698318
Blocksize 1048576 : 0:00:00.722758
```

===============================
#pyzsync
===============================
This is a fork of the `pyrsync2` package with the intention of implementing the [zsync](http://zsync.moria.org.uk/) algorithm based on its code using asynchronous file access.

A lot of the work done here, and certainly the hardest one, comes from [Georgy Angelov's](https://github.com/georgyangelov/pyrsync) and [Eric Pruitt's](http://code.activestate.com/recipes/577518-rsync-algorithm/) excellent work on pyrsync. I adapted their work to implement zsync with asyncio. Also Mark Adler, creator of the [Adler32 checksum algorithm](https://en.wikipedia.org/wiki/Adler-32) who's online documentation was essential.

## FAQ
**What is the state of the project?**
Both the synchronous and asynchronous behaviour currently work.
I will be working on adapting the test suite. Currently the best guide is tests/simple_test.py

**Why is so much code duplicated?**
This has to do with whether a function is a regular python function or an asyncio coroutine. Inside those almost-equal functions, the I/O differs between regular or a call to a coroutine (`file.read(size)` vs `await file.read(size)`). The only way to call a coroutine is inside another coroutine, so I can't just get away with something like an if/else to choose which one to call - in order to even call the asynchronous I/O, the caller itself has to be a coroutine defined with `async def`, which obviously you wouldn't want for regular I/O. So this way the asnchronous and synchronous versions get separated.

## Requirements
The dependencies are:
* `hashlib` for generating the strong hash (MD5) 
* `zlib` for usage of the adler32 rolling checksum for the weak hash
* (optional for async usage) `aiofiles`, a library that provides non-blocking file I/O using asyncio which you can get from pip:
```
$ pip install aiofiles
```

## Usage

### Synchronous
```
# Generate the hash list for the patched file
with open(patched_file, "rb") as f:
	num, hashes = zsync.block_checksums(f, blocksize=blocksize)

# Get the instructions
with open(unpatched_file, "rb") as f:
	local, remote = zsync.get_instructions(f, hashes, blocksize=blocksize)
missing = list(remote.keys())

# Get the blocks from the local file and write them to the result file
with open(unpatched_file, "rb") as unpatched, \
		open(result_file, "wb") as result:
	zsync.patch_local_blocks(unpatched, result, local, blocksize)

# Get the missing blocks from the patched file
with open(patched_file, "rb") as f:
	blocks = [b for b in zsync.get_blocks(f, missing, blocksize)]

# Patch the result file with the missing blocks
with open(result_file, "r+b") as result: # This opens the result file for updating in binary
	zsync.patch_remote_blocks(blocks, result, remote, check_hashes=True)
```
### Asynchronous
```
# Generate the hash list for the patched file
async with aiofiles.open(patched_file, "rb") as f:
	num,hashes = await zsync.block_checksums(f, blocksize=blocksize)

# Get the instructions
async with aiofiles.open(unpatched_file, "rb") as f:
	local, remote = await zsync.get_instructions(f, hashes, blocksize=blocksize)
missing = list(remote.keys())

# Get the blocks from the local file and write them to the result file
async with aiofiles.open(unpatched_file, "rb") as unpatched, \
		aiofiles.open(result_file, "wb") as result:
	await zsync.patch_local_blocks(unpatched, result, local, blocksize)

# Get the missing blocks from the patched file
async with aiofiles.open(patched_file, "rb") as f:
	blocks = [ b async for b in zsync.get_blocks(f, missing, blocksize) ]

# Patch the result file with the missing blocks
async with aiofiles.open(result_file, "r+b") as result:  # This opens the result file for updating in binary
	await zsync.patch_remote_blocks(blocks, result, remote, check_hashes=True)
```

## Partial patches
The `patch_remote_blocks()` function doesn't force you to have the entire block list from the patched file. You can fill the result file as blocks arrive instead of sending huge bytearrays over a network or keeping them in memory:
```
pivot = int(len(blocks)/2)
b1 = blocks[:pivot]
b2 = blocks[pivot:]
with open(result_file, "r+b") as result: # This opens the result file for updating in binary
    # Received blocks part 1 from remote
	zsync.patch_remote_blocks(blocks1, result, remote, check_hashes=True)
	# Received blocks part 2 from remote
	zsync.patch_remote_blocks(blocks2, result, remote, check_hashes=True)
```

## Testing
The current test suite included `pyzsync_tests.py` hasn't been updated for the latest changes, but the `simple_test.py` should work fine.

## Theory
### Rsync vs Zsync
Zsync differs from rsync in the delegation of tasks. Let's assume B just modified their file and A needs to modify their version accordingly. Rsync works somewhat like this:

* B notifies A that their file has been changed and requests a hashlist from A
* A sends B a list of hashes for blocks of their unpatched file
* B calculates the difference in relation to their patched file and send back the blocks A is missing
* A patches their file according to their unpatched file and the received blocks

Meanwhile zsync has an extra step:

* B notifies A that their file has been changed and **sends** its hashlist A
* A calculates which blocks it's missing and requests them from B
* B sends those blocks to A
* A patches their file

So rsync has one notification, one hashlist message and one blocklist message; while zsync has one hashlist message, one block request and one blocklist message. They send the same number of messages, although ZSync ends up sending slightly more data in one of them. But the blocklist message is going to be the largest one in most cases, and by a few orders of magnitude, so the overhead introduced by that block request is very small.
Also rsync requires that the party with a patched file must calculate the missing blocks for each individual party with an unpatched file. Imagine a cloud-storage server with 1000 clients all watching a file waiting for modifications. Zsync on the other hand makes every client calculate their own missing blocks and request them. The calculation itself isn't heavy for a single client, but it becomes a burden to centralize it on a single node.

### Optimizing

You could argue for a rsync optimization where you could just calculate the missing blocks for one unpatched file, and from there onwards check that it's identical for all (for example with timestamps or hashing the hashlist, since we expect all clients to have their unpatched files be equal) for each and send that, but the basic algorithm is still fairly crude. Also, the same sort of optimization is possible with zsync: after the first client requests the missing blocks, simply send the other clients the patched file's hashlist and those missing blocks.

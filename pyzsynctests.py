import pyzsync
import pyrsync2
import filecmp
import unittest
from datetime import datetime
import os

unpatched_file = "/home/francisco/loremipsum"
patched_file = "/home/francisco/loremipsum_modified"
resulting_file = "/home/francisco/loremipsum_result" # this one gets cleared by the open(...,"wb") call

unpatched_large = "/tmp/unpatched_large"
patched_large = "/home/francisco/1434065645264.jpg"
resulting_large = "/tmp/result_large"

unpatched_very_large = "/tmp/unpatched_very_large"
patched_very_large = "/home/francisco/SEL_03.mp4"
resulting_very_large = "/tmp/result_very_large"

def common_zsync(patched_file, unpatched_file, resulting_file, blocksize):
	with open(unpatched_file, "rb") as unpatched, \
			open(patched_file, "rb") as patched, \
			open(resulting_file, "wb") as result:
		start = datetime.now()
		num, hashes = pyzsync.block_checksums(patched, blocksize=blocksize)
		delta = pyzsync.zsync_delta(unpatched, hashes, blocksize=blocksize)
		instructions,missing = pyzsync.get_blueprint(hashes, num, blocksize=blocksize)
		blocks = pyzsync.get_blocks(patched, missing, blocksize)
		pyzsync.easy_patch(unpatched, result, instructions, blocks, blocksize)
		duration = datetime.now() - start
	return duration

def common_rsync(patched_file, unpatched_file, resulting_file, blocksize):
	with open(unpatched_file, "rb") as unpatched, \
			open(patched_file, "rb") as patched, \
			open(resulting_file, "wb") as result:
		start = datetime.now()
		hashes = pyrsync2.blockchecksums(unpatched, blocksize)
		delta = pyrsync2.rsyncdelta(patched, hashes, blocksize)
		pyrsync2.patchstream(unpatched, result, delta, blocksize)
		duration = datetime.now() - start
	return duration


class PyZsyncTests(unittest.TestCase):
	def setUp(self):
		with open(unpatched_large, "wb"), \
				open(resulting_large, "wb"),\
				open(unpatched_very_large, "wb"),\
				open(resulting_very_large, "wb"):
			pass

	def tearDown(self):
		os.remove(unpatched_large)
		os.remove(resulting_large)
		os.remove(unpatched_very_large)
		os.remove(resulting_very_large)

	def testSimplePatch(self):
		blocksize = 32
		common_zsync(patched_file, unpatched_file, resulting_file, blocksize)
		self.assertTrue(filecmp.cmp(patched_file, resulting_file, shallow=False))

	def testLargePatch(self):
		filesize = os.path.getsize(patched_large)
		blocksize = 4096

		self.assertFalse(filecmp.cmp(patched_large, resulting_large, shallow=False))
		duration_zsync = common_zsync(patched_large, unpatched_large, resulting_large, blocksize)
		self.assertTrue(filecmp.cmp(patched_large, resulting_large, shallow=False))
		self.tearDown()
		self.setUp()

		self.assertFalse(filecmp.cmp(patched_large, resulting_large, shallow=False))
		duration_rsync = common_rsync(patched_large, unpatched_large, resulting_large, blocksize)
		self.assertTrue(filecmp.cmp(patched_large, resulting_large, shallow=False))

		print(str(filesize) + "B: Zsync took " + str(duration_zsync) + " seconds, while Rsync took " + str(
			duration_rsync) + " seconds")

	def testLargePatchSeveralBlocksizes(self):
		blocksizes = [ 2**i for i in range(3,21) ]
		durations = []
		for blocksize in blocksizes:
			duration = common_zsync(patched_large, unpatched_large, resulting_large, blocksize)
			self.assertTrue(filecmp.cmp(patched_large, resulting_large, shallow=False))
			durations.append((blocksize,duration))
		for b,d in durations:
			print("Blocksize "+str(b)+" : "+str(d))

	def testVeryLargePatch(self):
		return
		filesize = os.path.getsize(patched_very_large)
		blocksize = 4096

		self.assertFalse(filecmp.cmp(patched_very_large, resulting_very_large, shallow=False))
		duration_zsync = common_zsync(patched_very_large, unpatched_very_large, resulting_very_large, blocksize)
		self.assertTrue(filecmp.cmp(patched_very_large, resulting_very_large, shallow=False))

		self.setUp()
		self.assertFalse(filecmp.cmp(patched_very_large, resulting_very_large, shallow=False))
		duration_rsync = common_rsync(patched_very_large, unpatched_very_large, resulting_very_large, blocksize)
		self.assertTrue(filecmp.cmp(patched_very_large, resulting_very_large, shallow=False))

		print(str(filesize) + "B: Zsync took " + str(duration_zsync) + " seconds, while Rsync took " + str(
			duration_rsync) + " seconds")


if __name__ == "__main__":
	unittest.main()

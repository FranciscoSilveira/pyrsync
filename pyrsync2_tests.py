import unittest
import hashlib
import math

from io import BytesIO

import pyrsync2


class PyRsyncTests(unittest.TestCase):
    TEST_BLOCK_SIZE = 4
    TEST_FILE = b'one really small file here'

    TEST_FILE_ADDITIONS = b'one really smaller file here :)'
    ADDITIONS_DELTA = [0, 1, 2, 3, b'er', 4, 5, b're', b' :)']

    TEST_FILE_DELETES = b'one really s file here'
    DELETES_DELTA = [0, 1, 2, 4, 5, 6]

    TEST_FILE_REORDERS = b'realone mallly s file here'
    REORDERS_DELTA = [1, 0, 3, 2, 4, 5, 6]

    def get_block(self, data, block):
        return data[
            block * self.TEST_BLOCK_SIZE:(block + 1) * self.TEST_BLOCK_SIZE
        ]

    def get_delta(self, file):
        file_to = BytesIO(self.TEST_FILE)
        file_from = BytesIO(file)

        hashes = pyrsync2.blockchecksums(
            file_to,
            blocksize=self.TEST_BLOCK_SIZE
        )

        delta = pyrsync2.rsyncdelta(
            file_from,
            hashes,
            blocksize=self.TEST_BLOCK_SIZE
        )
        return list(delta)

    def test_blockchecksums(self):
        with BytesIO(self.TEST_FILE) as file1:
            hashes = pyrsync2.blockchecksums(
                file1,
                blocksize=self.TEST_BLOCK_SIZE
            )

            for block, block_hash in enumerate(hashes):
                block_data = self.get_block(self.TEST_FILE, block)

                weaksum = pyrsync2.weakchecksum(block_data)[0]
                strongsum = hashlib.md5(block_data).digest()

                self.assertEqual(block_hash, (weaksum, strongsum))

    def test_rsyncdelta_same_file(self):
        with BytesIO(self.TEST_FILE) as file_to:
            hashes = pyrsync2.blockchecksums(
                file_to,
                blocksize=self.TEST_BLOCK_SIZE
            )

            with BytesIO(self.TEST_FILE) as file_from:
                delta = pyrsync2.rsyncdelta(
                    file_from, hashes,
                    blocksize=self.TEST_BLOCK_SIZE
                )

                for index, block in enumerate(delta):
                    self.assertEqual(index, block)

    def test_rsyncdelta_with_changes(self):
        changes_in_blocks = [
            (0, 0),
            (3, 2),
            (4, 0),
            (5, self.TEST_BLOCK_SIZE - 1),
            (math.ceil(len(self.TEST_FILE) / self.TEST_BLOCK_SIZE) - 1, 0)
        ]
        changed_blocks = [block for block, position in changes_in_blocks]

        with BytesIO(self.TEST_FILE) as changed_file:
            file_buffer = changed_file.getbuffer()

            for block, position in changes_in_blocks:
                file_buffer[block * self.TEST_BLOCK_SIZE + position] += 1

            changed_file_data = changed_file.getvalue()

            with BytesIO(self.TEST_FILE) as file_to:
                hashes = pyrsync2.blockchecksums(
                    file_to,
                    blocksize=self.TEST_BLOCK_SIZE
                )

                delta = pyrsync2.rsyncdelta(
                    changed_file,
                    hashes,
                    blocksize=self.TEST_BLOCK_SIZE,
                    max_buffer=self.TEST_BLOCK_SIZE
                )

                for block, data in enumerate(delta):
                    if block in changed_blocks:
                        self.assertEqual(
                            self.get_block(changed_file_data, block),
                            data
                        )
                    else:
                        self.assertEqual(block, data)

    def test_rsyncdelta_with_additions(self):
        delta = self.get_delta(self.TEST_FILE_ADDITIONS)
        self.assertEqual(delta, self.ADDITIONS_DELTA)

    def test_rsyncdelta_with_deletes(self):
        delta = self.get_delta(self.TEST_FILE_DELETES)
        self.assertEqual(delta, self.DELETES_DELTA)

    def test_rsyncdelta_with_reorders(self):
        delta = self.get_delta(self.TEST_FILE_REORDERS)
        self.assertEqual(delta, self.REORDERS_DELTA)

    def test_patchstream_with_additions(self):
        delta = self.get_delta(self.TEST_FILE_ADDITIONS)

        old_file = BytesIO(self.TEST_FILE)
        out_file = BytesIO()
        pyrsync2.patchstream(
            old_file,
            out_file,
            delta,
            blocksize=self.TEST_BLOCK_SIZE
        )

        self.assertEqual(out_file.getvalue(), self.TEST_FILE_ADDITIONS)

    def test_patchstream_with_deletes(self):
        delta = self.get_delta(self.TEST_FILE_DELETES)

        old_file = BytesIO(self.TEST_FILE)
        out_file = BytesIO()
        pyrsync2.patchstream(
            old_file,
            out_file,
            delta,
            blocksize=self.TEST_BLOCK_SIZE
        )

        self.assertEqual(out_file.getvalue(), self.TEST_FILE_DELETES)

    def test_patchstream_with_reorders(self):
        delta = self.get_delta(self.TEST_FILE_REORDERS)

        old_file = BytesIO(self.TEST_FILE)
        out_file = BytesIO()
        pyrsync2.patchstream(
            old_file,
            out_file,
            delta,
            blocksize=self.TEST_BLOCK_SIZE
        )

        self.assertEqual(out_file.getvalue(), self.TEST_FILE_REORDERS)

if __name__ == '__main__':
    unittest.main()

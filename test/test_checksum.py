#   Copyright (c) 2023, TriForMine. (https://triformine.dev) and samsoucoupe All rights reserved.
#  #
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#  #
#        http://www.apache.org/licenses/LICENSE-2.0
#  #
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

from src.checksum import Checksum
import tempfile
from os import path
import unittest
from zlib import adler32

class ChecksumTest(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()

        self.file = path.join(self.test_dir.name, "test.txt")
        self.file2 = path.join(self.test_dir.name, "test2.txt")
        self.file3 = path.join(self.test_dir.name, "test3.txt")

        with open(self.file, "w") as f:
            f.write("test")

        with open(self.file2, "w") as f:
            f.write("test2")

        with open(self.file3, "w") as f:
            f.write(" test")

    def tearDown(self) -> None:
        self.test_dir.cleanup()

    def test_checksum(self):
        """
        Test if the checksum is correct
        :return:
        """
        checksum = Checksum(self.file, divide=1)
        self.assertEqual(len(checksum.checksums), 1, "Checksums length is not 1.")
        self.assertEqual(checksum.checksums[0], adler32(b"test"), "Checksum is not correct.")

    def test_multiple_checksum(self):
        """
        Test if the checksum is correct
        :return:
        """
        checksum = Checksum(self.file, divide=2)
        self.assertEqual(len(checksum.checksums), 2, "Checksums length is not 2.")
        self.assertEqual(checksum.checksums[0], adler32(b"tes"), "Checksum is not correct.")
        self.assertEqual(checksum.checksums[1], adler32(b"t"), "Checksum is not correct.")

    def test_checksums_part_length(self):
        """
        Test if the part length is correct
        :return:
        """
        checksum = Checksum(self.file, divide=2)
        self.assertEqual(checksum.partLength, 3, "Part length is not 3.")

    def test_checksums_total_length(self):
        """
        Test if the total length is correct
        :return:
        """
        checksum = Checksum(self.file, divide=2)
        self.assertEqual(checksum.totalLength, 4, "Total length is not 4.")

    def test_checksums_from_checksums(self):
        """
        Test if the checksums are correct
        :return:
        """
        checksum = Checksum(self.file, divide=2)
        checksum2 = Checksum(checksums=checksum.checksums, part_length=checksum.partLength, total_length=checksum.totalLength)
        self.assertEqual(checksum.checksums, checksum2.checksums, "Checksums are not equal.")
        self.assertEqual(checksum.partLength, checksum2.partLength, "Part length is not equal.")
        self.assertEqual(checksum.totalLength, checksum2.totalLength, "Total length is not equal.")

    def test_compare_checksums_with_file(self):
        """
        Test if the checksums are correct
        :return:
        """
        checksum = Checksum(self.file, divide=2)
        parts = checksum.compare_with_file(self.file2)

        self.assertGreater(len(parts), 0, "Parts length is not bigger than 0.")

        # The second part is different, it should be asking for 3 bytes from the 6th byte.
        self.assertEqual(parts[0], (3, 6, 0), "The part is not correct.")

    def test_compare_checksums_with_offset(self):
        """
        Test if the checksums are correct
        :return:
        """
        checksum = Checksum(self.file, divide=1)
        parts = checksum.compare_with_file(self.file3)

        self.assertEqual(len(parts), 2, "Parts length is not 2.")

        self.assertEqual(parts[0], (0, 4, 1), "It should first tell to move bytes 0 from 4 by 1 byte.")
        self.assertEqual(parts[1], (0, 1, 0), "It should then ask for bytes 0 to 1.")



if __name__ == '__main__':
    unittest.main()
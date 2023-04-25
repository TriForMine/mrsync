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

import unittest
from src.adler32 import Adler32
from zlib import adler32

class TestAdler32(unittest.TestCase):
    def test_adler32_no_data(self):
        """
        Test if Adler32 calculates checksum correctly with no data
        :return:
        """
        self.assertEqual(Adler32().checksum, adler32(b""), "Adler32 did not calculate checksum correctly.")

    def test_adler32_with_data(self):
        """
        Test if Adler32 calculates checksum correctly with data
        :return:
        """
        data = b"Hello World!"
        self.assertEqual(Adler32(data).checksum, adler32(data), "Adler32 did not calculate checksum correctly.")

    def test_adler32_with_data_and_window(self):
        """
        Test if Adler32 calculates checksum correctly with data and window
        :return:
        """
        data = b"AHello World"
        moved_data = b"Hello World!"
        adler = Adler32(data)
        adler.move_window(b'A', b'!')
        self.assertEqual(adler.checksum, adler32(moved_data), "Adler32 did not move window correctly.")


if __name__ == '__main__':
    unittest.main()

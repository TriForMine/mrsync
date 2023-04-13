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

import zlib

_BASE = 65521  # largest prime smaller than 65536
_NMAX = 5552  # largest n such that 255n(n+1)/2 + (n+1)(BASE-1) <= 2^32-1
_OFFS = 1  # default initial s1 offset


class Adler32:
    def __init__(self, data: bytes = ''):
        """
        Create a new Adler32 checksum.
        :param data:  The data to initialize the checksum with.
        """
        self.s2, self.s1 = 0, _OFFS
        self.count = 0
        if data: self.update(data)

    def update(self, data: bytes):
        """
        Update the checksum with new data.
        :param data: The data to update the checksum with.
        :return: The new checksum.
        """
        value = zlib.adler32(data, self.checksum)
        # Split the checksum into two 16-bit values.
        self.s2, self.s1 = (value >> 16) & 0xffff, value & 0xffff
        # Update the byte count.
        self.count = self.count + len(data)

    def move_window(self, first_byte: bytes, new_byte: bytes):
        """
        Move the checksum window by removing the first byte and adding a new byte.
        :param first_byte: The first byte of the window.
        :param new_byte: The new byte to add to the window.
        :return:
        """
        first_byte = ord(first_byte)
        if new_byte:
            new_byte = ord(new_byte)
            # Update the checksum.
            self.s1 = (self.s1 - first_byte + new_byte) % _BASE
            self.s2 = (self.s2 - self.count * first_byte + self.s1 - _OFFS) % _BASE
        else:
            # Update the checksum.
            self.s1 = (self.s1 - first_byte) % _BASE
            self.s2 = (self.s2 - self.count * first_byte - _OFFS) % _BASE
            self.count -= 1

    @property
    def checksum(self):
        return (self.s2 << 16) | self.s1

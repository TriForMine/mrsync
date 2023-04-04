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

import hashlib

from typing import List, Optional, Tuple


class Checksum:
    parts: int
    checksums: List[str]
    partLength: int
    totalLength: int

    def __init__(self, path: str, divide: int = 2, max_size: Optional[int] = None, total_length: Optional[int] = None,
                 checksums: Optional[List[str]] = None, part_length: Optional[int] = None):
        """
        Create a divide checksum of a file.
        :param path:  The path to the file.
        :param divide:  The number of parts to divide the file into.
        :param max_size:  The maximum size of the file.
        To be able to find the difference between two files, the maximum size of the file must be the same.
        """

        if checksums is not None:
            self.checksums = checksums
            self.parts = len(checksums)
            self.partLength = part_length
            self.totalLength = total_length
            return

        self.parts = divide
        self.path = path
        self.checksums = self.calculate(max_size)

    def calculate(self, max_size: Optional[int] = None) -> List[str]:
        """
        Calculate the checksums.
        """
        checksums = []
        with open(self.path, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            self.totalLength = size
            if max_size is not None and size > max_size:
                size = max_size

            self.partLength = size // self.parts + 1
            f.seek(0)
            for i in range(self.parts):
                checksums.append(hashlib.md5(f.read(self.partLength)).hexdigest())

        return checksums

    def compare_with_file(self, path: str):
        """
        Compare this checksum with a file.
        :param path:  The path to the file.
        :return:  The parts that are different.
        """
        return self.get_difference_bytes(Checksum(path, self.parts, self.totalLength))

    def get_difference_bytes(self, other) -> List[Tuple[int, int]]:
        """
        Get the bytes that are different between this file and another file.
        :param other:
        :return:
        """
        if self.parts != other.parts:
            raise ValueError("The checksums have different parts.")
        parts = []

        my_checksums = self.checksums
        if self.totalLength > other.totalLength:
            my_checksums = self.calculate(other.totalLength)

        for i in range(self.parts):
            if my_checksums[i] != other.checksums[i]:
                parts.append((i * self.partLength, (i + 1) * self.partLength))

        # Add the last part if it is not the same length as the other parts
        if self.totalLength < other.totalLength:
            parts.append((self.totalLength, other.totalLength))
        elif self.totalLength > other.totalLength:
            parts.append((other.totalLength, self.totalLength))

        # Group parts that are next to each other
        return_parts = []
        for part in parts:
            if len(return_parts) == 0:
                return_parts.append(part)
                continue
            if return_parts[-1][1] == part[0]:
                return_parts[-1] = (return_parts[-1][0], part[1])
            else:
                return_parts.append(part)

        return return_parts

    def __hash__(self):
        return hash(self.checksums)

    def __str__(self):
        return f"{self.checksums}"

    def __repr__(self):
        return f"{self.checksums}"

    def __eq__(self, other):
        return self.totalLength == other.totalLength \
            and self.partLength == other.partLength \
            and self.checksums == other.checksums

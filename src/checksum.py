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

from typing import List, Optional, Tuple
from adler32 import Adler32


class Checksum:
    parts: int
    checksums: List[int]
    partLength: int
    totalLength: int

    def __init__(self, path: str, divide: int = 2, max_size: Optional[int] = None, total_length: Optional[int] = None,
                 checksums: Optional[List[int]] = None, part_length: Optional[int] = None):
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

    def calculate(self, max_size: Optional[int] = None) -> List[int]:
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
                checksums.append(Adler32(f.read(self.partLength)).checksum)

        return checksums

    def compare_with_file(self, path: str):
        """
        Compare this checksum with a file.
        :param path:  The path to the file.
        :return:  The parts that are different.
        """
        return self.get_difference_bytes(Checksum(path, self.parts, self.totalLength))

    def get_difference_bytes(self, other: "Checksum") -> List[Tuple[int, int, int]]:
        """
        Get the bytes that are different between this file and another file.
        :param other: Another Checksum object representing the other file to compare to.
        :return:
        """
        if self.parts != other.parts:
            raise ValueError("The checksums have different parts.")
        parts = []

        if self.totalLength > other.totalLength:
            self.calculate(other.totalLength)

        # Compare the checksums
        with open(self.path, "rb") as f1:
            window = 0

            for i in range(self.parts):
                f1.seek(i * self.partLength + window)

                read_data = f1.read(self.partLength)
                current_hash = Adler32(read_data)

                while window < self.partLength:
                    if current_hash.checksum == other.checksums[i]:
                        if window > 0:
                            # Send the part between the start and the offset
                            parts.append((i * self.partLength, i * self.partLength + window, 0))
                            # Send an offset representing the part that is the same
                            parts.append((i * self.partLength, (i + 1) * self.partLength - window, window))
                        break

                    if len(read_data) <= window:
                        parts.append((i * self.partLength, (i + 1) * self.partLength, 0))
                        break

                    first_byte = bytes([read_data[window]])
                    next_byte = f1.read(1)

                    current_hash.move_window(first_byte, next_byte)

                    window += 1

                # All windows have been checked and no match was found.
                # Add the whole part as a difference.
                if window >= self.partLength:
                    parts.append((i * self.partLength, (i + 1) * self.partLength, 0))
                    window = 0

        # Add the last part if it is not the same length as the other parts
        if self.totalLength < other.totalLength:
            if len(parts) == 0 or (parts[-1][1] + parts[-1][2]) != other.totalLength:
                parts.append((self.totalLength, other.totalLength, 0))
        elif self.totalLength > other.totalLength:
            if len(parts) == 0 or (parts[-1][1] + parts[-1][2]) != self.totalLength:
                parts.append((other.totalLength, self.totalLength, 0))

        # Group parts that are next to each other
        return_parts = []
        for part in parts:
            if len(return_parts) == 0:
                return_parts.append(part)
                continue
            if return_parts[-1][1] == part[0] and return_parts[-1][2] == part[2]:
                return_parts[-1] = (return_parts[-1][0], part[1], return_parts[-1][2])
            elif return_parts[-1][1] > part[0] and return_parts[-1][2] == part[2]:
                return_parts[-1] = (return_parts[-1][0], max(return_parts[-1][1], part[1]), return_parts[-1][2])
            else:
                return_parts.append(part)

        # Order the parts by offset since the offset need to be applied first
        return_parts.sort(key=lambda x: -x[2])

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

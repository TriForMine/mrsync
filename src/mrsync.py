#   Copyright (c) 2023, TriForMine. (https://triformine.dev) All rights reserved.
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

import os

from checksum import Checksum

if __name__ == '__main__':
    print("Current directory:", os.getcwd())

    path1 = input("Enter the path of the first file: ")
    path2 = input("Enter the path of the second file: ")

    firstChecksum = Checksum(path1, 10)
    secondChecksum = Checksum(path2, 10)

    print("The first file has been divided into", firstChecksum.parts, "parts.")
    print("The second file has been divided into", secondChecksum.parts, "parts.")

    if firstChecksum == secondChecksum:
        print("The files are the same.")
    else:
        print("The files are different.")
        print("The bytes that are different are:", firstChecksum.compare_with_file(path2))

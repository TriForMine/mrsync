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
import subprocess
import os
import tempfile


class TestCompareWithRealRsync(unittest.TestCase):
    def setUp(self) -> None:
        # Change to the root directory of the project
        os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        # Create a test source directory
        self.test_src_dir = tempfile.TemporaryDirectory()

        # Create a test destination directory for mrsync
        self.test_dst_dir = tempfile.TemporaryDirectory()

        # Create a test destination directory for the real rsync
        self.test_dst_dir_2 = tempfile.TemporaryDirectory()

        # Create a unit_tests file
        self.test_file = os.path.join(self.test_src_dir.name, "test.txt")

        # Write to the unit_tests file
        with open(self.test_file, "w") as f:
            f.write("test")

        # Create a subdirectory
        os.mkdir(os.path.join(self.test_src_dir.name, "subdir"))

        # Create a file in the subdirectory
        open(os.path.join(self.test_src_dir.name, "subdir", "test3.txt"), "w").close()

        # Create an extra file in the destination directory
        open(os.path.join(self.test_dst_dir.name, "test2.txt"), "w").close()
        open(os.path.join(self.test_dst_dir_2.name, "test2.txt"), "w").close()

    def tearDown(self) -> None:
        self.test_src_dir.cleanup()
        self.test_dst_dir.cleanup()
        self.test_dst_dir_2.cleanup()

    def test_compare_with_real_rsync(self):
        # Run mrsync
        subprocess.run(["python3", "mrsync.py", "-r", self.test_src_dir.name, self.test_dst_dir.name])

        # Run the real rsync
        subprocess.run(["rsync", "-r", self.test_src_dir.name, self.test_dst_dir_2.name])

        # Compare the two directories
        result = subprocess.run(["diff", "-r", self.test_dst_dir.name, self.test_dst_dir_2.name])

        # Check if the two directories are the same
        self.assertEqual(result.returncode, 0)

    def test_compare_with_real_rsync_with_archive(self):
        # Run mrsync
        subprocess.run(["python3", "mrsync.py", "-r", "--archive", self.test_src_dir.name, self.test_dst_dir.name])

        # Run the real rsync
        subprocess.run(["rsync", "-r", "--archive", self.test_src_dir.name, self.test_dst_dir_2.name])

        # Compare the two directories
        result = subprocess.run(["diff", "-r", self.test_dst_dir.name, self.test_dst_dir_2.name])

        # Check if the two directories are the same
        self.assertEqual(result.returncode, 0)

    def test_compare_with_real_rsync_with_compress(self):
        # Run mrsync
        subprocess.run(["python3", "mrsync.py", "-r", "--compress", self.test_src_dir.name, self.test_dst_dir.name])

        # Run the real rsync
        subprocess.run(["rsync", "-r", "--compress", self.test_src_dir.name, self.test_dst_dir_2.name])

        # Compare the two directories
        result = subprocess.run(["diff", "-r", self.test_dst_dir.name, self.test_dst_dir_2.name])

        # Check if the two directories are the same
        self.assertEqual(result.returncode, 0)

    def test_compare_with_real_rsync_with_checksum(self):
        # Run mrsync
        subprocess.run(["python3", "mrsync.py", "-r", "--checksum", self.test_src_dir.name, self.test_dst_dir.name])

        # Run the real rsync
        subprocess.run(["rsync", "-r", "--checksum", self.test_src_dir.name, self.test_dst_dir_2.name])

        # Compare the two directories
        result = subprocess.run(["diff", "-r", self.test_dst_dir.name, self.test_dst_dir_2.name])

        # Check if the two directories are the same
        self.assertEqual(result.returncode, 0)

    def test_compare_with_real_rsync_with_dirs(self):
        # Run mrsync
        subprocess.run(["python3", "mrsync.py", "-r", "--dirs", self.test_src_dir.name, self.test_dst_dir.name])

        # Run the real rsync
        subprocess.run(["rsync", "-r", "--dirs", self.test_src_dir.name, self.test_dst_dir_2.name])

        # Compare the two directories
        result = subprocess.run(["diff", "-r", self.test_dst_dir.name, self.test_dst_dir_2.name])

        # Check if the two directories are the same
        self.assertEqual(result.returncode, 0)

    def test_compare_with_real_rsync_with_hard_links(self):
        # Run mrsync
        subprocess.run(["python3", "mrsync.py", "-r", "--hard-links", self.test_src_dir.name, self.test_dst_dir.name])

        # Run the real rsync
        subprocess.run(["rsync", "-r", "--hard-links", self.test_src_dir.name, self.test_dst_dir_2.name])

        # Compare the two directories
        result = subprocess.run(["diff", "-r", self.test_dst_dir.name, self.test_dst_dir_2.name])

        # Check if the two directories are the same
        self.assertEqual(result.returncode, 0)

    def test_compare_with_real_rsync_with_perms(self):
        # Run mrsync
        subprocess.run(["python3", "mrsync.py", "-r", "--perms", self.test_src_dir.name, self.test_dst_dir.name])

        # Run the real rsync
        subprocess.run(["rsync", "-r", "--perms", self.test_src_dir.name, self.test_dst_dir_2.name])

        # Compare the two directories
        result = subprocess.run(["diff", "-r", self.test_dst_dir.name, self.test_dst_dir_2.name])

        # Check if the two directories are the same
        self.assertEqual(result.returncode, 0)

    def test_compare_with_real_rsync_with_existing(self):
        # Run mrsync
        subprocess.run(["python3", "mrsync.py", "-r", "--existing", self.test_src_dir.name, self.test_dst_dir.name])

        # Run the real rsync
        subprocess.run(["rsync", "-r", "--existing", self.test_src_dir.name, self.test_dst_dir_2.name])

        # Compare the two directories
        result = subprocess.run(["diff", "-r", self.test_dst_dir.name, self.test_dst_dir_2.name])

        # Check if the two directories are the same
        self.assertEqual(result.returncode, 0)

    def test_compare_with_real_rsync_with_ignore_existing(self):
        # Run mrsync
        subprocess.run(["python3", "mrsync.py", "-r", "--ignore-existing", self.test_src_dir.name, self.test_dst_dir.name])

        # Run the real rsync
        subprocess.run(["rsync", "-r", "--ignore-existing", self.test_src_dir.name, self.test_dst_dir_2.name])

        # Compare the two directories
        result = subprocess.run(["diff", "-r", self.test_dst_dir_2.name, self.test_dst_dir.name])

        # Check if the two directories are the same
        self.assertEqual(result.returncode, 0)

    def test_compare_with_real_rsync_with_size_only(self):
        # Run mrsync
        subprocess.run(["python3", "mrsync.py", "-r", "--size-only", self.test_src_dir.name, self.test_dst_dir.name])

        # Run the real rsync
        subprocess.run(["rsync", "-r", "--size-only", self.test_src_dir.name, self.test_dst_dir_2.name])

        # Compare the two directories
        result = subprocess.run(["diff", "-r", self.test_dst_dir_2.name, self.test_dst_dir.name])

        # Check if the two directories are the same
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
        unittest.main()

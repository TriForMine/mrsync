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


class TestMrSync(unittest.TestCase):
    def setUp(self) -> None:
        # Change to the root directory of the project
        os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        # Create a test source directory
        self.test_src_dir = tempfile.TemporaryDirectory()

        # Create a test destination directory
        self.test_dst_dir = tempfile.TemporaryDirectory()

        # Create a unit_tests file
        self.test_file = os.path.join(self.test_src_dir.name, "unit_tests.txt")

        # Write to the unit_tests file
        with open(self.test_file, "w") as f:
            f.write("unit_tests")

    def tearDown(self) -> None:
        self.test_src_dir.cleanup()
        self.test_dst_dir.cleanup()

    def test_list_only(self):
        """
        Test the --list-only option
        :return:
        """
        result = subprocess.run(
            ["python3", "mrsync.py", "--list-only", self.test_src_dir.name],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(result.returncode, 0, "Return code is not 0")
        self.assertIn(
            os.path.basename(self.test_src_dir.name),
            result.stdout.decode(),
            "Directory is not in the list",
        )

    def test_list_only_with_file(self):
        """
        Test the --list-only option with a file
        :return:
        """
        result = subprocess.run(
            ["python3", "mrsync.py", "--list-only", self.test_file],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(result.returncode, 0, "Return code is not 0")
        self.assertIn(
            os.path.basename(self.test_file),
            result.stdout.decode(),
            "File is not in the list",
        )

    def test_list_only_with_recursive(self):
        """
        Test the --list-only option with the --recursive option
        :return:
        """
        result = subprocess.run(
            [
                "python3",
                "mrsync.py",
                "--list-only",
                "--recursive",
                self.test_src_dir.name,
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(result.returncode, 0, "Return code is not 0")
        self.assertIn(
            os.path.basename(self.test_src_dir.name),
            result.stdout.decode(),
            "Directory is not in the list",
        )
        self.assertIn(
            os.path.basename(self.test_file),
            result.stdout.decode(),
            "File is not in the list",
        )

    def test_list_only_with_recursive_and_file(self):
        """
        Test the --list-only option with the --recursive option and a file
        :return:
        """
        result = subprocess.run(
            [
                "python3",
                "mrsync.py",
                "--list-only",
                self.test_file,
                self.test_src_dir.name,
                self.test_dst_dir.name,
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(result.returncode, 0, "Return code is not 0")
        self.assertIn(
            os.path.basename(self.test_file),
            result.stdout.decode(),
            "File is not in the list",
        )
        self.assertIn(
            os.path.basename(self.test_src_dir.name),
            result.stdout.decode(),
            "Directory is not in the list",
        )

    def test_sync(self):
        """
        Test the sync
        :return:
        """
        result = subprocess.run(
            [
                "python3",
                "mrsync.py",
                "-q",
                "-r",
                self.test_src_dir.name + "/",
                self.test_dst_dir.name,
            ],
            check=True,
        )
        self.assertEqual(result.returncode, 0)

        # Check if the file exists in the destination directory
        self.assertTrue(
            os.path.exists(
                os.path.join(self.test_dst_dir.name, os.path.basename(self.test_file))
            ),
            "File does not exist in the destination directory",
        )

        # Check if the file is the same
        with open(
            os.path.join(self.test_dst_dir.name, os.path.basename(self.test_file)), "r"
        ) as f:
            self.assertEqual(f.read(), "unit_tests", "File is not the same")

    def test_sync_with_compress(self):
        """
        Test the sync with compression
        :return:
        """
        result = subprocess.run(
            [
                "python3",
                "mrsync.py",
                "-q",
                "-r",
                "-z",
                self.test_src_dir.name + "/",
                self.test_dst_dir.name,
            ],
            check=True,
        )
        self.assertEqual(result.returncode, 0)

        # Check if the file exists in the destination directory
        self.assertTrue(
            os.path.exists(
                os.path.join(self.test_dst_dir.name, os.path.basename(self.test_file))
            ),
            "File does not exist in the destination directory",
        )

        # Check if the file is the same
        with open(
            os.path.join(self.test_dst_dir.name, os.path.basename(self.test_file)), "r"
        ) as f:
            self.assertEqual(f.read(), "unit_tests", "File is not the same")

    def test_sync_with_permissions(self):
        """
        Test the sync with permissions
        :return:
        """
        result = subprocess.run(
            [
                "python3",
                "mrsync.py",
                "-q",
                "-r",
                "-p",
                self.test_src_dir.name + "/",
                self.test_dst_dir.name,
            ],
            check=True,
        )
        self.assertEqual(result.returncode, 0)

        # Check if the file exists in the destination directory
        self.assertTrue(
            os.path.exists(
                os.path.join(self.test_dst_dir.name, os.path.basename(self.test_file))
            ),
            "File does not exist in the destination directory",
        )

        # Check if the permissions are the same
        self.assertEqual(
            os.stat(
                os.path.join(self.test_dst_dir.name, os.path.basename(self.test_file))
            ).st_mode,
            os.stat(self.test_file).st_mode,
            "Permissions are not the same",
        )

    def test_sync_with_times(self):
        """
        Test the sync with times
        :return:
        """
        result = subprocess.run(
            [
                "python3",
                "mrsync.py",
                "-q",
                "-r",
                "-t",
                self.test_src_dir.name + "/",
                self.test_dst_dir.name,
            ],
            check=True,
        )
        self.assertEqual(result.returncode, 0)

        # Check if the file exists in the destination directory
        self.assertTrue(
            os.path.exists(
                os.path.join(self.test_dst_dir.name, os.path.basename(self.test_file))
            ),
            "File does not exist in the destination directory",
        )

        # Check if the times are the same
        self.assertEqual(
            int(
                os.stat(
                    os.path.join(
                        self.test_dst_dir.name, os.path.basename(self.test_file)
                    )
                ).st_mtime
            ),
            int(os.stat(self.test_file).st_mtime),
            "Times are not the same",
        )

    def test_sync_file_to_file(self):
        """
        Test the sync with a file as the destination
        :return:
        """
        result = subprocess.run(
            [
                "python3",
                "mrsync.py",
                "-q",
                "-r",
                self.test_file,
                os.path.join(self.test_dst_dir.name, os.path.basename(self.test_file)),
            ],
            check=True,
        )
        self.assertEqual(result.returncode, 0)

        # Check if the file exists in the destination directory
        self.assertTrue(
            os.path.exists(self.test_file),
            "File does not exist in the destination directory",
        )

        # Check if the file is the same
        with open(self.test_file, "r") as f:
            self.assertEqual(f.read(), "unit_tests", "File is not the same")

    def test_sync_update(self):
        """
        Test the sync with an updated file
        :return:
        """
        # Create a unit_tests file in the destination directory
        with open(
            os.path.join(self.test_dst_dir.name, os.path.basename(self.test_file)), "w"
        ) as f:
            f.write("test2")

        result = subprocess.run(
            [
                "python3",
                "mrsync.py",
                "-q",
                "-r",
                self.test_src_dir.name + "/",
                self.test_dst_dir.name,
            ],
            check=True,
        )
        self.assertEqual(result.returncode, 0)

        # Check if the file exists in the destination directory
        self.assertTrue(
            os.path.exists(
                os.path.join(self.test_dst_dir.name, os.path.basename(self.test_file))
            ),
            "File does not exist in the destination directory",
        )

        # Check if the file is the same
        with open(
            os.path.join(self.test_dst_dir.name, os.path.basename(self.test_file)), "r"
        ) as f:
            self.assertEqual(f.read(), "unit_tests", "File is not the same")

    def test_sync_update_with_delete(self):
        """
        Test the sync with an updated file and the --delete option
        :return:
        """
        self.test_file2 = os.path.join(self.test_src_dir.name, "test2.txt")

        # Create a unit_tests file in the destination directory
        with open(
            os.path.join(self.test_dst_dir.name, os.path.basename(self.test_file2)), "w"
        ) as f:
            f.write("test2")

        result = subprocess.run(
            [
                "python3",
                "mrsync.py",
                "-q",
                "-r",
                "--delete",
                self.test_src_dir.name + "/",
                self.test_dst_dir.name,
            ],
            check=True,
        )
        self.assertEqual(result.returncode, 0)

        # Check if the file exists in the destination directory
        self.assertFalse(
            os.path.exists(
                os.path.join(self.test_dst_dir.name, os.path.basename(self.test_file2))
            ),
            "File exists in the destination directory",
        )

    def test_quiet(self):
        """
        Test the --quiet option
        :return:
        """
        result = subprocess.run(
            [
                "python3",
                "mrsync.py",
                "-q",
                "-r",
                self.test_src_dir.name + "/",
                self.test_dst_dir.name,
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.decode(), "")
        self.assertEqual(result.stderr.decode(), "")


if __name__ == "__main__":
    unittest.main()

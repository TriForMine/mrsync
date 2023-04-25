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
import os

from src.message import send, MESSAGE_TAG, recv, FileDescriptorMethod
import unittest

class TestMessage(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pipes = os.pipe()

    def test_simple_message(self):
        """
        Test if a simple message is correctly sent and received
        :return:
        """
        send(FileDescriptorMethod(self.pipes[1]), MESSAGE_TAG.END, "unit_tests")
        self.assertEqual(recv(FileDescriptorMethod(self.pipes[0])), (MESSAGE_TAG.END, "unit_tests"))

    def test_multiple_message(self):
        """
        Test if multiple messages are correctly sent and received
        :return:
        """
        send(FileDescriptorMethod(self.pipes[1]), MESSAGE_TAG.END, "unit_tests")
        send(FileDescriptorMethod(self.pipes[1]), MESSAGE_TAG.END, "test2")
        self.assertEqual(recv(FileDescriptorMethod(self.pipes[0])), (MESSAGE_TAG.END, "unit_tests"))
        self.assertEqual(recv(FileDescriptorMethod(self.pipes[0])), (MESSAGE_TAG.END, "test2"))

    def test_big_message(self):
        """
        Test if a big message is correctly sent and received
        :return:
        """
        send(FileDescriptorMethod(self.pipes[1]), MESSAGE_TAG.END, "unit_tests" * 1000)
        self.assertEqual(recv(FileDescriptorMethod(self.pipes[0])), (MESSAGE_TAG.END, "unit_tests" * 1000))

    def test_file_data(self):
        """
        Test if the file data is correctly sent and received
        :return:
        """
        data = ("unit_tests" * 1000).encode()
        send(FileDescriptorMethod(self.pipes[1]), MESSAGE_TAG.FILE_DATA, ('unit_tests.txt', {"mtime": 0}, 0, 0, True, data))
        self.assertEqual(recv(FileDescriptorMethod(self.pipes[0])), (MESSAGE_TAG.FILE_DATA, ('unit_tests.txt', {"mtime": 0}, 0, 0, True, data)))

    def test_file_data_with_compress(self):
        """
        Test if the file data is correctly sent and received with compress
        :return:
        """
        data = ("unit_tests" * 1000).encode()
        send(FileDescriptorMethod(self.pipes[1]), MESSAGE_TAG.FILE_DATA, ('unit_tests.txt', {"mtime": 0}, 0, 0, True, data), compress_file=True, compress_level=9)
        self.assertEqual(recv(FileDescriptorMethod(self.pipes[0]), compress_file=True), (MESSAGE_TAG.FILE_DATA, ('unit_tests.txt', {"mtime": 0}, 0, 0, True, data)))

    def test_timeout(self):
        """
        Test if the timeout is triggered when no message is sent
        :return:
        """
        with self.assertRaises((SystemExit, TimeoutError), msg="The timeout is not triggered when no message is sent") as cm:
            recv(FileDescriptorMethod(self.pipes[0]), timeout=1)

        self.assertEqual(cm.exception.code, 30, msg="The exit code is not 30")

    def test_timeout2(self):
        """
        Test if the timeout is not triggered when a message is sent
        :return:
        """
        send(FileDescriptorMethod(self.pipes[1]), MESSAGE_TAG.END, "unit_tests")
        self.assertEqual(recv(FileDescriptorMethod(self.pipes[0]), timeout=1), (MESSAGE_TAG.END, "unit_tests"))

if __name__ == "__main__":
    unittest.main()

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
import shutil
import sys
import time
from argparse import Namespace
from os import path

from filelist import generate_file_list, FileListInfo
from generator import Generator
from logger import Logger
from message import recv, send, MESSAGE_TAG


class Server:
    def __init__(self, source: str, destination: str, rd: int, wr: int, logger: Logger, args: Namespace):
        self.logger = logger
        self.source = source
        self.destination = destination
        self.wr = wr
        self.rd = rd
        self.args = args

    def run(self):
        self.logger.info('Server started')
        t1 = time.time()
        self.loop()
        t2 = time.time()
        self.logger.info('Server stopped')
        self.logger.info(f"Time elapsed: {t2 - t1:.2f}s")
        sys.exit(0)

    def handle_file_creation(self, file: str, data: bytes):
        """
        Handle file creation
        :param file: The file name
        :param data:  The file data
        :return: None
        """

        if self.args.existing:
            return

        if file.endswith("/"):
            self.logger.info(f"Creating directory {file}...")
            os.makedirs(path.join(self.destination, file), exist_ok=True)
        else:
            if not path.exists(path.dirname(path.join(self.destination, file))):
                os.makedirs(path.dirname(path.join(self.destination, file)), exist_ok=True)

            self.logger.info(f"Creating file {file}...")
            target_path = path.join(self.destination, file) if file != '' else path.join(self.destination,
                                                                                         path.basename(self.source[0]))
            with open(target_path, "wb") as f:
                f.write(data)

    def handle_file_modification(self, file_name: str, start_byte: int, end_byte: int, whole_file: bool,
                                 modification_time: float, data: bytes):
        if self.args.ignore_existing:
            return

        if not path.exists(path.dirname(path.join(self.destination, file_name))):
            os.makedirs(path.dirname(path.join(self.destination, file_name)), exist_ok=True)

        self.logger.info(f"Modifying file {file_name} from byte {start_byte} to {start_byte + len(data)}...")
        target_path = path.join(self.destination, file_name) if file_name != '' else path.join(self.destination,
                                                                                               path.basename(
                                                                                                   self.source[0]))
        # verify if not a directory
        if not path.isdir(target_path):
            with open(target_path, "r+b") as f:
                f.seek(start_byte)
                f.write(data)

                # If data is smaller than end_byte - start_byte, we need to truncate the file
                if len(data) < end_byte - start_byte:
                    f.truncate()

                if whole_file:
                    f.truncate()

            atime = os.path.getatime(target_path)
            os.utime(target_path, (atime, modification_time))
        else:
            self.logger.warn(f"Cannot modify directory {file_name}")

    def handle_file_deletion(self, files: list):
        """

        :param files:
        :return:
        """
        if files is None:
            return

        for file in files:
            self.logger.info(f"Deleting {file}...")
            print(self.destination, file)
            if path.isdir(path.join(self.destination, file)):
                try:
                    os.rmdir(path.join(self.destination, file))
                except OSError:
                    # If the directory is not empty, we delete all files in it
                    if self.args.force:
                        shutil.rmtree(path.join(self.destination, file))
            else:
                try:
                    os.remove(path.join(self.destination, file))
                except OSError:
                    self.logger.warn(f"Cannot delete {file}")

    def handle_file_offset(self, file_name: str, start_byte: int, end_byte: int, offset: int):
        """
        Move all the content from start_byte to end_byte by offset.
        :param file_name:
        :param start_byte:
        :param end_byte:
        :param offset:
        :return:
        """
        if self.args.ignore_existing:
            return

        if not path.exists(path.dirname(path.join(self.destination, file_name))):
            os.makedirs(path.dirname(path.join(self.destination, file_name)), exist_ok=True)

        self.logger.info(f"Moving file {file_name} from byte {start_byte} to {end_byte}...")
        target_path = path.join(self.destination, file_name) if file_name != '' else path.join(self.destination,
                                                                                               path.basename(
                                                                                                   self.source[0]))
        # verify if not a directory
        if not path.isdir(target_path):
            with open(target_path, "r+b") as f:
                f.seek(start_byte)
                data = f.read(end_byte - start_byte + 1)
                f.seek(start_byte + offset)
                f.write(data)

                # Replace the offset with empty bytes
                f.seek(start_byte)
                f.write(b'\x00' * offset)

                # If data is smaller than end_byte - start_byte, we need to truncate the file
                if len(data) < end_byte - start_byte:
                    f.truncate()
        else:
            self.logger.warn(f"Cannot modify directory {file_name}")

    def loop(self):
        file_list_flags = 0

        if self.args.hard_links:
            file_list_flags |= FileListInfo.HARD_LINKS.value
        if self.args.perms:
            file_list_flags |= FileListInfo.PERMISSIONS.value
        if self.args.times:
            file_list_flags |= FileListInfo.FILE_TIMES.value
        if self.args.size_only:
            file_list_flags |= FileListInfo.FILE_SIZE.value
        if self.args.checksum:
            file_list_flags |= FileListInfo.CHECKSUM.value

        if not self.args.checksum:
            file_list_flags |= FileListInfo.FILE_SIZE.value
            file_list_flags |= FileListInfo.FILE_TIMES.value

        send(self.wr, MESSAGE_TAG.ASK_FILE_LIST, file_list_flags, timeout=self.args.timeout, logger=self.logger)
        while True:
            tag, v = recv(self.rd, timeout=self.args.timeout)

            if tag == MESSAGE_TAG.ASK_FILE_LIST:
                destination_files = generate_file_list([self.destination], self.logger, recursive=self.args.recursive,
                                                       directory=True, options=file_list_flags)
                send(self.wr, MESSAGE_TAG.FILE_LIST, destination_files, timeout=self.args.timeout,
                     logger=self.logger)
            elif tag == MESSAGE_TAG.FILE_LIST:
                self.logger.info(f'File list received {v}')

                source_files = v

                pid = os.fork()

                if pid == 0:
                    os.close(self.rd)
                    destination_files = generate_file_list([self.destination], self.logger,
                                                           recursive=self.args.recursive,
                                                           directory=True, options=file_list_flags)
                    generator = Generator(self.wr, self.source, self.destination, source_files, destination_files,
                                          self.logger, self.args)
                    generator.run()
                    sys.exit(0)
            elif tag == MESSAGE_TAG.FILE_DATA:
                (file_name, start, end, whole_file, modification_time, data) = v
                if not os.path.exists(path.join(self.destination, file_name)):
                    self.handle_file_creation(file_name, data)
                else:
                    self.handle_file_modification(file_name, start, end, whole_file, modification_time, data)
            elif tag == MESSAGE_TAG.FILE_DATA_OFFSET:
                (file_name, start, end, offset) = v
                self.handle_file_offset(file_name, start, end, offset)
            elif tag == MESSAGE_TAG.DELETE_FILES:
                self.handle_file_deletion(v)
            elif tag == MESSAGE_TAG.END:
                self.logger.info('Server: End of transmission')
                send(self.wr, MESSAGE_TAG.SERVER_FINISHED, None, timeout=self.args.timeout, logger=self.logger)
                break

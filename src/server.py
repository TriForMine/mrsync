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

from src.filelist import (
    generate_file_list,
    FileListInfo,
    generate_file_list_flags_from_args,
)
from src.generator import Generator
from src.logger import Logger
from src.message import recv, send, MESSAGE_TAG, MessageMethod


class Server:
    def __init__(
        self,
        source: str,
        destination: str,
        rd: MessageMethod,
        wr: MessageMethod,
        logger: Logger,
        args: Namespace,
    ):
        """
        Server constructor
        :param source: The source directory
        :param destination: The destination directory
        :param rd: The read file descriptor
        :param wr: The write file descriptor
        :param logger: The logger
        :param args: The arguments
        """
        self.logger = logger
        self.source = source

        # Add trailing slash if destination is a directory
        if not destination.endswith("/") and os.path.isdir(destination):
            destination += "/"

        self.destination = destination
        self.wr = wr
        self.rd = rd
        self.args = args

    def run(self):
        self.logger.info("Server started")
        t1 = time.time()
        self.loop()
        t2 = time.time()
        self.logger.info("Server stopped")
        self.logger.info(f"Time elapsed: {t2 - t1:.2f}s")
        sys.exit(0)

    def handle_file_creation(self, path: str, data: bytes, file_info: dict):
        """
        Handle file creation
        :param file_info: The file info
        :param path: The file path
        :param data:  The file data
        :return: None
        """

        if self.args.existing:
            return

        # Create directory if path ends with a slash
        if path.endswith("/"):
            if os.path.exists(path) and not os.path.isdir(path):
                os.remove(path)

            self.logger.info(f"Creating directory {path}...")
            os.makedirs(path, exist_ok=True)
        else:
            # Create parent directory if it doesn't exist
            if not os.path.exists(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path), exist_ok=True)

            if os.path.exists(path) and os.path.isdir(path):
                try:
                    # If the directory is empty, we delete it
                    os.rmdir(path)
                except OSError:
                    # If the directory is not empty and --force is set, we delete it recursively
                    if self.args.force:
                        shutil.rmtree(path)

                    self.logger.error(
                        f"Could not create file {path}: a directory with the same name already exists and is not empty. Use --force to delete it."
                    )
                    return

            self.logger.info(f"Creating file {path}...")
            with open(path, "wb") as f:
                f.write(data)

            if self.args.hard_links and len(file_info["hard_links"]) > 0:
                for link in file_info["hard_links"]:
                    self.logger.info(f"Creating hard link {link}...")
                    link = os.path.join(os.path.dirname(path), link)
                    if os.path.exists(link):
                        os.remove(link)
                    os.link(path, link)

            if self.args.perms:
                os.chmod(path, file_info["permissions"])

            if self.args.times:
                # Set the access and modification time
                os.utime(path, (file_info["atime"], file_info["mtime"]))
            else:
                # Set the modification time
                atime = os.path.getatime(path)
                os.utime(path, (atime, file_info["mtime"]))

    def handle_file_modification(
        self,
        path: str,
        start_byte: int,
        end_byte: int,
        whole_file: bool,
        file_info: dict,
        data: bytes,
    ):
        """
        Handle file modification
        :param path: The file path
        :param start_byte: The start byte
        :param end_byte: The end byte
        :param whole_file: If the file is modified entirely
        :param modification_time: The modification time
        :param data: The data
        :return:
        """
        if self.args.ignore_existing:
            return

        # Create parent directory if it doesn't exist
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path), exist_ok=True)

        self.logger.info(
            f"Modifying file {path} from byte {start_byte} to {start_byte + len(data)}..."
        )

        # If path is a folder, we delete it and create a file with the same name
        if os.path.isdir(path):
            try:
                # If the directory is empty, we delete it
                os.rmdir(path)
            except OSError:
                # If the directory is not empty and --force is set, we delete it recursively
                if self.args.force:
                    self.logger.warn(f"Deleting directory {path} recursively...")
                    shutil.rmtree(path)
                else:
                    self.logger.error(
                        f"Could not modify file {path}: a directory with the same name already exists and is not empty. Use --force to delete it."
                    )
                    return

            self.handle_file_creation(path, data, file_info)
            return

        with open(path, "r+b") as f:
            f.seek(start_byte)
            f.write(data)

            # If data is smaller than end_byte - start_byte, we need to truncate the file
            if len(data) < end_byte - start_byte:
                f.truncate()

            # If the whole file is modified, we truncate it to the new size
            if whole_file:
                f.truncate()

        if self.args.hard_links and len(file_info["hard_links"]) > 0:
            for link in file_info["hard_links"]:
                self.logger.info(f"Creating hard link {link}...")
                link = os.path.join(os.path.dirname(path), link)
                if os.path.exists(link):
                    os.remove(link)
                os.link(path, link)

        if self.args.perms:
            os.chmod(path, int(file_info["permissions"]))

        if self.args.times:
            # Set the access and modification time
            os.utime(path, (file_info["atime"], file_info["mtime"]))
        else:
            # Set the modification time
            atime = os.path.getatime(path)
            os.utime(path, (atime, file_info["mtime"]))

    def handle_file_deletion(self, files: list):
        """
        Handle file deletion
        :param files: The files to delete
        :return:
        """
        if files is None:
            return

        for file in files:
            self.logger.info(f"Deleting {file}...")

            # If the file is a directory, we delete it
            if os.path.isdir(os.path.join(self.destination, file)):
                shutil.rmtree(os.path.join(self.destination, file))
            else:
                try:
                    # If the file is not a directory, we delete it
                    os.remove(os.path.join(self.destination, file))
                except OSError:
                    self.logger.warn(f"Cannot delete {file}")

    def handle_file_offset(
        self, file_name: str, start_byte: int, end_byte: int, offset: int
    ):
        """
        Move all the content from start_byte to end_byte by offset.
        :param file_name: The file name
        :param start_byte: The start byte
        :param end_byte: The end byte
        :param offset: The offset
        :return:
        """
        if self.args.ignore_existing:
            return

        # Create parent directory if it doesn't exist
        if not os.path.exists(
            os.path.dirname(os.path.join(self.destination, file_name))
        ):
            os.makedirs(
                os.path.dirname(os.path.join(self.destination, file_name)),
                exist_ok=True,
            )

        self.logger.info(
            f"Moving file {file_name} from byte {start_byte} to {end_byte}..."
        )
        target_path = (
            os.path.join(self.destination, file_name)
            if file_name != ""
            else os.path.join(self.destination, os.path.basename(self.source[0]))
        )
        # verify if not a directory
        if not os.path.isdir(target_path):
            with open(target_path, "r+b") as f:
                f.seek(start_byte)
                data = f.read(end_byte - start_byte + 1)
                f.seek(start_byte + offset)
                f.write(data)

                # Replace the offset with empty bytes, this is needed to avoid having the same data twice
                # The date will be overwritten by the next modification
                f.seek(start_byte)
                f.write(b"\x00" * offset)

                # If data is smaller than end_byte - start_byte, we need to truncate the file
                if len(data) < end_byte - start_byte:
                    f.truncate()
        else:
            self.logger.warn(f"Cannot modify directory {file_name}")

    def loop(self):
        """
        The src loop of the server
        :return:
        """

        send(
            self.wr,
            MESSAGE_TAG.ASK_FILE_LIST,
            generate_file_list_flags_from_args(self.args),
            timeout=self.args.timeout,
            logger=self.logger,
        )

        if self.args.destination.endswith("/") and not os.path.exists(
            self.args.destination
        ):
            os.makedirs(self.args.destination)

        while True:
            tag, v = recv(
                self.rd, timeout=self.args.timeout, compress_file=self.args.compress
            )

            if tag == MESSAGE_TAG.ASK_FILE_LIST:
                destination_files = generate_file_list(
                    [self.destination],
                    self.logger,
                    recursive=self.args.recursive,
                    directory=True,
                    options=generate_file_list_flags_from_args(self.args),
                )
                send(
                    self.wr,
                    MESSAGE_TAG.FILE_LIST,
                    destination_files,
                    timeout=self.args.timeout,
                    logger=self.logger,
                )
            elif tag == MESSAGE_TAG.PING:
                send(
                    self.wr,
                    MESSAGE_TAG.PONG,
                    None,
                    timeout=self.args.timeout,
                    logger=self.logger,
                )
            elif tag == MESSAGE_TAG.FILE_LIST:
                self.logger.info(f"File list received {v}")

                source_files = v

                pid = os.fork()

                # Once the file list is received, we start the generator
                if pid == 0:
                    self.rd.close()
                    destination_files = generate_file_list(
                        [self.destination],
                        self.logger,
                        recursive=self.args.recursive,
                        directory=True,
                        options=generate_file_list_flags_from_args(self.args),
                    )
                    generator = Generator(
                        self.wr,
                        self.source,
                        self.destination,
                        source_files,
                        destination_files,
                        self.logger,
                        self.args,
                    )
                    generator.run()
                    sys.exit(0)
            elif tag == MESSAGE_TAG.FILE_DATA:
                (file_name, file_info, start, end, whole_file, data) = v
                source = file_info["source"]

                if file_name != "" and not self.source[source].endswith("/"):
                    # The file is in a subdirectory, in recursive mode
                    file_name = os.path.join(
                        os.path.basename(self.source[source]), file_name
                    )

                if self.destination.endswith("/"):
                    target_path = (
                        os.path.join(self.destination, file_name)
                        if file_name != "" and file_name != "/"
                        else os.path.join(
                            self.destination, os.path.basename(self.source[source])
                        )
                    )
                else:
                    target_path = self.destination

                if file_name == "/":
                    target_path += "/"

                # Check whether the file needs to be created or modified
                if not os.path.exists(target_path):
                    self.handle_file_creation(target_path, data, file_info)
                else:
                    self.handle_file_modification(
                        target_path, start, end, whole_file, file_info, data
                    )
            elif tag == MESSAGE_TAG.FILE_DATA_OFFSET:
                (file_name, start, end, offset) = v
                self.handle_file_offset(file_name, start, end, offset)
            elif tag == MESSAGE_TAG.DELETE_FILES:
                self.handle_file_deletion(v)
            elif tag == MESSAGE_TAG.END:
                self.logger.info("Server: End of transmission")
                send(
                    self.wr,
                    MESSAGE_TAG.SERVER_FINISHED,
                    None,
                    timeout=self.args.timeout,
                    logger=self.logger,
                )
                break

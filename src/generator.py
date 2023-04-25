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
from os import path
from typing import List, Tuple

from src.checksum import Checksum
from src.filelist import FileType
from src.message import send, MESSAGE_TAG, MessageMethod


class Generator:
    def __init__(self, write_server: MessageMethod, source, destination, source_list: List[dict], destination_list: List[dict], logger,
                 args):
        # Sort source and destination lists with dict.path
        self.source_list = sorted(source_list, key=lambda x: x["path"])
        self.source_path_list = [x["path"] for x in self.source_list]
        self.destination_list = sorted(destination_list, key=lambda x: x["path"])
        self.destination_path_list = [x["path"] for x in self.destination_list]
        self.source = source
        self.destination = destination
        self.write_server = write_server
        self.logger = logger
        self.args = args

    def get_missing_files(self) -> Tuple[List[str], List[int]]:
        """
        Returns a list of files that are in the source list but not in the destination list.
        :return: List of missing files
        """

        files = []
        sources = []

        for file_info in self.source_list:
            file = file_info["path"]
            file = file if file != "" else path.basename(self.source[file_info["source"]])

            if file != "" and not self.source[file_info["source"]].endswith("/") and file != path.basename(self.source[file_info["source"]]):
                # The file is in a subdirectory, in recursive mode
                file = path.join(path.basename(self.source[file_info["source"]]), file)

            if not self.destination.endswith("/") and file != path.basename(self.destination):
                file = ''

            if file not in self.destination_path_list:
                files.append(file_info["path"])
                sources.append(file_info["source"])

        return files, sources

    def get_extra_files(self) -> List[str]:
        """
        Returns a list of files that are in the destination list but not in the source list.
        :return: List of extra files
        """

        files = []

        for file_info in self.destination_list:
            file = file_info["path"]
            file = file if file != "" else path.basename(self.destination)

            found = False
            for source in self.source_list:
                source_file = source["path"]
                source_file = source_file if source_file != "" else path.basename(self.source[source["source"]])

                if source_file != "" and not self.source[source["source"]].endswith("/") and source_file != path.basename(
                        self.source[source["source"]]):
                    # The file is in a subdirectory, in recursive mode
                    source_file = path.join(path.basename(self.source[source["source"]]), source_file)

                if not self.destination.endswith("/") and source_file != path.basename(self.destination):
                    if '' in self.destination_path_list:
                        found = True

                    continue

                if source_file == file:
                    found = True
                    break
            if not found:
                files.append(file_info["path"])

        return files

    def get_modified_files(self) -> Tuple[List[str], List[int], List[List[int]], List[int]]:
        """
        Returns a list of files that are in both the source and destination lists, but have different checksums.
        :return: List of modified files
        """

        modified_files = []
        sources = []
        checksums = []
        total_lengths = []

        for file_info in self.source_list:
            file = file_info["path"]
            file = file if file != "" else path.basename(self.source[file_info["source"]])

            if file != "" and not self.source[file_info["source"]].endswith("/"):
                # The file is in a subdirectory, in recursive mode
                file = path.join(path.basename(self.source[file_info["source"]]), file)

            if not self.destination.endswith("/") and file != path.basename(self.destination):
                file = ''

            # Check if file is in destination list
            if file in self.destination_path_list:
                # Skip directories
                if file_info["type"] == FileType.DIRECTORY.value:
                    continue

                destination_index = self.destination_path_list.index(file)
                destination_info = self.destination_list[destination_index]
                is_modified = False

                # Check if file is modified
                if self.args.checksum:
                    if file_info["checksum"] != destination_info[
                        "checksum"]:
                        self.logger.debug(
                            f"File {file} has different checksum. (Source: {file_info['checksum']}, Destination: {destination_info['checksum']})")
                        is_modified = True
                else:
                    if file_info["size"] != destination_info["size"]:
                        is_modified = True
                        self.logger.debug(
                            f"File {file} has different size. (Source: {file_info['size']}, Destination: {destination_info['size']})")
                    elif not self.args.ignore_times and file_info["mtime"] != destination_info["mtime"]:
                        is_modified = True
                        self.logger.debug(
                            f"File {file} has different modification time. (Source: {file_info['mtime']}, Destination: {destination_info['mtime']})")

                if is_modified:
                    modified_files.append(file_info["path"])
                    sources.append(file_info["source"])
                    if destination_info["path"] == '':
                        destination_path = self.destination
                    else:
                        destination_path = path.join(self.destination, destination_info["path"])

                    # Amount of blocks calculated from the total file size
                    # Block size is calculated like the real rsync
                    block_size = 700
                    if file_info["size"] > 490000:
                        # Square root of the file size (rounded up to a multiple of 8)
                        block_size = int(2 ** ((file_info["size"] - 1).bit_length() + 1) ** 0.5)

                    # Maximum blocks size 131kB
                    if block_size > 131072:
                        block_size = 131072

                    amount_of_blocks = int(file_info["size"] / block_size)

                    if file_info["size"] % block_size != 0:
                        amount_of_blocks += 1

                    if amount_of_blocks == 0:
                        amount_of_blocks = 1

                    # Calculate checksums
                    checksum = Checksum(destination_path, divide=amount_of_blocks)
                    checksums.append(checksum.checksums)
                    total_lengths.append(checksum.totalLength)

        return modified_files, sources, checksums, total_lengths

    def ask_file(self, path: str, source: int, checksums: List[int], total_length: int):
        """
        Asks the client to send a file.
        :param path: Path of the file
        :param source: Source of the file
        :param checksums: Checksums of the file
        :param total_length: Total length of the file
        :return: None
        """

        send(self.write_server, MESSAGE_TAG.ASK_FILE_DATA, (path, source, checksums, total_length),
             timeout=self.args.timeout)

    def ask_files(self, files: List[str], sources: List[int], checksums: List[List[int]], total_lengths: List[int]):
        """
        Asks the client to send multiple files.
        :param files: A list of paths
        :param sources: A list of sources
        :param checksums: A list of checksums
        :param total_lengths: A list of total lengths
        :return: None
        """

        for i in range(len(files)):
            self.ask_file(files[i], sources[i], checksums[i], total_lengths[i])

    def run(self):
        """
        Runs the generator.
        """

        missing_files, files_sources = self.get_missing_files()
        extra_files = self.get_extra_files()
        (modified_files, modified_sources, checksums, total_lengths) = self.get_modified_files()

        if missing_files:
            self.logger.debug("Missing files:")
            # Ask for missing files, -1 means ask for the whole file
            self.ask_files(missing_files, files_sources, [[] for _ in missing_files], [-1 for _ in missing_files])
        else:
            self.logger.debug("No missing files.")

        if extra_files:
            self.logger.debug("Extra files:")
            if self.args.delete:
                self.logger.debug(f"Deleting extra files {extra_files}...")
                send(self.write_server, MESSAGE_TAG.DELETE_FILES, extra_files, timeout=self.args.timeout)
            else:
                self.logger.debug(f"Ignoring extra files {extra_files}...")

        else:
            self.logger.debug("No extra files.")

        if modified_files:
            self.logger.debug("Modified files:")
            self.ask_files(modified_files, modified_sources, checksums, total_lengths)
        else:
            self.logger.debug("No modified files.")

        self.logger.info("Generator finished")
        send(self.write_server, MESSAGE_TAG.GENERATOR_FINISHED, None, timeout=self.args.timeout)
        self.write_server.close()

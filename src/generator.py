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
from typing import List, Tuple, Any

from checksum import Checksum
from message import send, MESSAGE_TAG
from filelist import FileType


class Generator:
    def __init__(self, write_server, source, destination, source_list: List[dict], destination_list: List[dict], logger,
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

    def get_missing_files(self) -> List[str]:
        """
        Returns a list of files that are in the source list but not in the destination list.
        :return: List of missing files
        """

        files = []

        for file_info in self.source_list:
            file = file_info["path"]
            if (file != "" or file == "" and path.basename(
                    self.source[
                        file_info[
                            'source']]) not in self.destination_path_list) and file not in self.destination_path_list:
                files.append(file)

        return files

    def get_extra_files(self) -> List[str]:
        """
        Returns a list of files that are in the destination list but not in the source list.
        :return: List of extra files
        """

        files = []

        for file_info in self.destination_list:
            file = file_info["path"]
            if (file != "" or file == "" and path.basename(
                    self.destination) not in self.source_path_list) and file not in self.source_path_list:
                files.append(file)

        return files

    def get_modified_files(self) -> Tuple[List[str], List[List[int]], List[int]]:
        """
        Returns a list of files that are in both the source and destination lists, but have different checksums.
        :return: List of modified files
        """

        modified_files = []
        checksums = []
        total_lengths = []

        for file_info in self.source_list:
            if file_info["path"] not in self.destination_path_list:
                continue
            file = file_info["path"]
            if (file != "" or file == "" and path.basename(
                    self.source[
                        file_info['source']]) in self.destination_path_list) or file in self.destination_path_list:

                if file_info["type"] == FileType.DIRECTORY.value:
                    continue

                destination_index = self.destination_path_list.index(file)
                destination_info = self.destination_list[destination_index]
                is_modified = False

                if self.args.checksum:
                    if file_info["checksum"] != destination_info[
                        "checksum"]:
                        self.logger.debug(f"File {file} has different checksum. (Source: {file_info['checksum']}, Destination: {destination_info['checksum']})")
                        is_modified = True
                else:
                    if file_info["size"] != destination_info["size"]:
                        is_modified = True
                        self.logger.debug(f"File {file} has different size. (Source: {file_info['size']}, Destination: {destination_info['size']})")
                    elif not self.args.ignore_times and file_info["mtime"] != destination_info["mtime"]:
                        is_modified = True
                        self.logger.debug(f"File {file} has different modification time. (Source: {file_info['mtime']}, Destination: {destination_info['mtime']})")

                if is_modified:
                    modified_files.append(file)
                    destination_path = path.join(self.destination, destination_info["path"])
                    checksum = Checksum(destination_path)
                    checksums.append(checksum.checksums)
                    total_lengths.append(checksum.totalLength)

        return modified_files, checksums, total_lengths

    def ask_file(self, file, checksums: List[int], total_length: int):
        send(self.write_server, MESSAGE_TAG.ASK_FILE_DATA, (file, checksums, total_length), timeout=self.args.timeout)

    def ask_files(self, files: List[str], checksums: List[List[int]], total_lengths: List[int]):
        for i in range(len(files)):
            self.ask_file(files[i], checksums[i], total_lengths[i])

    def run(self):
        """
        Runs the generator.
        """

        missing_files = self.get_missing_files()
        extra_files = self.get_extra_files()
        (modified_files, checksums, total_lengths) = self.get_modified_files()

        if missing_files:
            self.logger.debug("Missing files:")
            # Ask for missing files, -1 means ask for the whole file
            self.ask_files(missing_files, [[] for _ in missing_files], [-1 for _ in missing_files], [-1 for _ in missing_files])
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
            self.ask_files(modified_files, checksums, total_lengths)
        else:
            self.logger.debug("No modified files.")

        self.logger.info("Generator finished")
        send(self.write_server, MESSAGE_TAG.GENERATOR_FINISHED, None, timeout=self.args.timeout)
        os.close(self.write_server)

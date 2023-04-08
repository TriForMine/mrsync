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

from checksum import Checksum
from message import send, MESSAGE_TAG


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

    def get_modified_files(self) -> Tuple[List[str], List[List[Tuple[int, int]]]]:
        """
        Returns a list of files that are in both the source and destination lists, but have different checksums.
        :return: List of modified files
        """

        modified_files = []
        bytes = []

        for file_info in self.source_list:
            if file_info not in self.destination_list:
                continue
            file = file_info["path"]
            if (file != "" or file == "" and path.basename(
                    self.source[
                        file_info['source']]) in self.destination_path_list) or file in self.destination_path_list:
                source_path = path.join(self.source[0], file) if file != "" else self.source[file_info['source']]
                destination_path = path.join(self.destination, file) if file != "" else path.join(self.destination,
                                                                                                  path.basename(
                                                                                                      self.source[
                                                                                                          file_info[
                                                                                                              'source']]))

                if path.isdir(source_path):
                    continue  # Skip directories
                if path.isdir(destination_path):
                    continue  # Skip directories

                optimal_file_division = 2
                if self.args.whole_file:
                    optimal_file_division = 1

                source_checksum = Checksum(source_path, divide=optimal_file_division)
                modified_file_bytes = source_checksum.compare_with_file(destination_path)

                if len(modified_file_bytes) > 0:
                    modified_files.append(file)
                    # Calculate bytes to send
                    bytes += [modified_file_bytes]

        return modified_files, bytes

    def ask_file(self, file, parts: List[Tuple[int, int, int]] = None):
        for part in parts:
            if part[2] == 0:
                self.logger.debug(f"Asking for file {file} from byte {part[0]} to byte {part[1]}...")
            else:
                self.logger.debug(f"Asking for modifying file {file} from byte {part[0]} to byte {part[1]} with an offset of {part[2]}...")
            send(self.write_server, MESSAGE_TAG.ASK_FILE_DATA, (file, part), timeout=self.args.timeout)

    def ask_files(self, files: List[str], files_parts: List[List[Tuple[int, int, int]]]):
        for i in range(len(files)):
            self.ask_file(files[i], files_parts[i])

    def run(self):
        """
        Runs the generator.
        """

        missing_files = self.get_missing_files()
        extra_files = self.get_extra_files()
        (modified_files, modified_files_parts) = self.get_modified_files()

        if missing_files:
            self.logger.debug("Missing files:")
            # Ask for missing files, -1 means ask for the whole file
            self.ask_files(missing_files, [[(-1, -1, 0)] for _ in range(len(missing_files))])
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
            self.ask_files(modified_files, modified_files_parts)
        else:
            self.logger.debug("No modified files.")

        self.logger.info("Generator finished")
        send(self.write_server, MESSAGE_TAG.GENERATOR_FINISHED, None, timeout=self.args.timeout)
        os.close(self.write_server)

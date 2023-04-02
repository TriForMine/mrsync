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
from os import path
from typing import List

from checksum import Checksum
from message import send, MESSAGE_TAG


class Generator:
    def __init__(self, write_server, source, destination, source_list, destination_list, logger):
        self.source_list = sorted(source_list)
        self.destination_list = sorted(destination_list)
        self.source = source
        self.destination = destination
        self.write_server = write_server
        self.logger = logger

    def get_missing_files(self) -> List[str]:
        """
        Returns a list of files that are in the source list but not in the destination list.
        :return: List of missing files
        """

        return [file for file in self.source_list if file not in self.destination_list]

    def get_extra_files(self) -> List[str]:
        """
        Returns a list of files that are in the destination list but not in the source list.
        :return: List of extra files
        """

        return [file for file in self.destination_list if file not in self.source_list]

    def get_modified_files(self) -> List[str]:
        """
        Returns a list of files that are in both the source and destination lists, but have different checksums.
        :return: List of modified files
        """

        modified_files = []

        for file in self.source_list:
            if file in self.destination_list:
                if path.isdir(path.join(self.source[0], file)):
                    continue  # Skip directories
                source_checksum = Checksum(path.join(self.source[0], file))
                destination_checksum = Checksum(path.join(self.destination, file))

                if source_checksum != destination_checksum:
                    modified_files.append(file)

        return modified_files

    def send_file(self, files):
        for file in files:
            self.logger.debug(f"Sending file {file}...")
            send(self.write_server, MESSAGE_TAG.ASK_FILE_DATA, file)

    def run(self):
        """
        Runs the generator.
        """

        missing_files = self.get_missing_files()
        extra_files = self.get_extra_files()
        modified_files = self.get_modified_files()

        if missing_files:
            print("Missing files:")
            for file in missing_files:
                self.logger.debug(f"Asking for file {file}...")
                send(self.write_server, MESSAGE_TAG.ASK_FILE_DATA, file)
        else:
            print("No missing files.")

        if extra_files:
            print("Extra files:")
            for file in extra_files:
                print(file)
        else:
            print("No extra files.")

        if modified_files:
            print("Modified files:")
            for file in modified_files:
                self.logger.debug(f"Asking for file {file}...")
                send(self.write_server, MESSAGE_TAG.ASK_FILE_DATA, file)
        else:
            print("No modified files.")

        self.logger.info("Generator finished")
        send(self.write_server, MESSAGE_TAG.GENERATOR_FINISHED, None)

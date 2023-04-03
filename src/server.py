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
import sys
from argparse import Namespace
from os import path

from filelist import generate_file_list
from generator import Generator
from logger import Logger
from message import recv, send, MESSAGE_TAG


class Server:
    def __init__(self, source: str, destination: str, rd: int, wr: int, logger: Logger, args: Namespace):
        self.logger = logger
        self.source = source
        self.destination = destination
        self.rd = rd
        self.wr = wr
        self.args = args

    def run(self):
        self.logger.info('Server started')
        self.loop()
        self.logger.info('Server stopped')
        sys.exit(0)

    def handle_file_creation(self, file: str, data: bytes):
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

    def handle_file_deletion(self, files: list):
        if files is None:
            return

        for file in files:
            self.logger.info(f"Deleting {file}...")
            if path.isdir(path.join(self.destination, file)):
                os.rmdir(path.join(self.destination, file))
            else:
                os.remove(path.join(self.destination, file))

    def loop(self):
        destination_files = generate_file_list([self.destination], self.logger, recursive=self.args.recursive,
                                               directory=True)

        send(self.wr, MESSAGE_TAG.ASK_FILE_LIST, None)
        while True:
            tag, v = recv(self.rd)

            if tag == MESSAGE_TAG.FILE_LIST:
                self.logger.info(f'File list received {v}')

                source_files = v

                pid = os.fork()

                if pid == 0:
                    os.close(self.rd)
                    generator = Generator(self.wr, self.source, self.destination, source_files, destination_files,
                                          self.logger, self.args)
                    generator.run()
                    sys.exit(0)
            elif tag == MESSAGE_TAG.FILE_DATA:
                (file_name, data) = v
                self.handle_file_creation(file_name, data)
            elif tag == MESSAGE_TAG.DELETE_FILES:
                self.handle_file_deletion(v)
            elif tag == MESSAGE_TAG.END:
                self.logger.info('Server: End of transmission')
                break

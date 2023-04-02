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
from argparse import Namespace
from os import path
from typing import List

from filelist import generate_file_list
from logger import Logger
from message import recv, MESSAGE_TAG, send


class Client:
    def __init__(self, sources: List[str], rd: int, wr: int, server_pid: int, logger: Logger, args: Namespace):
        self.logger = logger
        self.sources = sources
        self.rd = rd
        self.wr = wr
        self.server_pid = server_pid
        self.args = args

    def run(self):
        running = True
        while running:
            (tag, v) = recv(self.rd)

            if tag == MESSAGE_TAG.ASK_FILE_LIST:
                self.logger.info('File list requested')
                file_list = generate_file_list(self.sources, self.logger, recursive=self.args.recursive)
                send(self.wr, MESSAGE_TAG.FILE_LIST, file_list)
            elif tag == MESSAGE_TAG.ASK_FILE_DATA:
                self.logger.info(f'File data requested for {v}')
                if path.isdir(path.join(self.sources[0], v)):
                    send(self.wr, MESSAGE_TAG.FILE_DATA, (v + '/', b''))
                else:
                    with open(path.join(self.sources[0], v), 'rb') as f:
                        data = f.read()
                        send(self.wr, MESSAGE_TAG.FILE_DATA, (v, data))
            elif tag == MESSAGE_TAG.END:
                send(self.wr, MESSAGE_TAG.END, None)
                self.logger.debug('End of transmission')
                running = False
                break
            elif tag == MESSAGE_TAG.GENERATOR_FINISHED:
                self.logger.debug('[Stopping] Generator finished')
                running = False
                break

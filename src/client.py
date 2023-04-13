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
from argparse import Namespace
from os import path
from typing import List

from checksum import Checksum
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
        generator_finished = False
        server_finished = False

        while not (generator_finished and server_finished):
            (tag, v) = recv(self.rd, timeout=self.args.timeout)

            if tag == MESSAGE_TAG.ASK_FILE_LIST:
                self.logger.info('File list requested')
                file_list = generate_file_list(self.sources, self.logger, recursive=self.args.recursive,
                                               directory=self.args.dirs, options=v)
                send(self.wr, MESSAGE_TAG.FILE_LIST, file_list, timeout=self.args.timeout, logger=self.logger)
            elif tag == MESSAGE_TAG.ASK_FILE_DATA:
                (filename, source, checksums, total_length) = v

                target_path = path.join(self.sources[source], filename) if filename != '' else self.sources[source]
                self.logger.info(f'File data requested for {target_path}')
                if path.isdir(target_path):
                    m_time = os.path.getmtime(target_path)
                    send(self.wr, MESSAGE_TAG.FILE_DATA, (filename + '/', source, 0, 0, True, m_time, b''),
                         timeout=self.args.timeout,
                         logger=self.logger)
                else:
                    with open(target_path, "rb") as f:
                        m_time = os.path.getmtime(target_path)

                        if not checksums:
                            send(self.wr, MESSAGE_TAG.FILE_DATA, (filename, source, 0, 0, True, m_time, f.read()),
                                 timeout=self.args.timeout,
                                 logger=self.logger)
                            continue

                        destination_checksum = Checksum("", checksums=checksums,
                                                        part_length=total_length / len(checksums),
                                                        total_length=total_length)
                        parts = destination_checksum.compare_with_file(target_path)

                        if len(parts) == 0:
                            self.logger.info(f'File {filename} is already up to date')
                            send(self.wr, MESSAGE_TAG.FILE_DATA, (filename, source, 0, 0, False, m_time, b''),
                                 timeout=self.args.timeout,
                                 logger=self.logger)
                            continue
                        else:
                            for part in parts:
                                if part[2] > 0:
                                    send(self.wr, MESSAGE_TAG.FILE_DATA_OFFSET, (filename, part[0], part[1], part[2]),
                                         timeout=self.args.timeout, logger=self.logger)
                                elif part[0] == -1 or part[1] == -1:
                                    send(self.wr, MESSAGE_TAG.FILE_DATA,
                                         (filename, source, 0, 0, True, m_time, f.read()),
                                         timeout=self.args.timeout,
                                         logger=self.logger)
                                else:
                                    f.seek(part[0])
                                    data = f.read(part[1] - part[0] + 1)
                                    send(self.wr, MESSAGE_TAG.FILE_DATA,
                                         (filename, source, part[0], part[1], False, m_time, data),
                                         timeout=self.args.timeout, logger=self.logger)
            elif tag == MESSAGE_TAG.END:
                self.logger.debug('End of transmission')
                break
            elif tag == MESSAGE_TAG.GENERATOR_FINISHED:
                send(self.wr, MESSAGE_TAG.END, None, timeout=self.args.timeout, logger=self.logger)
                self.logger.debug('[Client] Generator finished')
                generator_finished = True
            elif tag == MESSAGE_TAG.SERVER_FINISHED:
                self.logger.debug('[Client] Server finished')
                server_finished = True
            elif tag == MESSAGE_TAG.DELETE_FILES:
                self.logger.info(f'Deleting files {v}')
                send(self.wr, MESSAGE_TAG.DELETE_FILES, v, timeout=self.args.timeout, logger=self.logger)
            else:
                raise Exception(f'Unknown message tag {tag}')

        self.logger.debug('Client finished')
        os.close(self.rd)
        os.close(self.wr)

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

from src.checksum import Checksum
from src.filelist import (
    generate_file_list,
    generate_info,
    generate_file_list_flags_from_args,
)
from src.logger import Logger
from src.message import recv, MESSAGE_TAG, send, MessageMethod


class Client:
    def __init__(
        self,
        sources: List[str],
        rd: MessageMethod,
        wr: MessageMethod,
        logger: Logger,
        args: Namespace,
    ):
        self.logger = logger
        self.sources = sources
        self.rd = rd
        self.wr = wr
        self.args = args

    def run(self):
        """
        Run the client
        :return:
        """
        generator_finished = False
        server_finished = False

        while not (generator_finished and server_finished):
            (tag, v) = recv(self.rd, timeout=self.args.timeout)

            if tag == MESSAGE_TAG.ASK_FILE_LIST:
                self.logger.info("File list requested")
                file_list = generate_file_list(
                    self.sources,
                    self.logger,
                    recursive=self.args.recursive,
                    directory=self.args.dirs,
                    options=v,
                )
                send(
                    self.wr,
                    MESSAGE_TAG.FILE_LIST,
                    file_list,
                    timeout=self.args.timeout,
                    logger=self.logger,
                )
            elif tag == MESSAGE_TAG.PING:
                send(
                    self.wr,
                    MESSAGE_TAG.PONG,
                    timeout=self.args.timeout,
                    logger=self.logger,
                )
            elif tag == MESSAGE_TAG.ASK_FILE_DATA:
                (filename, source, checksums, total_length) = v

                # If the filename is empty, it means that the file is the source itself
                target_path = (
                    path.join(self.sources[source], filename)
                    if filename != ""
                    else self.sources[source]
                )

                file_info = generate_info(
                    target_path,
                    generate_file_list_flags_from_args(self.args),
                    source,
                    False,
                )

                self.logger.info(f"File data requested for {target_path}")
                if path.isdir(target_path):
                    send(
                        self.wr,
                        MESSAGE_TAG.FILE_DATA,
                        (filename + "/", file_info, 0, 0, True, b""),
                        timeout=self.args.timeout,
                        logger=self.logger,
                        compress_file=self.args.compress,
                        compress_level=self.args.compress_level,
                    )
                else:
                    with open(target_path, "rb") as f:
                        # If there are no checksums, it means that the file is new
                        if not checksums:
                            send(
                                self.wr,
                                MESSAGE_TAG.FILE_DATA,
                                (filename, file_info, 0, 0, True, f.read()),
                                timeout=self.args.timeout,
                                logger=self.logger,
                                compress_file=self.args.compress,
                                compress_level=self.args.compress_level,
                            )
                            continue

                        # Calculate the parts that need to be sent
                        destination_checksum = Checksum(
                            "",
                            checksums=checksums,
                            part_length=total_length / len(checksums),
                            total_length=total_length,
                        )
                        parts = destination_checksum.compare_with_file(target_path)

                        # If there are no parts, it means that the file is already up-to-date
                        # Ask for the server to update the modification time
                        if len(parts) == 0:
                            self.logger.info(f"File {filename} is already up to date")
                            send(
                                self.wr,
                                MESSAGE_TAG.FILE_DATA,
                                (filename, file_info, 0, 0, False, b""),
                                timeout=self.args.timeout,
                                logger=self.logger,
                                compress_file=self.args.compress,
                                compress_level=self.args.compress_level,
                            )
                            continue
                        else:
                            # Request for all the parts
                            for part in parts:
                                if part[2] > 0:
                                    send(
                                        self.wr,
                                        MESSAGE_TAG.FILE_DATA_OFFSET,
                                        (filename, part[0], part[1], part[2]),
                                        timeout=self.args.timeout,
                                        logger=self.logger,
                                        compress_file=self.args.compress,
                                        compress_level=self.args.compress_level,
                                    )
                                elif part[0] == -1 or part[1] == -1:
                                    # If the part is -1, it means that the file needs to be sent entirely
                                    send(
                                        self.wr,
                                        MESSAGE_TAG.FILE_DATA,
                                        (filename, file_info, 0, 0, True, f.read()),
                                        timeout=self.args.timeout,
                                        logger=self.logger,
                                        compress_file=self.args.compress,
                                        compress_level=self.args.compress_level,
                                    )
                                else:
                                    f.seek(part[0])
                                    data = f.read(part[1] - part[0] + 1)
                                    send(
                                        self.wr,
                                        MESSAGE_TAG.FILE_DATA,
                                        (
                                            filename,
                                            file_info,
                                            part[0],
                                            part[1],
                                            False,
                                            data,
                                        ),
                                        timeout=self.args.timeout,
                                        logger=self.logger,
                                        compress_file=self.args.compress,
                                        compress_level=self.args.compress_level,
                                    )
            elif tag == MESSAGE_TAG.END:
                self.logger.debug("End of transmission")
                break
            elif tag == MESSAGE_TAG.GENERATOR_FINISHED:
                send(
                    self.wr,
                    MESSAGE_TAG.END,
                    None,
                    timeout=self.args.timeout,
                    logger=self.logger,
                )
                self.logger.debug("[Client] Generator finished")
                generator_finished = True
            elif tag == MESSAGE_TAG.SERVER_FINISHED:
                self.logger.debug("[Client] Server finished")
                server_finished = True
            elif tag == MESSAGE_TAG.DELETE_FILES:
                self.logger.info(f"Deleting files {v}")
                send(
                    self.wr,
                    MESSAGE_TAG.DELETE_FILES,
                    v,
                    timeout=self.args.timeout,
                    logger=self.logger,
                )
            else:
                raise Exception(f"Unknown message tag {tag}")

        self.logger.debug("Client finished")
        self.rd.close()
        self.wr.close()

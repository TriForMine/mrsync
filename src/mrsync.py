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
import pwd
import signal
import sys
import select
import socket
from argparse import Namespace

from src.client import Client
from src.demon import Daemon
from src.filelist import (
    print_file_list,
    FileListInfo,
    generate_file_list,
    generate_file_list_flags_from_args,
)
from src.logger import Logger
from src.message import (
    FileDescriptorMethod,
    recv,
    SocketMethod,
    send,
    MESSAGE_TAG,
    SOCKET_IDENTIFICATION,
)
from src.options import get_args
from src.server import Server
from src.utils import parse_path


def main(args=None):
    logger = Logger()
    args = get_args(logger, program_args=args)
    logger = Logger(to_file=(args.daemon or args.server))
    logger.verbose = args.verbose
    logger.quiet = args.quiet

    if len(args.source[0]) > 0:
        (
            parsed_source_mode,
            parsed_source_user,
            parsed_source_host,
            parsed_source_destination,
        ) = parse_path(args.source[0][0])

        if parsed_source_user is None:
            parsed_source_user = pwd.getpwuid(os.getuid()).pw_name
    else:
        parsed_source_mode = "local"
        parsed_source_user = None
        parsed_source_host = None
        parsed_source_destination = None

    if args.list_only and not (args.server or args.daemon):
        file_list = []

        logger.debug_mode = True
        if parsed_source_mode == "local":
            file_list = generate_file_list(
                args.source[0],
                logger,
                recursive=args.recursive,
                directory=args.dirs,
                options=FileListInfo.PERMISSIONS.value
                | FileListInfo.FILE_SIZE.value
                | FileListInfo.FILE_TIMES.value,
            )
        elif parsed_source_mode == "ssh":
            rd_server, wr_client = os.pipe()
            rd_client, wr_server = os.pipe()
            pid = os.fork()
            if pid == 0:
                send(
                    FileDescriptorMethod(wr_server),
                    MESSAGE_TAG.ASK_FILE_LIST,
                    FileListInfo.PERMISSIONS.value
                    | FileListInfo.FILE_SIZE.value
                    | FileListInfo.FILE_TIMES.value,
                )
                tag, file_list = recv(FileDescriptorMethod(rd_server))
            else:
                # Redirect rd_client to stdin and wr_client to stdout
                os.dup2(rd_client, 0)
                os.dup2(wr_client, 1)

                os.execv(
                    "/usr/bin/ssh",
                    [
                        "ssh",
                        "-e",
                        "none",
                        "-l",
                        parsed_source_user,
                        parsed_source_host,
                        "--",
                        "python3",
                        "mrsync.py",
                        "--server",
                    ]
                    + sys.argv[1:],
                )
                exit(0)
        elif parsed_source_mode == "daemon":
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.connect((parsed_source_host, args.port))
            except ConnectionRefusedError:
                logger.error("Could not connect to daemon")
                exit(1)

            message = b"run " + " ".join(sys.argv[1:]).encode("utf-8") + b"\n"
            sock.sendall(len(message).to_bytes(4, byteorder="big"))
            sock.sendall(message)

            send(
                SocketMethod(sock),
                MESSAGE_TAG.SOCKET_IDENTIFICATION,
                SOCKET_IDENTIFICATION.CLIENT,
            )
            send(
                SocketMethod(sock),
                MESSAGE_TAG.ASK_FILE_LIST,
                FileListInfo.PERMISSIONS.value
                | FileListInfo.FILE_SIZE.value
                | FileListInfo.FILE_TIMES.value,
            )

            _, identification = recv(SocketMethod(sock))
            flag, file_list = recv(SocketMethod(sock))
            sock.close()
        print_file_list(args.source[0], logger, file_list)
        exit(0)

    if args.server:
        if parsed_source_mode == "ssh":
            args.source[0] = [parsed_source_destination]
            client = Client(
                args.source[0],
                FileDescriptorMethod(0),
                FileDescriptorMethod(1),
                logger,
                args,
            )
            client.run()
            exit(0)
        else:
            (
                parsed_destination_mode,
                parsed_destination_user,
                parsed_destination_host,
                parsed_destination,
            ) = parse_path(args.destination)
            args.destination = parsed_destination

            # rd_server is stdin and wr_server is stdout
            server = Server(
                args.source[0],
                args.destination,
                FileDescriptorMethod(0),
                FileDescriptorMethod(1),
                logger,
                args,
            )
            server.run()
            exit(0)

    if args.daemon:
        daemon = Daemon(logger, args)
        daemon.run()
        exit(0)

    # SSH will only be able to ask for the password if it is in the foreground, so only the parent process will be able to be used to execute SSH
    # So depending on if destination is local or remote, the parent process will be the client or the server
    # If both source and destination are ssh, the program will exit with an error
    (
        parsed_destination_mode,
        parsed_destination_user,
        parsed_destination_host,
        parsed_destination,
    ) = parse_path(args.destination)

    if parsed_source_mode == "ssh" and parsed_destination_mode == "ssh":
        logger.error("Cannot use SSH for both source and destination")
        exit(1)

    if parsed_source_mode == "ssh" and len(args.source[0]) > 1:
        logger.error("Cannot use multiple sources with SSH")
        exit(1)

    if parsed_source_mode == "daemon" and parsed_destination_mode == "daemon":
        logger.error("Cannot use daemon for both source and destination")
        exit(1)

    if parsed_source_mode == "daemon" and len(args.source[0]) > 1:
        logger.error("Cannot use multiple sources with daemon")
        exit(1)

    rd_server, wr_client = os.pipe()
    rd_client, wr_server = os.pipe()

    pid = os.fork()

    if (pid > 0 and parsed_destination_mode == "ssh") or (
        pid == 0 and parsed_destination_mode != "ssh"
    ):
        os.close(wr_client)
        os.close(rd_client)

        args.destination = parsed_destination

        if parsed_destination_mode == "local":
            server = Server(
                args.source[0],
                args.destination,
                FileDescriptorMethod(rd_server),
                FileDescriptorMethod(wr_server),
                logger,
                args,
            )
            server.run()
        elif parsed_destination_mode == "ssh":
            if not parsed_destination_user:
                parsed_destination_user = pwd.getpwuid(os.getuid()).pw_name

            # Redirect rd_server to stdin and wr_server to stdout
            os.dup2(rd_server, 0)
            os.dup2(wr_server, 1)

            os.execv(
                "/usr/bin/ssh",
                [
                    "ssh",
                    "-e",
                    "none",
                    "-l",
                    parsed_destination_user,
                    parsed_destination_host,
                    "--",
                    "python3",
                    "mrsync.py",
                    "--server",
                ]
                + sys.argv[1:],
            )
        elif parsed_destination_mode == "daemon":
            logger.debug("Connecting to daemon...")

            # Start a socket client to the daemon and send the "run" command
            # Then redirect rd_client and wr_client to the socket

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.connect((parsed_destination_host, args.port))
            except ConnectionRefusedError:
                logger.error("Could not connect to daemon")
                exit(1)

            message = b"run " + " ".join(sys.argv[1:]).encode("utf-8") + b"\n"
            sock.sendall(len(message).to_bytes(4, byteorder="big"))
            sock.sendall(message)

            logger.debug("Connected to daemon")

            # Send all from rd_client to the socket and read all from the socket and send it to wr_client
            while True:
                r, w, x = select.select([sock, rd_server], [], [])
                if sock in r:
                    flag_identification, identification = recv(SocketMethod(sock))

                    flag, data = recv(SocketMethod(sock))

                    if identification == SOCKET_IDENTIFICATION.CLIENT:
                        send(FileDescriptorMethod(wr_server), flag, data)
                    elif identification == SOCKET_IDENTIFICATION.SERVER:
                        # This should never happen
                        logger.error(
                            "Received message from server while being the server"
                        )
                        exit(1)

                if rd_server in r:
                    flag, data = recv(FileDescriptorMethod(rd_server))

                    if flag == MESSAGE_TAG.END:
                        break

                    send(
                        SocketMethod(sock),
                        MESSAGE_TAG.SOCKET_IDENTIFICATION,
                        SOCKET_IDENTIFICATION.SERVER,
                    )
                    send(SocketMethod(sock), flag, data)
        else:
            logger.error("Unsupported destination mode")
            exit(1)
    else:
        os.close(rd_server)
        os.close(wr_server)

        if parsed_source_mode == "ssh":
            if not parsed_source_user:
                parsed_source_user = pwd.getpwuid(os.getuid()).pw_name

            # Redirect rd_client to stdin and wr_client to stdout
            os.dup2(rd_client, 0)
            os.dup2(wr_client, 1)

            os.execv(
                "/usr/bin/ssh",
                [
                    "ssh",
                    "-e",
                    "none",
                    "-l",
                    parsed_source_user,
                    parsed_source_host,
                    "--",
                    "python3",
                    "mrsync.py",
                    "--server",
                ]
                + sys.argv[1:],
            )
        elif parsed_source_mode == "daemon":
            logger.debug("Connecting to daemon...")

            # Start a socket client to the daemon and send the "run" command
            # Then redirect rd_client and wr_client to the socket

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.connect((parsed_source_host, args.port))
            except ConnectionRefusedError:
                logger.error("Could not connect to daemon")
                # Kill the child process
                os.kill(pid, signal.SIGKILL)
                exit(1)

            message = b"run " + " ".join(sys.argv[1:]).encode("utf-8") + b"\n"
            sock.sendall(len(message).to_bytes(4, byteorder="big"))
            sock.sendall(message)

            logger.debug("Connected to daemon")

            # Send all from rd_client to the socket and read all from the socket and send it to wr_client
            while True:
                r, w, x = select.select([sock, rd_client], [], [])
                if sock in r:
                    flag_identification, identification = recv(SocketMethod(sock))

                    flag, data = recv(SocketMethod(sock))

                    if identification == SOCKET_IDENTIFICATION.CLIENT:
                        # This should never happen
                        logger.error(
                            "Received message from client while being the client"
                        )
                        exit(1)
                    elif identification == SOCKET_IDENTIFICATION.SERVER:
                        send(FileDescriptorMethod(wr_client), flag, data)

                if rd_client in r:
                    flag, data = recv(FileDescriptorMethod(rd_client))

                    if flag == MESSAGE_TAG.END:
                        break

                    send(
                        SocketMethod(sock),
                        MESSAGE_TAG.SOCKET_IDENTIFICATION,
                        SOCKET_IDENTIFICATION.CLIENT,
                    )
                    send(SocketMethod(sock), flag, data)
        else:
            client = Client(
                args.source[0],
                FileDescriptorMethod(rd_client),
                FileDescriptorMethod(wr_client),
                logger,
                args,
            )
            client.run()


if __name__ == "__main__":
    main()

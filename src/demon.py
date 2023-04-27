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
from typing import List

import daemon
import socket
import select

from src.client import Client
from src.logger import Logger
from src.message import (
    recv,
    FileDescriptorMethod,
    send,
    SocketMethod,
    SOCKET_IDENTIFICATION,
    MESSAGE_TAG,
)
from src.options import get_args
from src.server import Server
import os

from src.utils import parse_path


class Daemon:
    """
    The daemon class, which is used to run a socket server in the background.
    And on each client connection, it will run a new server.
    """

    def __init__(self, logger: Logger, args: Namespace):
        self.logger = logger
        self.args = args
        self.clients = []

        # Check if the daemon is already running.
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.connect((self.args.address, self.args.port))
            self.server.send("ping".encode())
            data = self.server.recv(1024)
            data = data.decode()
            if data.startswith("ok"):
                daemon_pid = int(data.split(" ")[1])
                print(
                    "The daemon is already running with PID " + str(daemon_pid) + ".\r"
                )
                exit(1)
            else:
                print(
                    "The daemon is already running but it is not responding. Or another program is using the port.\r"
                )
                exit(1)
        except ConnectionRefusedError:
            self.server.close()
            pass

    def accept_new_client(self):
        """
        Accept a new client connection.
        """
        # Fork a new process to handle the client.
        client, _ = self.server.accept()
        self.clients.append(client)

    def run_server(self, sock: socket.socket, unparsed_args: List[str]):
        """
        Run a new server to handle a client.
        """
        pid = os.fork()

        if pid == 0:
            # Close the server socket.
            self.server.close()

            self.logger.verbose = True

            # Create a pipe to communicate with the socket.
            rd_client, wr_server = os.pipe()
            rd_server, wr_client = os.pipe()

            # Fork a new process to handle the client.
            pid = os.fork()

            # Parse the args.
            args = get_args(self.logger, unparsed_args)

            (
                parsed_source_mode,
                parsed_source_user,
                parsed_source_host,
                parsed_source_destination,
            ) = parse_path(args.source[0][0])

            if pid == 0:
                self.logger.verbose = True

                try:
                    if parsed_source_mode == "daemon":
                        args.source[0] = [parsed_source_destination]
                        self.logger.info(
                            f"[Daemon] Running a new client for socket {sock}"
                        )
                        client = Client(
                            args.source[0],
                            FileDescriptorMethod(rd_client),
                            FileDescriptorMethod(wr_client),
                            self.logger,
                            args,
                        )
                        client.run()
                    else:
                        (
                            parsed_destination_mode,
                            parsed_destination_user,
                            parsed_destination_host,
                            parsed_destination,
                        ) = parse_path(args.destination)
                        args.destination = parsed_destination

                        self.logger.info(
                            f"[Daemon] Running a new server for socket {sock}"
                        )

                        # rd_server is stdin and wr_server is stdout
                        server = Server(
                            args.source[0],
                            args.destination,
                            FileDescriptorMethod(rd_server),
                            FileDescriptorMethod(wr_server),
                            self.logger,
                            args,
                        )
                        server.run()
                except Exception as e:
                    self.logger.error(
                        f"[Daemon] An error occurred while running a new server: {e}"
                    )
                    sock.send("error".encode())
                finally:
                    sock.close()
                    self.clients.remove(sock)
                    exit(0)
            else:
                # Read the data from the socket and write it to the pipe. And read the data from the pipe and write it to the socket.
                # Finish when the child process exits.

                if parsed_source_mode == "daemon":
                    lst = [sock, rd_server]
                else:
                    lst = [sock, rd_client]

                while os.waitpid(pid, os.WNOHANG)[0] == 0:
                    r, _, _ = select.select(lst, [], [])
                    if sock in r:
                        identification_flag, identification = recv(SocketMethod(sock))
                        self.logger.info(
                            "[Daemon] Received identification: " + str(identification)
                        )

                        if identification_flag == MESSAGE_TAG.PING:
                            send(SocketMethod(sock), MESSAGE_TAG.PONG, pid)
                            continue
                        elif identification_flag != MESSAGE_TAG.SOCKET_IDENTIFICATION:
                            self.logger.error(
                                "[Daemon] The socket identification is not correct."
                            )
                            send(SocketMethod(sock), MESSAGE_TAG.END, None)
                            exit(1)

                        flag, data = recv(SocketMethod(sock))
                        self.logger.info("[Daemon] Received flag: " + str(flag))

                        if identification == SOCKET_IDENTIFICATION.CLIENT:
                            send(FileDescriptorMethod(wr_server), flag, data)
                        elif identification == SOCKET_IDENTIFICATION.SERVER:
                            send(FileDescriptorMethod(wr_client), flag, data)

                        if flag == MESSAGE_TAG.END:
                            self.logger.info(
                                f"[Daemon] The child process with PID {pid} exited."
                            )
                            exit(0)

                    if rd_client in r:
                        flag, data = recv(FileDescriptorMethod(rd_client))

                        send(
                            SocketMethod(sock),
                            MESSAGE_TAG.SOCKET_IDENTIFICATION,
                            SOCKET_IDENTIFICATION.CLIENT,
                        )
                        send(SocketMethod(sock), flag, data)

                    if rd_server in r:
                        flag, data = recv(FileDescriptorMethod(rd_server))

                        send(
                            SocketMethod(sock),
                            MESSAGE_TAG.SOCKET_IDENTIFICATION,
                            SOCKET_IDENTIFICATION.SERVER,
                        )
                        send(SocketMethod(sock), flag, data)

            # Exit the process.
            self.logger.info(f"[Daemon] The child process with PID {pid} exited.")
            exit(0)
        else:
            # Do not handle the client in the parent process.
            sock.close()
            self.clients.remove(sock)
            print(
                f"[Daemon] Forked a new process with PID {pid} to handle the client {sock}."
            )

    def handle_client(self, sock: socket.socket):
        """
        Handle a client connection.
        """
        size = int.from_bytes(sock.recv(4), byteorder="big")
        data = sock.recv(size)
        if not data:
            self.clients.remove(sock)
            sock.close()
            return
        data = data.decode()
        if data.startswith("run"):
            args = data.split(" ")[1:]
            # Remove the last line break.
            args[-1] = args[-1][:-1]
            self.logger.info("Running a new server with args: " + str(args))
            self.run_server(sock, args)
        elif data == "ping":
            pid = os.getpid()
            sock.send(("ok " + str(pid)).encode())
            sock.close()
            self.clients.remove(sock)
        else:
            self.logger.error("Invalid command: " + data)
            sock.send("error".encode())
            sock.close()
            self.clients.remove(sock)

    def run(self):
        """
        The main loop of the daemon.
        """
        self.logger.info("Starting daemon...")
        home_dir = os.path.expanduser("~")
        with daemon.DaemonContext(
            stdout=self.logger.stdout,
            stderr=self.logger.stderr,
            detach_process=(not self.args.no_detach),
            working_directory=os.path.join(home_dir),
        ):
            self.logger.info("Daemon started.")

            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind((self.args.address, self.args.port))
            self.server.listen(5)

            self.logger.info(
                "Listening on " + self.args.address + ":" + str(self.args.port)
            )

            with self.server:
                while True:
                    rlist, _, _ = select.select([self.server] + self.clients, [], [])
                    for sock in rlist:
                        if sock is self.server:
                            self.accept_new_client()
                        else:
                            self.handle_client(sock)

        # When the daemon exits, wait for all the child processes to exit.
        while os.waitpid(-1, os.WNOHANG)[0] > 0:
            pass

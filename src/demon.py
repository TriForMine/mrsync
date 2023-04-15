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

import daemon
import socket
import select
from src.logger import Logger
from src.server import Server
import os

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
            if data == "ok":
                print("The daemon is already running.\r")
                exit(1)
            else:
                print("The daemon is already running, but it is not responding.\r")
                exit(1)
        except ConnectionRefusedError:
            pass

    def accept_new_client(self):
        """
        Accept a new client connection.
        """
        # Fork a new process to handle the client.
        client, _ = self.server.accept()
        self.clients.append(client)

    def run_server(self, sock: socket.socket):
        """
        Run a new server.
        """
        pid = os.fork()
        if pid != 0:
            server = Server(self.args.source[0], self.args.destination, logger=self.logger, args=self.args, rd=sock.fileno(), wr=sock.fileno())
            server.run()

    def handle_client(self, sock: socket.socket):
        """
        Handle a client connection.
        """
        data = sock.recv(1024)
        if not data:
            self.clients.remove(sock)
            sock.close()
            return
        data = data.decode()
        if data == "run":
            self.logger.info("Running a new server...")
            sock.send("ok".encode())
            sock.close()
            self.clients.remove(sock)
            self.run_server()
        elif data == "ping":
            sock.send("ok".encode())
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
        with daemon.DaemonContext(stdout=self.logger.stdout, stderr=self.logger.stderr):
            self.logger.info("Daemon started.")

            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind((self.args.address, self.args.port))
            self.server.listen(5)

            self.logger.info("Listening on " + self.args.address + ":" + str(self.args.port))

            while True:
                rlist, _, _ = select.select([self.server] + self.clients, [], [])
                for sock in rlist:
                    if sock is self.server:
                        self.accept_new_client()
                    else:
                        self.handle_client(sock)


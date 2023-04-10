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
import os

from logger import Logger
from options import parse_args
from server import Server


def run_server(source: str, destination: str, rd: int, wr: int, logger: Logger, args: Namespace):
    server = Server(source, destination, rd, wr, logger, args)
    server.run()


def run_daemon():
    args = parse_args()
    logger = Logger(args.verbose)
    logger.info("Starting server...")

    rd, wr = os.pipe()

    with daemon.DaemonContext():
        run_server(args.source, args.destination, rd, wr, logger, args)


if __name__ == '__main__':
    run_daemon()

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

from src.options import get_args
from src.client import Client
from src.demon import run_daemon
from src.filelist import print_file_list
from src.logger import Logger
from src.server import Server

def main(args = None):
    logger = Logger()
    args = get_args(logger, args=args)
    logger.verbose = args.verbose
    logger.quiet = args.quiet

    if args.list_only:
        logger.debug_mode = True
        print_file_list(args.source[0], logger, recursive=args.recursive, directory=args.dirs)
        exit(0)

    rd_server, wr_client = os.pipe()
    rd_client, wr_server = os.pipe()

    if args.server:
        server = Server(args.source[0], args.destination, rd_server, wr_server, logger, args)
        server.run()
        exit(0)

    if args.daemon:
        run_daemon()
        exit(0)

    pid = os.fork()

    if pid > 0:
        os.close(rd_server)
        os.close(wr_server)

        client = Client(args.source[0], rd_client, wr_client, pid, logger, args)
        client.run()
    else:
        os.close(wr_client)
        os.close(rd_client)
        server = Server(args.source[0], args.destination, rd_server, wr_server, logger, args)
        server.run()

if __name__ == '__main__':
    main()
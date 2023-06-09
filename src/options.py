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

import argparse
import os
from typing import Optional, List

from src.logger import Logger


def parse_args(args=None):
    """
    Parse the command line arguments.
    :return: The parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="A copy of rsync.", prog="mrsync", allow_abbrev=True
    )

    # Source
    parser.add_argument(
        "source",
        type=str,
        action="append",
        help="the source file or directory",
        nargs="*",
        metavar="SOURCE",
    )

    # Destination
    parser.add_argument(
        "destination",
        type=str,
        nargs="?",
        default=None,
        help="the destination file or directory",
        metavar="DESTINATION",
    )

    # Options
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="increase verbosity"
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="suppress non-error messages"
    )
    parser.add_argument(
        "-a",
        "--archive",
        action="store_true",
        help="archive mode; same as -rpt (no -H)",
    )
    parser.add_argument(
        "-r", "--recursive", action="store_true", help="recurse into directories"
    )
    parser.add_argument(
        "-u",
        "--update",
        action="store_true",
        help="skip files that are newer on the receiver",
    )
    parser.add_argument(
        "-d",
        "--dirs",
        action="store_true",
        help="transfer directories without recursing",
    )
    parser.add_argument(
        "-H", "--hard-links", action="store_true", help="preserve hard links"
    )
    parser.add_argument(
        "-p", "--perms", action="store_true", help="preserve permissions"
    )
    parser.add_argument("-t", "--times", action="store_true", help="preserve times")
    parser.add_argument(
        "-z", "--compress", action="store_true", help="compress file data"
    )
    parser.add_argument(
        "--compress-level", type=int, help="specify level of compression"
    )
    parser.add_argument(
        "--existing", action="store_true", help="skip creating new files on receiver"
    )
    parser.add_argument(
        "--ignore-existing",
        action="store_true",
        help="skip updating files that exist on receiver",
    )
    parser.add_argument(
        "--delete", action="store_true", help="delete extraneous files from dest dirs"
    )
    parser.add_argument(
        "--force", action="store_true", help="force deletion of dirs even if not empty"
    )
    parser.add_argument("--timeout", type=int, help="set I/O timeout in seconds")
    parser.add_argument(
        "--blocking-io",
        action="store_true",
        help="use blocking I/O for the remote shell",
    )
    parser.add_argument(
        "-I",
        "--ignore-times",
        action="store_true",
        help="don't skip files that match size and time",
    )
    parser.add_argument(
        "--size-only", action="store_true", help="skip files that match in size"
    )
    parser.add_argument(
        "--address", type=str, help="bind address for outgoing socket to daemon"
    )
    parser.add_argument(
        "--port", type=int, help="specify double-colon alternate port number"
    )
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="list the files instead of copying them",
    )
    parser.add_argument(
        "--whole-file",
        action="store_true",
        help="copy files whole (w/o dividing them into blocks)",
    )
    parser.add_argument(
        "--checksum",
        action="store_true",
        help="skip based on checksum, not mod-time & size",
    )
    parser.add_argument(
        "--server", action="store_true", help="run as the server on remote machine"
    )
    parser.add_argument("--daemon", action="store_true", help="run as a daemon")
    parser.add_argument(
        "--no-detach",
        action="store_true",
        help="don't detach from the controlling terminal",
    )
    parser.add_argument("--version", action="store_true", help="print version number")

    return parser.parse_args(args), parser


def get_args(logger: Logger, program_args: Optional[List[str]] = None):
    """
    Get the arguments and check for errors.
    :param program_args: The program arguments.
    :param logger: The logger.
    :return: The arguments.
    """

    args, parser = parse_args(program_args)

    if args.version:
        print("mrsync 0.1.0")
        print("Written by TriForMine. (https://triformine.dev) and Samsoucoupe")
        exit(0)

    if not args.port:
        args.port = 10873

    if not args.address:
        args.address = "127.0.0.1"

    if args.daemon:
        return args

    if args.source == args.destination:
        logger.error("Source and destination are the same.")
        exit(3)

    if args.destination is None and not args.list_only:
        if len(args.source[0]) > 1:
            args.destination = args.source[0][-1]
            args.source = [args.source[0][:-1]]
        else:
            args.list_only = True

    if len(args.source) == 0 or len(args.source[0]) == 0:
        parser.print_help()
        exit(1)

    if args.destination and not args.destination.endswith("/"):
        # If the destination is a directory, add a trailing slash.
        if os.path.exists(args.destination) and os.path.isdir(args.destination):
            args.destination += "/"

    if args.compress_level is None:
        args.compress_level = 9

    if args.compress_level < 1 or args.compress_level > 9:
        logger.error("Invalid compression level.")
        exit(2)

    if args.archive:
        args.recursive = True
        args.times = True
        args.perms = True

    if args.recursive:
        args.dirs = True

    if args.update:
        args.ignore_existing = True

    if args.ignore_existing:
        args.update = True

    if args.delete:
        if not args.dirs and not args.recursive:
            logger.error("Delete is only allowed if either -r or -d is specified.")
            exit(2)

    if args.force:
        args.delete = True

    if args.blocking_io:
        args.timeout = 0

    if args.timeout == 0:
        args.blocking_io = True

    if args.list_only:
        args.dirs = True

    return args

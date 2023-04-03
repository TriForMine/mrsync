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

from logger import Logger


def parse_args():
    parser = argparse.ArgumentParser(description="A copy of rsync.")

    # Source
    parser.add_argument("source", type=str, action='append', help="the source file or directory", nargs='+')

    # Destination
    parser.add_argument("destination", type=str, help="the destination file or directory")

    # Options
    parser.add_argument("-v", "--verbose", action="store_true", help="increase verbosity")
    parser.add_argument("-q", "--quiet", action="store_true", help="suppress non-error messages")
    parser.add_argument("-a", "--archive", action="store_true", help="archive mode; same as -rpt (no -H)")
    parser.add_argument("-r", "--recursive", action="store_true", help="recurse into directories")
    parser.add_argument("-u", "--update", action="store_true", help="skip files that are newer on the receiver")
    parser.add_argument("-d", "--dirs", action="store_true", help="transfer directories without recursing")
    parser.add_argument("-H", "--hard-links", action="store_true", help="preserve hard links")
    parser.add_argument("-p", "--perms", action="store_true", help="preserve permissions")
    parser.add_argument("-t", "--times", action="store_true", help="preserve times")
    parser.add_argument("--existing", action="store_true", help="skip creating new files on receiver")
    parser.add_argument("--ignore-existing", action="store_true", help="skip updating files that exist on receiver")
    parser.add_argument("--delete", action="store_true", help="delete extraneous files from dest dirs")
    parser.add_argument("--force", action="store_true", help="force deletion of dirs even if not empty")
    parser.add_argument("--timeout", type=int, help="set I/O timeout in seconds")
    parser.add_argument("--blocking-io", action="store_true", help="use blocking I/O for the remote shell")
    parser.add_argument("-I", "--ignore-times", action="store_true", help="don't skip files that match size and time")
    parser.add_argument("--size-only", action="store_true", help="skip files that match in size")
    parser.add_argument("--address", type=str, help="bind address for outgoing socket to daemon")
    parser.add_argument("--port", type=int, help="specify double-colon alternate port number")
    parser.add_argument("--list-only", action="store_true", help="list the files instead of copying them")

    return parser.parse_args()


def get_args(logger: Logger):
    args = parse_args()

    if args.source == args.destination:
        logger.error("Source and destination are the same.")
        exit(3)

    if len(args.source) == 0:
        logger.error("No source specified.")
        exit(3)

    if args.destination is None:
        logger.error("No destination specified.")
        exit(3)

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
        args.force = True

    if args.force:
        args.delete = True

    if args.blocking_io:
        args.timeout = 0

    if args.timeout == 0:
        args.blocking_io = True

    if args.list_only:
        args.update = True
        args.ignore_existing = True
        args.delete = True
        args.force = True

    return args

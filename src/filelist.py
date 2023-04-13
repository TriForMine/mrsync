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
from enum import Enum
from time import strftime, localtime
from typing import List, Optional

from adler32 import Adler32


# Enum bitfield for info to include in file list.

class FileType(Enum):
    FILE = 0
    DIRECTORY = 1

    def __str__(self):
        return self.name.title()


class FileListInfo(Enum):
    NONE = 0
    HARD_LINKS = 1
    PERMISSIONS = 2
    FILE_SIZE = 4
    FILE_TIMES = 8
    CHECKSUM = 16

    def __str__(self):
        return self.name.replace('_', ' ').title()


def generate_info(path, options, source, is_self=False, rel=None):
    file_type = FileType.FILE if os.path.isfile(path) else FileType.DIRECTORY

    if is_self:
        info_path = ''
    elif rel:
        info_path = os.path.relpath(path, rel)
    else:
        info_path = os.path.basename(path)

    info = {'type': file_type.value, 'path': info_path, 'source': source}

    if options & FileListInfo.HARD_LINKS.value:
        info['hard_links'] = os.stat(path).st_nlink
    if options & FileListInfo.PERMISSIONS.value:
        info['permissions'] = oct(os.stat(path).st_mode)[-3:]
    if options & FileListInfo.FILE_SIZE.value:
        info['size'] = os.stat(path).st_size
    if options & FileListInfo.FILE_TIMES.value:
        info['atime'] = int(os.stat(path).st_atime)
        info['mtime'] = int(os.stat(path).st_mtime)
        info['ctime'] = int(os.stat(path).st_ctime)

    if file_type.value == FileType.FILE.value:
        if options & FileListInfo.CHECKSUM.value:
            with open(path, 'rb') as f:
                info['checksum'] = Adler32(f.read()).checksum

    return info


def generate_file_list(sources: List[str], logger,
                       options: int = FileListInfo.NONE.value,
                       recursive: Optional[bool] = False,
                       directory: Optional[bool] = False) -> List[dict]:
    # Returns a list of dictionaries containing file info.

    logger.debug("Generating file list...")
    file_list = []

    def recursive_dir(path):
        for root, dirs, files in os.walk(path, followlinks=True):
            for file in files:
                file_path = os.path.join(root, file)
                file_list.append(generate_info(file_path, options, i, rel=path))
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                file_list.append(generate_info(dir_path, options, i, rel=path))

            if not recursive:
                break

    for i in range(len(sources)):
        source = sources[i]
        if directory:
            if not source.endswith(os.sep):
                if os.path.isdir(source):
                    file_list.append(generate_info(source, options, i, True))
                elif os.path.isfile(source):
                    file_list.append(generate_info(source, options, i, True))
            else:
                recursive_dir(source)
        elif os.path.isfile(source):
            file_list.append(generate_info(source, options, i, True))

    logger.debug("File list generated.")
    return file_list


def humanize_size(size: int):
    if size < 1024:
        size = f"{size}B"
    elif size < 1024 * 1024:
        size = f"{size / 1024:.1f}K"
    elif size < 1024 * 1024 * 1024:
        size = f"{size / 1024 / 1024:.1f}M"
    else:
        size = f"{size / 1024 / 1024 / 1024:.1f}G"

    return size


def print_file_list(sources: List[str], logger, recursive: Optional[bool] = False,
                    directory: Optional[bool] = False):
    file_list = generate_file_list(sources, logger, recursive=recursive, directory=directory,
                                   options=FileListInfo.PERMISSIONS.value | FileListInfo.FILE_SIZE.value | FileListInfo.FILE_TIMES.value)

    # Calculate max length of size to align columns
    max_size_length = 0
    for file in file_list:
        size = humanize_size(file['size'])
        if len(size) > max_size_length:
            max_size_length = len(size)

    # Print like ls -l
    for file in file_list:
        # Generate permission string from permission int
        permission_string = ""
        for i in range(3):
            permission_string += "r" if int(file['permissions'][i]) & 4 else "-"
            permission_string += "w" if int(file['permissions'][i]) & 2 else "-"
            permission_string += "x" if int(file['permissions'][i]) & 1 else "-"

        if file['type'] == FileType.DIRECTORY.value:
            permission_string = "d" + permission_string
        elif file['type'] == FileType.FILE.value:
            permission_string = "-" + permission_string

        size = humanize_size(file['size'])

        time = file['mtime']
        time = strftime("%b %d %H:%M", localtime(time))

        # Make so evertyhing is aligned
        size = size.rjust(max_size_length)

        full_path = file['path'] if file['path'] != "" else os.path.basename(sources[file['source']])

        logger.log(
            f"{permission_string} {size} {time} {full_path}")

    logger.log(f"Total files: {len(file_list)}")

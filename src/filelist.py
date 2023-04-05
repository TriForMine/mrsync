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

    def __str__(self):
        return self.name.replace('_', ' ').title()


def generate_file_list(sources: List[str], logger,
                       options: int = FileListInfo.NONE.value,
                       recursive: Optional[bool] = False,
                       directory: Optional[bool] = False) -> List[dict]:
    # Returns a list of dictionaries containing file info.

    logger.debug("Generating file list...")
    file_list = []
    for i in range(len(sources)):
        source = sources[i]
        if directory:
            for root, dirs, files in os.walk(source, followlinks=True):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_info = {'type': FileType.FILE.value, 'source': i, 'path': os.path.relpath(file_path, source)}
                    if options & FileListInfo.HARD_LINKS.value:
                        file_info['hard_links'] = os.stat(file_path).st_nlink
                    if options & FileListInfo.PERMISSIONS.value:
                        file_info['permissions'] = oct(os.stat(file_path).st_mode)[-3:]
                    if options & FileListInfo.FILE_SIZE.value:
                        file_info['size'] = os.stat(file_path).st_size
                    if options & FileListInfo.FILE_TIMES.value:
                        file_info['atime'] = os.stat(file_path).st_atime
                        file_info['mtime'] = os.stat(file_path).st_mtime
                        file_info['ctime'] = os.stat(file_path).st_ctime
                    file_list.append(file_info)
                for dir in dirs:
                    dir_path = os.path.join(root, dir)
                    dir_info = {'type': FileType.DIRECTORY.value, 'source': i,
                                'path': os.path.relpath(dir_path, source)}
                    if options & FileListInfo.HARD_LINKS.value:
                        dir_info['hard_links'] = os.stat(dir_path).st_nlink
                    if options & FileListInfo.PERMISSIONS.value:
                        dir_info['permissions'] = oct(os.stat(dir_path).st_mode)[-3:]
                    if options & FileListInfo.FILE_SIZE.value:
                        dir_info['size'] = os.stat(dir_path).st_size
                    if options & FileListInfo.FILE_TIMES.value:
                        dir_info['atime'] = os.stat(dir_path).st_atime
                        dir_info['mtime'] = os.stat(dir_path).st_mtime
                        dir_info['ctime'] = os.stat(dir_path).st_ctime
                    file_list.append(dir_info)

                if not recursive:
                    break
        else:
            file_info = {'type': FileType.FILE.value, 'source': i, 'path': os.path.basename(source)}
            if options & FileListInfo.HARD_LINKS.value:
                file_info['hard_links'] = os.stat(source).st_nlink
            if options & FileListInfo.PERMISSIONS.value:
                file_info['permissions'] = oct(os.stat(source).st_mode)[-3:]
            if options & FileListInfo.FILE_SIZE.value:
                file_info['size'] = os.stat(source).st_size
            if options & FileListInfo.FILE_TIMES.value:
                file_info['atime'] = os.stat(source).st_atime
                file_info['mtime'] = os.stat(source).st_mtime
                file_info['ctime'] = os.stat(source).st_ctime
            file_list.append(file_info)

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

        logger.log(
            f"{permission_string} {size} {time} {file['path']}")

    logger.log(f"Total files: {len(file_list)}")

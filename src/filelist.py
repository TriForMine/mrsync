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
from typing import List, Optional


def generate_file_list(sources: List[str], logger, recursive: Optional[bool] = False) -> List[str]:
    # Returns the list of files with their absolute paths relative to the source directory.

    logger.debug("Generating file list...")
    file_list = []
    for source in sources:
        for root, dirs, files in os.walk(source, followlinks=True):
            for file in files:
                file_path = os.path.join(root, file)
                file_list.append(os.path.relpath(file_path, source))
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                file_list.append(os.path.relpath(dir_path, source))

            if not recursive:
                break

    logger.debug("File list generated.")
    return file_list

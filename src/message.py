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

import cbor2


# Message tags
class MESSAGE_TAG(Enum):
    # Ask for file list
    ASK_FILE_LIST = 0
    # File list
    FILE_LIST = 1
    # Ask for file data
    ASK_FILE_DATA = 2
    # File data
    FILE_DATA = 3
    # File data end
    FILE_DATA_END = 4
    # End of transmission
    END = 5
    # Generator finished
    GENERATOR_FINISHED = 6


def send(fd: int, tag: MESSAGE_TAG, v: object) -> None:
    cbor_data = cbor2.dumps((tag.value, v))
    # Send message size first
    size = len(cbor_data).to_bytes(4, byteorder='big')
    os.write(fd, size)
    # Send message data
    response = os.write(fd, cbor_data)
    if response != len(cbor_data):
        raise Exception(f'Error while sending message {tag} to {fd}')


def recv(fd: int) -> (int, object):
    # Read message size first
    size_bytes = os.read(fd, 4)
    if len(size_bytes) != 4:
        return MESSAGE_TAG.END, None
    size = int.from_bytes(size_bytes, byteorder='big')
    # Read message data
    data = os.read(fd, size)
    tag, v = cbor2.loads(data)
    return MESSAGE_TAG(tag), v

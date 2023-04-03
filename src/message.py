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

MAX_SIZE = 1024 * 63


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
    # Delete files
    DELETE_FILES = 7


def send(fd: int, tag: MESSAGE_TAG, v: object) -> None:
    if tag == MESSAGE_TAG.FILE_DATA:
        (filename, data) = v
    else:
        data = cbor2.dumps(v)

    amount_of_packets = len(data) // MAX_SIZE + 1

    # Send total amount of packets
    size = amount_of_packets.to_bytes(4, byteorder='big')
    os.write(fd, size)

    # Send message tag
    size = tag.value.to_bytes(4, byteorder='big')
    os.write(fd, size)

    print(f'Sending {amount_of_packets} packets with tag {tag} ({tag.name})')

    if tag == MESSAGE_TAG.FILE_DATA:
        filename_data = filename.encode('utf-8')

        # Send size of filename
        size = len(filename_data).to_bytes(4, byteorder='big')
        os.write(fd, size)

        # Send filename
        os.write(fd, filename_data)

        print(f'Sending filename {filename}')

    for i in range(amount_of_packets):
        slice = data[i * MAX_SIZE:(i + 1) * MAX_SIZE]

        # Send current packet number
        size = i.to_bytes(4, byteorder='big')
        os.write(fd, size)

        # Send message size first
        size = len(slice).to_bytes(4, byteorder='big')
        os.write(fd, size)

        # Send message data
        response = os.write(fd, slice)
        if response != len(slice):
            raise Exception(f'Error while sending message {tag} to {fd}')


def recv(fd: int) -> (int, object):
    filename = ''

    # Receive total amount of packets
    size = os.read(fd, 4)
    amount_of_packets = int.from_bytes(size, byteorder='big')

    # Receive message tag
    size = os.read(fd, 4)
    tag = MESSAGE_TAG(int.from_bytes(size, byteorder='big'))

    print(f'Receiving {amount_of_packets} packets with tag {tag} ({tag.name})')

    if tag == MESSAGE_TAG.FILE_DATA:
        # Receive size of filename
        size = os.read(fd, 4)
        filename_size = int.from_bytes(size, byteorder='big')

        # Receive filename
        filename = os.read(fd, filename_size)
        filename = filename.decode('utf-8')

    current_packet = 0
    total_data = b''

    if amount_of_packets == 0:
        return tag, None

    while current_packet < amount_of_packets:
        # Receive current packet number
        size = os.read(fd, 4)
        current_packet = int.from_bytes(size, byteorder='big')

        # Receive message size first
        size = os.read(fd, 4)
        message_size = int.from_bytes(size, byteorder='big')

        # Receive message data
        data = os.read(fd, message_size)

        if len(data) != message_size:
            raise Exception(f'Error while receiving message from {fd}')

        total_data += data
        current_packet += 1

    if tag == MESSAGE_TAG.FILE_DATA:
        print(f'File {filename} received ({len(total_data)} bytes)')
        return tag, (filename, total_data)

    return tag, cbor2.loads(total_data)

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
import signal
import time
from enum import Enum
from typing import Optional

import cbor2

from logger import Logger

MAX_SIZE = 1024 * 63


# Message tags
class MESSAGE_TAG(Enum):
    # Ask for file list
    ASK_FILE_LIST = 1
    # File list
    FILE_LIST = 2
    # Ask for file data
    ASK_FILE_DATA = 3
    # File data
    FILE_DATA = 4
    # File data end
    FILE_DATA_END = 5
    # File data offset
    FILE_DATA_OFFSET = 6
    # End of transmission
    END = 7
    # Generator finished
    GENERATOR_FINISHED = 8
    # Delete files
    DELETE_FILES = 9

    def __str__(self):
        return self.name.replace('_', ' ').title()


def _timeout_handler(_signum, _frame):
    raise TimeoutError("Timeout reached.")


def send(fd: int, tag: MESSAGE_TAG, v: object, timeout: Optional[int] = None, logger: Optional[Logger] = None) -> None:
    # Use signal.alarm for timeout
    if timeout is not None:
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(timeout)

    try:
        if tag == MESSAGE_TAG.FILE_DATA:
            (filename, start, end, data) = v
        else:
            data = cbor2.dumps(v)

        amount_of_packets = len(data) // MAX_SIZE + 1
        bytes_sent = 0
        start_time = time.monotonic()

        # Send total amount of packets
        size = amount_of_packets.to_bytes(4, byteorder='big')
        os.write(fd, size)

        # Send message tag
        size = tag.value.to_bytes(4, byteorder='big')
        os.write(fd, size)

        if tag == MESSAGE_TAG.FILE_DATA:
            filename_data = filename.encode('utf-8')

            # Send size of filename
            size = len(filename_data).to_bytes(4, byteorder='big')
            os.write(fd, size)

            # Send filename
            os.write(fd, filename_data)

            # Send start byte
            size = start.to_bytes(4, byteorder='big')
            os.write(fd, size)

            # Send end byte
            size = end.to_bytes(4, byteorder='big')
            os.write(fd, size)

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
            bytes_sent += response
            if response != len(slice):
                raise Exception(f'Error while sending message {tag} to {fd}')

        # Calculate time taken to send the current packet
        current_time = time.monotonic()
        time_taken = current_time - start_time

        average_speed = bytes_sent / time_taken

        # Convert to MB/s
        average_speed /= 1024 * 1024
        # Round to 2 decimal places
        average_speed = round(average_speed, 2)

        time_taken = round(time_taken, 2)

        # Convert to MB
        bytes_sent /= 1024 * 1024
        bytes_sent = round(bytes_sent, 2)

        if logger is not None:
            logger.debug(
                f'Sent {tag} to {fd} in {time_taken} seconds at {average_speed} MB/s ({bytes_sent} MB)')

    except TimeoutError:
        if logger is not None:
            logger.error(f'Timeout reached while sending message {tag} ')
    finally:
        signal.alarm(0)


def recv(fd: int, timeout: Optional[int] = None) -> (int, object):
    filename = ''
    start_byte = 0
    end_byte = 0

    # Use signal.alarm for timeout
    if timeout is not None:
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(timeout)

    try:
        # Receive total amount of packets
        size = os.read(fd, 4)
        if not size:
            return MESSAGE_TAG.END, None
        amount_of_packets = int.from_bytes(size, byteorder='big')

        # Receive message tag
        size = os.read(fd, 4)
        if not size:
            return MESSAGE_TAG.END, None
        tag = int.from_bytes(size, byteorder='big')

        if tag == 0:
            raise Exception(f'Invalid tag received: {tag}')

        tag = MESSAGE_TAG(tag)

        if amount_of_packets == 0:
            return tag, None

        if tag == MESSAGE_TAG.FILE_DATA:
            # Receive size of filename
            size = os.read(fd, 4)
            if not size:
                return MESSAGE_TAG.END, None
            filename_size = int.from_bytes(size, byteorder='big')

            # Receive filename
            filename = os.read(fd, filename_size)
            if not size:
                return MESSAGE_TAG.END, None
            filename = filename.decode('utf-8')

            # Receive start byte
            size = os.read(fd, 4)
            if not size:
                return MESSAGE_TAG.END, None
            start_byte = int.from_bytes(size, byteorder='big')

            # Receive end byte
            size = os.read(fd, 4)
            if not size:
                return MESSAGE_TAG.END, None
            end_byte = int.from_bytes(size, byteorder='big')

        current_packet = 0
        total_data = b''

        while current_packet < amount_of_packets:
            # Receive current packet number
            size = os.read(fd, 4)
            if not size:
                return MESSAGE_TAG.END, None
            current_packet = int.from_bytes(size, byteorder='big')

            # Receive message size first
            size = os.read(fd, 4)
            if not size:
                return MESSAGE_TAG.END, None
            message_size = int.from_bytes(size, byteorder='big')

            # Receive message data
            data = os.read(fd, message_size)
            if not data and message_size != 0:
                return MESSAGE_TAG.END, None

            if len(data) != message_size:
                raise Exception(f'Error while receiving message from {fd}')

            total_data += data
            current_packet += 1

        if tag == MESSAGE_TAG.FILE_DATA:
            return tag, (filename, start_byte, end_byte, total_data)

        return tag, cbor2.loads(total_data)
    except TimeoutError:
        print(f'Timeout reached while receiving message')
    finally:
        signal.alarm(0)

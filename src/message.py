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
import socket
import zlib
from enum import Enum
from typing import Optional

import cbor2

from src.logger import Logger

MAX_SIZE = 256


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
    # Server finished
    SERVER_FINISHED = 10
    # Socket Identification (Click or Server)
    SOCKET_IDENTIFICATION = 11
    # Ping
    PING = 12
    # Pong
    PONG = 13

    def __str__(self):
        return self.name.replace('_', ' ').title()

class SOCKET_IDENTIFICATION(Enum):
    CLIENT = 1
    SERVER = 2

    def __str__(self):
        return self.name.replace('_', ' ').title()

def _timeout_handler(_signum, _frame):
    raise TimeoutError("Timeout reached.")

# A class that will be inherited to support both file descriptors and sockets
class MessageMethod:
    def __init__(self):
        self.fd = None

    def send(self, data) -> int:
        raise NotImplementedError

    def recv(self, size):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

class FileDescriptorMethod(MessageMethod):
    def __init__(self, fd):
        super().__init__()
        self.fd = fd

    def send(self, data):
        return os.write(self.fd, data)

    def recv(self, size):
        return os.read(self.fd, size)

    def close(self):
        os.close(self.fd)

    def __str__(self):
        return f"FileDescriptorMethod({self.fd})"

class SocketMethod(MessageMethod):
    def __init__(self, fd: socket.socket):
        super().__init__()
        self.fd = fd

    def send(self, data):
        return self.fd.send(data)

    def recv(self, size):
        return self.fd.recv(size)

    def close(self):
        self.fd.close()

    def __str__(self):
        return f"SocketMethod({self.fd})"

def send(fd: MessageMethod, tag: MESSAGE_TAG, v: object, timeout: Optional[int] = None, logger: Optional[Logger] = None, compress_file: bool = False, compress_level: int = 9) -> None:
    """
    Send a message to a file descriptor
    :param compress_file: Whether to compress the file or not
    :param fd: The file descriptor
    :param tag: The message tag
    :param v: The message data
    :param timeout: The timeout in seconds
    :param logger: The logger
    :return:
    """

    # Use signal.alarm for timeout
    if timeout is not None:
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(timeout)

    try:
        if tag == MESSAGE_TAG.FILE_DATA:
            (filename, file_info, start, end, whole_file, data) = v
            if compress_file:
                data = zlib.compress(data, compress_level)
        elif tag == MESSAGE_TAG.SOCKET_IDENTIFICATION:
            if v == SOCKET_IDENTIFICATION.CLIENT:
                data = (1).to_bytes(4, byteorder='big')
            elif v == SOCKET_IDENTIFICATION.SERVER:
                data = (2).to_bytes(4, byteorder='big')
        else:
            data = cbor2.dumps(v)

        amount_of_packets = len(data) // MAX_SIZE + 1
        bytes_sent = 0
        start_time = time.monotonic()

        # Send total amount of packets
        size = amount_of_packets.to_bytes(4, byteorder='big')
        fd.send(size)

        # Send message tag
        size = tag.value.to_bytes(4, byteorder='big')
        fd.send(size)

        if tag == MESSAGE_TAG.FILE_DATA:
            filename_data = filename.encode('utf-8')

            # Send size of filename
            size = len(filename_data).to_bytes(4, byteorder='big')
            fd.send(size)

            # Send filename
            fd.send(filename_data)

            # Encode file info
            encoded_file_info = cbor2.dumps(file_info)

            # Send file info size
            size = len(encoded_file_info).to_bytes(4, byteorder='big')
            fd.send(size)

            # Send file info
            fd.send(encoded_file_info)

            # Send start byte
            size = start.to_bytes(4, byteorder='big')
            fd.send(size)

            # Send end byte
            size = end.to_bytes(4, byteorder='big')
            fd.send(size)

            # Send whole file
            size = whole_file.to_bytes(1, byteorder='big')
            fd.send(size)

        for i in range(amount_of_packets):
            slice = data[i * MAX_SIZE:(i + 1) * MAX_SIZE]

            # Send current packet number
            size = i.to_bytes(4, byteorder='big')
            fd.send(size)

            # Send message size first
            size = len(slice).to_bytes(4, byteorder='big')
            fd.send(size)

            # Send message data
            response = fd.send(slice)
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
        exit(30)
    finally:
        signal.alarm(0)


def recv(fd: MessageMethod, timeout: Optional[int] = None, compress_file: bool = False) -> (int, object):
    """
    Receive a message from a file descriptor
    :param compress_file: Whether to compress the file or not
    :param fd: The file descriptor
    :param timeout: The timeout in seconds
    :return: The message tag and the message data
    """

    filename = ''
    source = 0
    start_byte = 0
    end_byte = 0
    whole_file = False
    file_info = None

    # Use signal.alarm for timeout
    if timeout is not None:
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(timeout)

    try:
        # Receive total amount of packets
        size = fd.recv(4)
        if not size:
            return MESSAGE_TAG.END, None
        amount_of_packets = int.from_bytes(size, byteorder='big')

        # Receive message tag
        size = fd.recv(4)
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
            size = fd.recv(4)
            if not size:
                return MESSAGE_TAG.END, None
            filename_size = int.from_bytes(size, byteorder='big')

            # Receive filename
            filename = fd.recv(filename_size)
            if not size:
                return MESSAGE_TAG.END, None
            filename = filename.decode('utf-8')

            # Receive file info size
            size = fd.recv(4)
            if not size:
                return MESSAGE_TAG.END, None
            file_info_size = int.from_bytes(size, byteorder='big')

            # Receive file info
            file_info = fd.recv(file_info_size)
            if not size:
                return MESSAGE_TAG.END, None
            file_info = cbor2.loads(file_info)

            # Receive start byte
            size = fd.recv(4)
            if not size:
                return MESSAGE_TAG.END, None
            start_byte = int.from_bytes(size, byteorder='big')

            # Receive end byte
            size = fd.recv(4)
            if not size:
                return MESSAGE_TAG.END, None
            end_byte = int.from_bytes(size, byteorder='big')

            # Receive whole file
            size = fd.recv(1)
            if not size:
                return MESSAGE_TAG.END, None
            whole_file = int.from_bytes(size, byteorder='big')

        current_packet = 0
        total_data = b''

        while current_packet < amount_of_packets:
            # Receive current packet number
            size = fd.recv(4)
            if not size:
                return MESSAGE_TAG.END, None
            current_packet = int.from_bytes(size, byteorder='big')

            # Receive message size first
            size = fd.recv(4)
            if not size:
                return MESSAGE_TAG.END, None
            message_size = int.from_bytes(size, byteorder='big')

            # Receive message data
            data = fd.recv(message_size)
            if not data and message_size != 0:
                return MESSAGE_TAG.END, None

            if len(data) != message_size:
                # Try to receive the rest of the data
                tries = 0
                while len(data) < message_size and tries < 10:
                    data += fd.recv(message_size - len(data))
                    tries += 1

                if len(data) != message_size:
                    exit(23)

            total_data += data
            current_packet += 1

        if tag == MESSAGE_TAG.FILE_DATA:
            if compress_file:
                total_data = zlib.decompress(total_data)
            return tag, (filename, file_info, start_byte, end_byte, whole_file, total_data)

        if tag == MESSAGE_TAG.SOCKET_IDENTIFICATION:
            return tag, SOCKET_IDENTIFICATION(int.from_bytes(total_data, byteorder='big'))

        return tag, cbor2.loads(total_data)
    except TimeoutError:
        exit(30)
    finally:
        signal.alarm(0)

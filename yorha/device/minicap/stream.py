""" Orlov Plugins : Minicap Stream Utility. """
from typing import Union, Optional
import os
import sys
import socket
import logging
import threading
from queue import Queue

PATH = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if PATH not in sys.path:
    sys.path.insert(0, PATH)

MAX_SIZE = 5
logger = logging.getLogger(__name__)


def bytes_to_int(byte_data: Union[int, bytes]) -> int:
    """ bytes_to_int utility.
    """
    if isinstance(byte_data, (int)):
        return byte_data
    else:
        return int.from_bytes(byte_data, 'big')


class Banner:
    """ Minicap DataSet Object.
    """

    def __init__(self) -> None:
        self.version = 0
        self.length = 0
        self.pid = 0
        self.real_width = 0
        self.real_height = 0
        self.virtual_width = 0
        self.virtual_height = 0
        self.orientation = 0
        self.quirks = 0

    def __str__(self) -> str:
        return 'Banner [ Version = ' + str(self.version) + \
                      ', Length = ' + str(self.length) + \
                      ', PID = ' + str(self.pid) + \
                      ', RealWidth = ' + str(self.real_width) + \
                      ', RealHeight = ' + str(self.real_height) + \
                      ', VirthalWidth = ' + str(self.virtual_width) + \
                      ', VirthalHeight = ' + str(self.virtual_height) + \
                      ', Orientation = ' + str(self.orientation) + \
                      ', Quirks = ' + str(self.quirks) + ' ]'


class MinicapStream:
    """ Minicap Stream Utility

    Attributes:
        ip(str): server ip address.
        port(str): server port.
    """
    __instance = None
    __mutex = threading.Lock()

    def __init__(self, ip: str, port: str) -> None:
        self.IP = ip
        self.PORT = int(port)
        self.PID = 0
        self.banner = Banner()
        self.minicap_socket: Optional[socket.socket] = None
        self.read_image_stream_task = None

        self.push = None
        self.picture: Queue[bytearray] = Queue()
        self.__flag = True

    @staticmethod
    def get_builder(ip: str = '127.0.0.1', port: str = '1313') -> 'MinicapStream':
        """ get stream builder.

        Arguments:
            ip(str): server ip address.
            port(str): server port.

        Returns:
            target(MinicapStream): MinicapStream instance.
        """
        if MinicapStream.__instance is None:
            MinicapStream.__mutex.acquire()
            if MinicapStream.__instance is None:
                MinicapStream.__instance = MinicapStream(ip, port)
            MinicapStream.__mutex.release()
        return MinicapStream.__instance

    def get_ip(self) -> str:
        """ get IP Address.
        Returns:
            ip(str): server ip address.
        """
        return self.IP

    def get_port(self) -> int:
        """ get Port.
        Returns:
            port(str): server port.
        """
        return self.PORT

    def get_queue(self) -> Queue[bytearray]:
        """ get picture queue object.
        Returns:
            queue(Queue): picture queue.
        """
        return self.picture

    def get_d(self) -> int:
        """ get picture queue size.
        Returns:
            size(int): picture queue size.
        """
        return self.picture.qsize()

    def start(self) -> None:
        """ start Minicap Stream.
        """
        self.minicap_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.minicap_socket.connect((self.IP, self.PORT))
        threading.Thread(target=self.read_image_stream).start()

    def finish(self) -> None:
        """ call stop Minicap Stream.
        """
        self.__flag = False

    def read_image_stream(self) -> None:
        """ read Image Stream.
        """
        read_banner_bytes = 0
        banner_length = 2
        read_frame_bytes = 0
        frame_body_length = 0
        data_body = bytearray(b'')
        counter = 0

        while self.__flag:
            # logger.info('Picture Queue : %s' % (self.get_d()))
            if self.minicap_socket is None:
                return
            reallen = self.minicap_socket.recv(4096)
            length = len(reallen)
            if not length:
                continue
            cursor = 0
            while cursor < length:
                if read_banner_bytes < banner_length:
                    if not read_banner_bytes:
                        self.banner.version = bytes_to_int(reallen[cursor])
                    elif read_banner_bytes == 1:
                        banner_length = bytes_to_int(reallen[cursor])
                        self.banner.length = banner_length
                    elif read_banner_bytes in [2, 3, 4, 5]:
                        self.banner.pid += (bytes_to_int(reallen[cursor]) << ((read_banner_bytes - 2) * 8)) >> 0
                    elif read_banner_bytes in [6, 7, 8, 9]:
                        self.banner.real_width += (bytes_to_int(reallen[cursor]) << ((read_banner_bytes - 6) * 8)) >> 0
                    elif read_banner_bytes in [10, 11, 12, 13]:
                        self.banner.real_height += (bytes_to_int(reallen[cursor]) <<
                                                    ((read_banner_bytes - 10) * 8)) >> 0
                    elif read_banner_bytes in [14, 15, 16, 17]:
                        self.banner.virtual_width += (bytes_to_int(reallen[cursor]) <<
                                                      ((read_banner_bytes - 14) * 8)) >> 0
                    elif read_banner_bytes in [18, 19, 20, 21]:
                        self.banner.virtual_height += (bytes_to_int(reallen[cursor]) <<
                                                       ((read_banner_bytes - 18) * 8)) >> 0
                    elif read_banner_bytes == 22:
                        self.banner.orientation = bytes_to_int(reallen[cursor]) * 90
                    elif read_banner_bytes == 23:
                        self.banner.quirks = bytes_to_int(reallen[cursor])
                    cursor += 1
                    read_banner_bytes += 1
                    if read_banner_bytes == banner_length:
                        logger.debug(self.banner)
                elif read_frame_bytes < 4:
                    frame_body_length = frame_body_length + ((bytes_to_int(reallen[cursor]) <<
                                                              (read_frame_bytes * 8)) >> 0)
                    cursor += 1
                    read_frame_bytes += 1
                else:
                    if length - cursor >= frame_body_length:
                        data_body = data_body + reallen[cursor:(cursor + frame_body_length)]
                        if bytes_to_int(data_body[0]) != 0xFF or bytes_to_int(data_body[1]) != 0xD8:
                            return
                        self.picture.put(data_body)
                        if self.get_d() > MAX_SIZE:
                            self.picture.get()
                        cursor += frame_body_length
                        frame_body_length = 0
                        read_frame_bytes = 0
                        data_body = bytearray(b'')
                        counter += 1
                    else:
                        data_body = data_body + reallen[cursor:length]
                        frame_body_length -= length - cursor
                        read_frame_bytes += length - cursor
                        cursor = length

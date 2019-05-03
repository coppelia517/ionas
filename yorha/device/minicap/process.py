"""  Orlov Plugins : Minicap Process Utility. """
from typing import Tuple, Dict, Any, Optional
import os
import io
import sys
import time
import logging
import threading
from queue import Queue

import cv2
from PIL import Image
import numpy as np
import fasteners

from .service import MinicapService
from .stream import MinicapStream

from ..adb import Android
from ...workspace import Workspace

PATH = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PATH not in sys.path:
    sys.path.insert(0, PATH)

MAX_SIZE = 5
logger = logging.getLogger(__name__)


class SearchObject:
    """ Search Object.
    Attributes:
        function(str): target get function.
        target(str): target image filepath.
        box(tuple): target position(x, y)
    """

    def __init__(self, _function: str, _target: str, _box: Optional[Tuple[int, int]]) -> None:
        self.func = _function
        self.target = _target
        self.box = _box

    def __repr__(self) -> str:
        return 'SearchObject()'

    def __str__(self) -> str:
        return 'Target, Box : %s, %s' % (os.path.basename(self.target), self.box)


# pylint: disable=E1101
class MinicapProc:
    """ Minicap Process
    Attributes:
        stream(MinicapStream): Minicap Stream Object.
        service(MinicapService): Minicap Service Object.
        debug(bool): Debug flag.
    """

    def __init__(self, _stream: MinicapStream, _service: MinicapService, debug: bool = False) -> None:
        self.module: Dict[str, Any] = {}
        self.module['stream'] = _stream
        self.module['service'] = _service

        self.space: Dict[str, str] = {}

        self.output: Queue[bytearray] = Queue()
        self._loop_flag = True
        self._debug = debug

        self._search: Optional[SearchObject] = None
        self.search_result: Queue[str] = Queue()
        self.counter = 1
        self.lock = fasteners.InterProcessLock('.lockfile')

    def start(self, _adb: Android, _workspace: Workspace, _package: Optional[str] = None) -> None:
        """ Minicap Process Start.
        Arguments:
            _adb(Android): android adaptor object.
            _workspace(Workspace): workspace adaptor object.
                - log : workspace.log
                - tmp : workspace.tmp
                - evidence : workspace.tmp.evidence
                - reference : workspace.tmp.reference
            _package(str): package name. default: None.
        """
        self.module['adb'] = _adb
        self.module['workspace'] = _workspace

        self.module['workspace'].mkdir('tmp')
        self.space['log'] = self.module['workspace'].mkdir('log')

        if _package is None:
            self.space['tmp'] = self.module['workspace'].mkdir('tmp')
            self.space['tmp.evidence'] = self.module['workspace'].mkdir('tmp\\evidence')
            self.space['tmp.reference'] = self.module['workspace'].mkdir('tmp\\reference')
            self.space['tmp.video'] = self.module['workspace'].mkdir('tmp\\video')
        else:
            self.space['tmp'] = self.module['workspace'].mkdir('tmp\\%s' % _package)
            self.space['tmp.evidence'] = self.module['workspace'].mkdir('tmp\\%s\\evidence' % _package)
            self.space['tmp.reference'] = self.module['workspace'].mkdir('tmp\\%s\\reference' % _package)
            self.space['tmp.video'] = self.module['workspace'].mkdir('tmp\\%s\\video' % _package)

        self.module['service'].start(self.module['adb'], self.space['log'])
        time.sleep(1)
        self.module['adb'].forward('tcp:%s localabstract:minicap' % str(self.module['stream'].get_port()))
        self.module['stream'].start()
        threading.Thread(target=self.main_loop).start()

    def finish(self) -> None:
        """ Minicap Process Finish.
        """
        self._loop_flag = False
        time.sleep(1)
        self.module['stream'].finish()
        if 'service' in self.module and self.module['service'] is not None:
            self.module['service'].stop()

    def get_d(self) -> int:
        """ Get output queue size.
        Returns:
            size(int): output queue size.
        """
        return self.output.qsize()

    def get_frame(self) -> bytearray:
        """ Get frame image in output.
        Returns:
            objects(bytearray): image data.
        """
        return self.output.get()

    def __save(self, filename: str, data: bytearray) -> None:
        """ Save framedata in files.
        Arguments:
            filename(str): saved filename.
            data(bytearray): save framedata.
        """
        with open(filename, 'wb') as f:
            f.write(data)
            f.flush()

    def __save_cv(self, filename: str, img_cv: np.ndarray) -> Optional[str]:
        """ Save framedata in files. (opencv)
        Arguments:
            filename(str): saved filename.
            img_cv(numpy.ndarray): framedata(opencv).
        Returns:
            filepath(Optional[str]): filepath
        """
        return filename if cv2.imwrite(filename, img_cv) else None

    def __save_evidence(self, number: float, data: bytearray) -> None:
        """ Save Evidence Data.
        Arguments:
            number(float): counter number.
            data(bytearray): save framedata.
        """
        zpnum = '{0:08d}'.format(int(number))
        if 'tmp.evidence' in self.space:
            self.__save_cv(os.path.join(self.space['tmp.evidence'], 'image_%s.png' % str(zpnum)), data)

    def __search(self, func: str, target: str, box: Optional[Tuple[int, int]] = None,
                 _timeout: int = 5) -> Optional[str]:
        """ Search Object.
        Arguments:
            func(str): function name.
                - capture, patternmatch, ocr.
            target(object): Target Object. only capture, filename.
            box(Optional[Tuple]): box object. (x, y, width, height)
            _timeout(int): Expired Time. default : 5.
        Returns:
            result(Optional[str]): return target.
        """

        with self.lock:
            self._search = SearchObject(func, target, box)
            result = self.search_result.get(timeout=_timeout)
            self._search = None

        return result

    def capture_image(self, filename: str, _timeout: int = 5) -> Optional[str]:
        """ Capture Image File.
        Arguments:
            filename(str): filename.
            _timeout(int): Expired Time. default : 5.
        Returns:
            result(Optional[str]): filename
        """
        return self.__search('capture', filename, box=None, _timeout=_timeout)

    def search_pattern(self, target: str, box: Optional[Tuple[int, int]] = None, _timeout: int = 5) -> Optional[str]:
        """ Search Pattern Match File.
        Arguments:
            target(str): target file path.
            box(tuple): target search box.
            _timeout(int): timeout.
        Returns:
            result(Optional[str]): search pattern point.
        """
        return self.__search('patternmatch', target, box=box, _timeout=_timeout)

    def search_ocr(self, box: Optional[Tuple[int, int]] = None, _timeout: int = 5) -> Optional[str]:
        """ Search OCR File.
        Arguments:
            box(tuple): target search box.
            _timeout(int): timeout.
        Returns:
            result(tuple): search pattern point.
        """
        return self.__search('ocr', 'dummy', box=box, _timeout=_timeout)

    def main_loop(self) -> None:
        """ Minicap Process Main Loop.
        """
        if self._debug:
            cv2.namedWindow('debug')

        while self._loop_flag:
            data = self.module['stream'].picture.get()
            save_flag = False

            image_pil = Image.open(io.BytesIO(data))
            image_cv = cv2.cvtColor(np.asarray(image_pil), cv2.COLOR_RGB2BGR)

            if self._search is not None:
                if self._search.func == 'capture':
                    outputfile = os.path.join(self.space['tmp'], self._search.target)
                    result = self.__save_cv(outputfile, image_cv)
                    if result:
                        self.search_result.put(result)

                elif self._search.func == 'patternmatch':
                    result, image_cv = Picture.search_pattern(image_cv, self._search.target, self._search.box,
                                                              self.space['tmp'])
                    if result:
                        self.search_result.put(result)
                        save_flag = True

                elif self._search.func == 'ocr':
                    result, image_cv = Ocr.img_to_string(image_cv, self._search.box, self.space['tmp'])
                    if result:
                        self.search_result.put(result)
                        save_flag = True
                else:
                    logger.warning('Could not find function : %s', self._search.func)

            if (not self.counter % 5) or save_flag:
                self.__save_evidence(self.counter / 5, image_cv)

            if self._debug:
                if self.module['adb'] is None:
                    resize_image_cv = cv2.resize(image_cv, (640, 360))
                else:
                    h = int(int(self.module['adb'].get().MINICAP_WIDTH) / 2)
                    w = int(int(self.module['adb'].get().MINICAP_HEIGHT) / 2)
                    if not int(self.module['adb'].get().ROTATE):
                        resize_image_cv = cv2.resize(image_cv, (h, w))
                    else:
                        resize_image_cv = cv2.resize(image_cv, (w, h))
                cv2.imshow('debug', resize_image_cv)
                key = cv2.waitKey(5)
                if key == 27:
                    break
            self.counter += 1

        if self._debug:
            cv2.destroyAllWindows()

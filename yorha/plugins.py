""" YoRHa Plugin Module. """
import os
import time
import logging
import pytest

# flake8: noqa
# pylint: disable=no-name-in-module
# pylint: disable=unused-import
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

from yorha.cmd import run

FFMPEG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'binary', 'ffmpeg', 'bin', 'ffmpeg.exe'))
logger = logging.getLogger(__name__)


def pytest_addoption(parser):
    """ add commandline options """
    group = parser.getgroup('yorha')
    group.addoption('--yorha-debug', action='store_true', dest='yorha_debug', default=False, help='debug flag.')

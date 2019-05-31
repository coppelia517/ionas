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


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item):
    """
    Pytest hookwrapper for makereport.
    This hook executes once for each test phase (setup, call, teardown).
    We can store the result of each phase in this hook. This is done so pytest_runtest_teardown hook can read it.
    """
    logger.debug('Setup of pytest_runtest_makereport')
    outcome = yield
    logger.debug('Teardown of pytest_runtest_makereport')
    # outcome.excinfo may be None or a (cls, val, tb) tuple

    res = outcome.get_result()  # will raise if outcome was exception
    # Pass the slaveinfo to report
    res.slaveinput = getattr(item.config, 'slaveinput', None)
    # Store the result of each test phase, so it can be read by pytest_runtest_teardown hook when it runs.
    if not hasattr(item, 'rep_' + res.when):
        setattr(item, 'rep_' + res.when, res)


def pytest_runtest_teardown(item):
    """
    Pytest hook for capturing screenshot on test failure.
    After each test phase execution is done, this hook is called.
    This is run before any other fixtures are called.
    """
    logger.debug('YoRHa Plugins : Begin Pytest Test Run Teardown.')
    if (hasattr(item, 'rep_setup') and item.rep_setup.failed):
        logger.info('YoRHa Plugins : Setup Failed.')

    if (hasattr(item, 'rep_call') and item.rep_call.failed):
        logger.info('YoRHa Plugins : Call Failed.')
        if hasattr(item.cls, 'evidence_dir') and hasattr(item.cls, 'video_dir'):
            filename = 'error_{}_{}.mp4'.format(item.name, time.strftime('%Y_%m_%d_%H_%M_%S'))
            logger.info(os.path.join(item.cls.video_dir, filename))
            create_video(item.cls.evidence_dir, item.cls.video_dir, filename)
            logger.debug('YoRHa Plugins : Screenshot Captured on Test Failure.')
        else:
            logger.debug('YoRHa Plugins : evidence_dir does not exist, screen shot not saved.')


def create_video(src, dst, filename='output.mp4'):
    """ create video.
    """
    output = os.path.join(dst, filename)
    if os.path.exists(output):
        os.remove(output)
    cmd = r'%s -r 3 -i %s -an -vcodec libx264 -pix_fmt yuv420p %s' \
         % (FFMPEG_PATH, os.path.join(src, 'image_%08d.png'), output)
    return run(cmd)

""" Test cmd.py """
import logging
import pytest

from yorha.cmd import run, run_bg
from yorha.exception import RunError

L = logging.getLogger(__name__)


def test_run_bg():
    """ Test run bg """
    run_bg('ls -la')
    assert True


def test_run_bg_debug():
    """ Test run bg debug """
    run_bg('ls -la', debug=True)
    assert True


def test_run():
    """ Test run """
    result = run('ls -la')
    assert not result[0]
    L.info(result[1])


def test_run_debug():
    """ Test run debug """
    result = run('ls -la', debug=True)
    assert not result[0]


def test_run_timeout():
    """ Test run timeout """
    result = run('sleep 2', timeout=5)
    assert not result[0]


def test_run_timeout_exception():
    """ Test run timeout """
    with pytest.raises(RunError):
        result = run('sleep 10', timeout=5)
        assert result[0] == 1

""" YoRHa module : command line utility. """
import sys
import traceback
import subprocess
from subprocess import TimeoutExpired, CalledProcessError

from yorha import STRING_SET
from yorha.exception import RunError

TIMEOUT = 300


def run_bg(cmd, cwd=None, shell=False, debug=False) -> None:
    """ Execute a child program in a new process.

    Arguments:
        cmd(str) : A string of program arguments.
        cwd(str) : Sets the current directory before the child is executed.
        shell(bool) : If true, the command will be executed through the shell.
        debug(bool) : debug mode flag.

    Raises:
        RunError: File not found.
    """
    cmd = _shell(cmd) if shell else cmd
    _debug(cmd, debug)
    try:
        subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell)
    except CalledProcessError:
        out = '{0}: {1}\n{2}'.format(CalledProcessError.__name__, ''.join(cmd), traceback.format_exc())
        raise RunError(cmd, None, message='Raise CalledProcess Error : %s' % out)


def run(cmd, cwd=None, timeout=TIMEOUT, shell=False, debug=False) -> tuple or None:
    """ Execute a child program in a new process.

    Arguments:
        cmd(str): A string of program arguments.
        cwd(str): Sets the current directory before the child is executed.
        timeout(int): Expired Time. default : 300.
        shell(bool): If true, the command will be executed through the shell.
        debug(bool): debug mode flag.

    Raises:
        RunError: File not found.
        TimeoutError: command execution timeout.

    Returns:
        returncode(int): status code.
        out(str): Standard out.
        err(str): Standard error.
    """
    cmd = _shell(cmd) if shell else cmd
    _debug(cmd, debug)
    try:
        proc = subprocess.run(
            cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, timeout=timeout, shell=shell)
        proc.check_returncode()
        out = proc.stdout
        err = proc.stderr
        returncode = proc.returncode
        try:
            if isinstance(out, bytes):
                out = str(out.decode('utf8'))
            if isinstance(err, bytes):
                err = str(err.decode('utf8'))
        except UnicodeDecodeError:
            output = '{0}: {1}\n{2}'.format(UnicodeDecodeError.__name__, ''.join(cmd), traceback.format_exc())
            raise RunError(cmd, None, message='Raise UnicodeDecodeError : %s' % output)
        return (returncode, out, err)
    except TimeoutExpired:
        out = '{0}: {1}\n{2}'.format(TimeoutExpired.__name__, ''.join(cmd), traceback.format_exc())
        raise RunError(cmd, None, message='Raise TimeoutExpired : %s' % out)
    except CalledProcessError:
        out = '{0}: {1}\n{2}'.format(CalledProcessError.__name__, ''.join(cmd), traceback.format_exc())
        raise RunError(cmd, None, message='Raise CalledProcess Error : %s' % out)
    return None


def _shell(cmd) -> str:
    """ Shell Mode Check.

    Arguments:
        cmd(str): A string of program arguments.

    Returns:
        cmd(str): Modify cmd strings.
    """
    if isinstance(cmd, STRING_SET):
        cmd = [c for c in cmd.split() if c != '']
    return cmd


def _debug(cmd, debug=False):
    """ Debug Print.

    Arguments:
        cmd(str): A string of program arguments.
        debug(bool): debug flag.
    """
    if debug:
        sys.stderr.write(''.join(cmd) + '\n')
        sys.stderr.flush()

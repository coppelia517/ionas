""" YoRHa module : command line utility. """
from typing import Optional, Union, List, Tuple
import sys
import traceback
import subprocess
from subprocess import TimeoutExpired, CalledProcessError

from yorha import STRING_SET
from yorha.exception import RunError

TIMEOUT: int = 300


def run_bg(cmd: str, cwd: Optional[str] = None, shell: bool = False, debug: bool = False) -> None:
    """ Execute a child program in a new process.

    Arguments:
        cmd (str): String of program arguments.
        cwd (Optional[str]): Sets the current directory before the child is executed.
        shell (bool): If true, the command will be executed through the shell.
        debug (bool): debug mode flag.

    Raises:
        RunError: File not found.
    """
    fix_cmd: Union[str, List[str]] = _shell(cmd) if shell else cmd
    _debug(cmd, debug)
    try:
        subprocess.run(fix_cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell)
    except CalledProcessError:
        out = '{0}: {1}\n{2}'.format(CalledProcessError.__name__, ''.join(cmd), traceback.format_exc())
        raise RunError(cmd, '', message='Raise CalledProcess Error : %s' % out)


def run(cmd: str, cwd: Optional[str] = None, timeout: int = TIMEOUT, shell: bool = False,
        debug: bool = False) -> Optional[Tuple[int, str, str]]:
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
        result(Tuple[int, str, str]): tuple result.
            - returncode(int): status code.
            - out(str): Standard out.
            - err(str): Standard error.
    """
    fix_cmd = _shell(cmd) if shell else cmd
    _debug(cmd, debug)
    try:
        proc = subprocess.run(
            fix_cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, timeout=timeout, shell=shell)
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
            raise RunError(cmd, '', message='Raise UnicodeDecodeError : %s' % output)
        return (returncode, out, err)
    except TimeoutExpired:
        out = '{0}: {1}\n{2}'.format(TimeoutExpired.__name__, ''.join(cmd), traceback.format_exc())
        raise RunError(cmd, '', message='Raise TimeoutExpired : %s' % out)
    except CalledProcessError:
        out = '{0}: {1}\n{2}'.format(CalledProcessError.__name__, ''.join(cmd), traceback.format_exc())
        raise RunError(cmd, '', message='Raise CalledProcess Error : %s' % out)
    return None


def _shell(cmd: str) -> Union[str, List[str]]:
    """ Shell Mode Check.

    Arguments:
        cmd(str): A string of program arguments.

    Returns:
        cmd(str): Modify cmd strings.
    """
    if isinstance(cmd, STRING_SET):
        fix_cmd = [c for c in cmd.split() if c != '']
    return fix_cmd


def _debug(cmd: str, debug: bool = False) -> None:
    """ Debug Print.

    Arguments:
        cmd(str): A string of program arguments.
        debug(bool): debug flag.
    """
    if debug:
        sys.stderr.write(''.join(cmd) + '\n')
        sys.stderr.flush()

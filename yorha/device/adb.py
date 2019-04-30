""" YoRHa Plugins : Android Device Utility. """
from typing import Optional, cast
import os
import sys
import time
import logging
import importlib

from yorha.cmd import run, run_bg
from yorha.exception import AndroidError

from yorha.device.profile import AndroidProp

PROFILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'profile'))
if PROFILE_PATH not in sys.path:
    sys.path.insert(0, PROFILE_PATH)

TIMEOUT = 30
ADB_ROOT = os.path.abspath(os.path.dirname(__file__))
logger = logging.getLogger(__name__)


class AndroidBase:
    """ Android Debug Bridge Utility Class.

    Attributes:
        profile(str): android profile path. default: ~/profile.
        host(str): base path of profile. default: PROFILE_PATH.
    """

    def __init__(self, profile: str, host: str = PROFILE_PATH) -> None:
        self.profile: AndroidProp
        self.WIFI = False
        self._set_profile(profile, host)

    def _set_profile(self, name: str, host: str) -> None:
        """ Set Android Profile.

        Arguments:
            name(str): android serial.
            host(str): base path of profile.

        Raises:
            AndroidError: 1. Device Not Found.
                          2. Pforile Data Not Found.
        """
        class_name = '_' + name
        if not os.path.exists(host):
            logger.warning('Not Found. : %s', host)
            raise AndroidError('Not Found. : %s' % host)
        try:
            prof = None
            for fdn in os.listdir(host):
                if fdn.endswith('.py') and (name in fdn):
                    prof = fdn.replace('.py', '')
            if prof is None:
                logger.warning('The Profile is not found. : %s', name)
                class_name = '_0000000000000000'
                for fdn in os.listdir(PROFILE_PATH):
                    if fdn.endswith('_0000000000000000.py'):
                        prof = fdn.replace('.py', '')
            sys.path.append(host)
            module = importlib.import_module(str(prof))
            self.profile = getattr(module, class_name)
            self.profile.SERIAL = name
            self.profile.TMP_PICTURE = '%s_TMP.png' % name
            sys.path.remove(host)
        except Exception as e:
            sys.path.remove(host)
            logger.debug('Raise Exception : %s', str(e))
            raise AndroidError(str(e))

    def get_profile(self) -> AndroidProp:
        """ Get Android Profile.

        Returns:
            profile(AndroidProp): return profile value.
        """
        return self.profile

    def __exec(self, cmd: str, timeout: int = TIMEOUT, debug: bool = False) -> str:
        """ Execute Command for target android.

        Arguments:
            cmd(str): A string of program arguments.
            timeout(int): Expired Time. default: 30.
            debug(bool): Debug mode flag.

        Raises:
            AndroidError: Execution Error.

        Returns:
            result(str): Standard out or Standard Error.
        """
        result = run(cmd, timeout=timeout, debug=debug)
        if result:
            try:
                if not result[0]:
                    result_value = result[1].replace('\r', '')
                else:
                    logger.warning(result[2].replace('\r', ''))
                    raise AndroidError('Android Execute Failed. : %s' % result[2].replace('\r', ''))
            except Exception as e:
                logger.warning(str(e))
                raise AndroidError(str(e))
        return result_value

    def __exec_bg(self, cmd: str, debug: bool = False) -> None:
        """ Execute Command BackGround for target android.

        Arguments:
            cmd(str): A string of program arguments.
            debug(bool): Debug mode flag.
        """
        run_bg(cmd, debug=debug)

    def _target(self) -> str:
        """ Target Settings.

        Returns:
            target(str): target strings.
        """
        if not self.WIFI:
            return '-s %s' % (self.profile.SERIAL)
        return '-s %s:%s' % (self.profile.IP, self.profile.PORT)

    def _adb(self, command: str, sync: bool = True, debug: bool = False, timeout: int = TIMEOUT) -> Optional[str]:
        """ Android Debug Bridge Command Run.

        Arguments:
            command(str): A string of program arguments.
            sync(bool): target sync flag. false -> async(exec_bg()).
            debug(bool): debug mode flag.
            timeout(int): Expired Time. default: 30.

        Returns:
            result(Optional[str]): adb result.
        """
        command = 'adb %s' % command
        if sync:
            return self.__exec(command, timeout, debug)
        self.__exec_bg(command, debug)
        return None

    def kill(self) -> str:
        """ Call `adb kill-server`.

        Returns:
            result(Optional[str]): adb result.
        """
        return cast(str, self._adb('kill-server'))

    def adb(self, command: str, sync: bool = True, debug: bool = False, timeout: int = TIMEOUT) -> Optional[str]:
        """ Call `adb command.`

        Arguments:
            command(str): A string of program arguments.
            sync(bool): target sync flag. false -> async(exec_bg()).
            debug(bool): debug mode flag.
            timeout(int): Expired Time. default: 30.

        Returns:
            result(Optional[str]): adb result.
        """
        command = '%s %s' % (self._target(), command)
        return self._adb(command, sync, debug, timeout)

    def push(self, src: str, dst: str, timeout: int = TIMEOUT) -> Optional[str]:
        """ Call `adb -s {target} push src dst`

        Arguments:
            src(str): push source path.
            dst(str): push destination path.
            timeout(int): Expired Time. default: 30.

        Returns:
            result(Optional[str]): adb push result.
        """
        command = 'push %s %s' % (src, dst)
        return self.adb(command, timeout=timeout)

    def pull(self, src: str, dst: str, timeout: int = TIMEOUT) -> Optional[str]:
        """ Call `adb -s {target} pull src dst`

        Arguments:
            src(str): pull source path.
            dst(str): pull destination path.
            timeout(int): Expired Time. default: 30.

        Returns:
            result(Optional[str]): adb pull result.
        """
        command = 'pull %s %s' % (src, dst)
        return self.adb(command, timeout=timeout)

    def shell(self, command: str, sync: bool = True, debug: bool = False, timeout: int = TIMEOUT) -> Optional[str]:
        """ Call `adb -s {target} shell command`

        Arguments:
            command(str): A string of program arguments.
            sync(bool): target sync flag. false -> async(exec_bg()).
            debug(bool): debug mode flag.
            timeout(int): Expired Time. default: 30.

        Returns:
            result(Optional[str]): adb result.
        """
        command = 'shell %s' % (command)
        return self.adb(command, sync, debug, timeout)

    def connect(self) -> Optional[str]:
        """ Call `adb connect [IP Address]:[Port]`

        Returns:
            result(Optional[str]): adb result.
        """
        if self.WIFI:
            command = 'connect %s:%s' % (self.profile.IP, self.profile.PORT)
            return self._adb(command)
        return None

    def disconnect(self) -> Optional[str]:
        """ Call `adb disconnect [IP Address]:[Port]`

        Returns:
            result(Optional[str]): adb result.
        """
        if self.WIFI:
            command = 'disconnect %s:%s' % (self.profile.IP, self.profile.PORT)
            return self._adb(command)
        return None

    def usb(self) -> Optional[str]:
        """ Call `adb usb`

        Returns:
            result(Optional[str]): result
        """
        if self.WIFI:
            self.disconnect()
            self.WIFI = False
        return self.adb('usb')

    def tcpip(self) -> Optional[str]:
        """ Call `adb tcpip [Port]`

        Returns:
            result(Optional[str]): adb result.
        """
        if not self.WIFI:
            self.disconnect()
            self.WIFI = True
        command = 'tcpip %s' % (self.profile.PORT)
        return self._adb(command)

    def root(self) -> Optional[str]:
        """ Call `adb -s [SERIAL] root`

        Returns:
            result(Optional[str]): adb result.
        """
        logger.debug(str(self.adb('root')))
        self.kill()
        if self.WIFI:
            self.tcpip()
        else:
            self.usb()
        return self.connect()

    def remount(self) -> None:
        """ Call `adb -s [SERIAL] remount`
        """
        logger.debug(self.adb('remount'))

    def restart(self) -> None:
        """ Call `adb -s [SERIAL] reboot`
        """
        logger.debug(self.adb('reboot'))

    def install(self, application: str, timeout: int = TIMEOUT) -> Optional[str]:
        """ Call `adb -s [SERIAL] install -r [application]`

        Arguments:
            application(str): A string of application arguments.
            timeout(int): Expired Time. default : 30.

        Returns:
            result(Optional[str]): result
        """
        command = 'install -r %s' % (application)
        return self.adb(command, timeout=timeout)

    def uninstall(self, application: str, timeout: int = TIMEOUT) -> Optional[str]:
        """ Call `adb -s [SERIAL] uninstall [application]`

        Arguments:
            application(str): A string of application arguments.
            timeout(int): Expired Time. default : 30.

        Returns:
            result(Optional[str]): result
        """
        command = 'uninstall %s' % (application)
        return self.adb(command, timeout=timeout)

    def wait(self, timeout: int = TIMEOUT) -> Optional[str]:
        """ Call `adb -s [SERIAL] wait-for-device`

        Arguments:
            timeout(int): Expired Time. default : 30.

        Returns:
            result(Optional[str]): adb result.
        """
        return self.adb('wait-for-device', timeout=timeout)


class Android:
    """ Android Wrapper Class.

    Attributes:
        profile(str): android profile path. default: ~/profile.
        host(str): base path of profile. default: PROFILE_PATH.
    """

    def __init__(self, profile: str, host: str = PROFILE_PATH) -> None:
        self._adb = AndroidBase(profile, host)

    def get(self) -> AndroidProp:
        """ Get profile Dict.

        Returns:
            profile(Dict): return profile value.
        """
        return self._adb.get_profile()

    def shell(self, command: str, sync: bool = True, debug: bool = False, timeout: int = TIMEOUT) -> Optional[str]:
        """ Call `adb -s [serial] shell command`

        Arguments:
            command(str): A string of program arguments.
            sync(bool): target sync flag. false -> async(exec_bg()).
            debug(bool): debug mode flag.
            timeout(int): Expired Time. default: 30.

        Returns:
            result(Optional[str]): adb result.
        """
        return self._adb.shell(command, sync, debug, timeout)

    def dumpsys(self, category: str) -> Optional[str]:
        """ Call `adb -s [serial] shell dumpsys [category]`

        Arguments:
            category(str): dumpsys category.

        Returns:
            result(Optional[str]): adb result.
        """
        command = 'dumpsys %s' % category
        return self.shell(command)

    def snapshot(self, filename: str, host: str) -> Optional[str]:
        """ get snapshot by Call `adb -s [SERIAL] shell screencap -p [directory]`

        Arguments:
            filename(str): screenshot filename. (*.png)
            host(str): pull destination path.

        Returns:
            filepath(Optional[str]): capture screenshot filepath.
        """
        self._adb.shell('screencap -p /sdcard/%s' % (filename))
        self._adb.pull('/sdcard/%s' % (filename), host)
        self._adb.shell('rm /sdcard/%s' % (filename))
        return os.path.join(host, filename)

    def start(self, intent: str) -> Optional[str]:
        """ Call `adb -s [SERIAL] shell am start -n [intent]`

        Arguments:
            intent(str): start intent name.

        Returns:
            result(Optional[str]): adb result.
        """
        return self._adb.shell('am start -n %s' % intent)

    def push(self, src: str, dst: str) -> Optional[str]:
        """ Call `adb -s {target} push src dst`

        Arguments:
            src(str): push source path.
            dst(str): push destination path.

        Returns:
            result(Optional[str]): adb push result.
        """
        return self._adb.push(src, dst)

    def pull(self, src: str, dst: str) -> Optional[str]:
        """ Call `adb -s {target} pull src dst`

        Arguments:
            src(str): pull source path.
            dst(str): pull destination path.

        Returns:
            result(Optional[str]): adb pull result.
        """
        return self._adb.pull(src, dst)

    def install(self, application: str) -> None:
        """ Call `adb -s [SERIAL] install -r [application]`

        Arguments:
            application(str): A string of application arguments.
        """
        self._adb.install(application)

    def uninstall(self, application: str) -> None:
        """ Call `adb -s [SERIAL] uninstall [application]`

        Arguments:
            application(str): A string of application arguments.
        """
        self._adb.uninstall(application)

    def forward(self, command: str) -> Optional[str]:
        """ Call `adb forward command`

        Arguments:
            command(str): A string of program arguments.

        Returns:
            result(Optional[str]): adb result.
        """
        command = 'forward %s' % command
        return self._adb.adb(command)

    def input(self, command: str, sync: bool = True, debug: bool = False) -> Optional[str]:
        """ Call `adb -s [SERIAL] shell input command`

        Arguments:
            command(str): A string of program arguments.
            sync(bool): target sync flag. false -> async(exec_bg()).
            debug(bool): debug mode flag.

        Returns:
            result(Optional[str]): adb result or None.
        """
        command = 'input %s' % command
        return self._adb.shell(command, sync, debug)

    def am(self, command: str, sync: bool = True) -> Optional[str]:
        """ Call `adb -s [SERIAL] shell am command`

        Arguments:
            command(str): A string of program arguments.
            sync(bool): target sync flag. false -> async(exec_bg()).

        Returns:
            result(Optional[str]): adb result.
        """
        command = 'am %s' % command
        return self._adb.shell(command, sync=sync)

    def tap(self, x: int, y: int) -> Optional[str]:
        """ Call `adb -s [SERIAL] shell am input tap x y`

        Arguments:
            x(int): position x.
            y(int): position y.

        Returns:
            result(Optional[str]): adb result.
        """
        command = 'tap %d %d' % (x, y)
        return self.input(command, sync=True)

    def invoke(self, app: str) -> Optional[str]:
        """ Call `adb -s [SERIAL] shell am start -n [app]`

        Arguments:
            app(str): start app name.

        Returns:
            result(Optional[str]): adb result.
        """
        command = 'start -n %s' % (app)
        return self.am(command)

    def keyevent(self, code: str) -> Optional[str]:
        """ Call `adb -s [SERIAL] shell am input keyevent [code]`

        Arguments:
            code(str): keycode.

        Returns:
            result(Optional[str]): adb result.
        """
        command = 'keyevent %s ' % (code)
        return self.input(command, sync=True)

    def text(self, command: str) -> None:
        """ Call `adb -s [SERIAL] shell am input text`

        Arguments:
            command(str): input text.
        """
        args = command.split(' ')
        for arg in args:
            self._text(arg)
            self.keyevent(self.get().KEYCODE_SPACE)

    def _text(self, command: str) -> None:
        """ Call `adb -s [SERIAL] shell am input text`

        Arguments:
            command(str): input text.
        """
        command = 'text %s' % command
        self.input(command)

    def stop(self, app: str) -> Optional[str]:
        """ Call `adb -s [SERIAL] shell am force-stop [app]`

        Arguments:
            app(str): A string of application arguments.

        Returns:
            result(Optional[str]): adb result.
        """
        package = app.split('/')[0]
        command = 'force-stop %s ' % (package)
        return self.am(command)

    def getprop(self, prop: str) -> Optional[str]:
        """ Call `adb -s [SERIAL] shell getprop [prop]`

        Arguments:
            prop(str): A string of property name.

        Returns:
            result(Optional[str]): adb result.
        """
        command = 'getprop %s' % prop
        return self._adb.shell(command)

    def setprop(self, prop: str, value: str) -> Optional[str]:
        """ Call `adb -s [SERIAL] shell setprop [prop] [value]`

        Arguments:
            prop(str): A string of property name.
            value(str): A string of property arguments.

        Returns:
            result(Optional[str]): adb result.
        """
        command = 'setprop %s %s' % (prop, value)
        return self._adb.shell(command)

    def power(self) -> None:
        """ Call `adb -s [SERIAL] shell am input keyevent POWER_CODE`
        """
        self.keyevent(self.get().KEYCODE_POWER)

    def boot_completed(self) -> Optional[str]:
        """ Call `adb -s [SERIAL] shell getprop PROP_BOOT_COMPLETED`

        Returns:
            result(Optional[str]): adb result.
        """
        return self.getprop(self.get().PROP_BOOT_COMPLETED)

    def reboot(self) -> None:
        """ Call `adb -s [SERIAL] reboot`
        """
        self._adb.restart()
        time.sleep(60)
        while self.boot_completed() != '1':
            time.sleep(5)

    def rotate(self) -> Optional[int]:
        """ Get rotate value.

        Returns:
            result(int): adb result.
        """
        result = self.dumpsys('input')
        if result is None:
            return None
        if isinstance(result, bytes):
            result = result.encode()
        result_code = result.split('\n')
        for line in result_code:
            if line.find('SurfaceOrientation') >= 0:
                return int(line.split(':')[1])
        return None

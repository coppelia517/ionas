""" YoRHa Plugins : Adb Factory Utility. """
from typing import TypeVar, Dict, List, Any
from yorha.device.adb import Android
from yorha.device.adb import PROFILE_PATH

T = TypeVar('T')


class Singleton(type):
    """ Singleton meta-class
    """
    _instances: Dict[Any, type] = {}

    def __call__(cls, *args: List[Any], **kwargs: Dict[str, Any]) -> type:
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class AndroidFactory:
    """ Android Device Factory Class
    """
    __metaclass__ = Singleton

    @classmethod
    def create(cls, serial: str, host: str = PROFILE_PATH) -> Android:
        """ Create Android Device.

        Arguments:
            serial(str): android serial number.
            host(str): host filepath. default : PROFILE_PATH.

        Returns:
            device(Android): Android Device Adaptor.
        """
        return Android(serial, host)

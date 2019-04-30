""" Android Device Base Class. """


class AndroidProp:
    """ Android Device Base Class.
    """
    SERIAL: str = ''
    IP: str = ''
    PORT: str = ''
    TMP_PICTURE: str = ''

    # adb keyevent
    KEYCODE_ENTER = 'KEYCODE_DPAD_CENTER'
    KEYCODE_RIGHT = 'KEYCODE_DPAD_RIGHT'
    KEYCODE_LEFT = 'KEYCODE_DPAD_LEFT'
    KEYCODE_DOWN = 'KEYCODE_DPAD_DOWN'
    KEYCODE_UP = 'KEYCODE_DPAD_UP'
    KEYCODE_SPACE = 'KEYCODE_SPACE'

    # adb get property
    PROP_LANGUAGE = 'persist.sys.language'
    PROP_COUNTRY = 'persist.sys.country'
    PROP_BOOT_COMPLETED = 'sys.boot_completed'
    PROP_SIM_STATE = 'gsm.sim.state'

    # adb shell dumpsys category
    CATEGORY_MEDIA_AUDIO_FLINGER = 'media.audio_flinger'
    CATEGORY_POWER = 'power'
    CATEGORY_INPUT = 'input'
    CATEGORY_WIFI = 'wifi'
    CATEGORY_AUDIO = 'audio'
    CATEGORY_STATUSBAR = 'statusbar'
    CATEGORY_ACTIVITY = 'activity activities'

    VAL_BATTERY = 'mBatteryLevel'

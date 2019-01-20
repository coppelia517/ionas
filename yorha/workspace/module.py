""" YoRHa Plugins : Workspace Utility. """
import os
import shutil
import datetime
import logging

from yorha import STRING_SET
from yorha.exception import WorkspaceError

logger = logging.getLogger(__name__)


class Workspace:
    """ YoRHa Workspace Module.

    Attributes:
        path(str): workspace base path.
        clear(bool): first time, workspace base folder cleared. default: True.
    """

    def __init__(self, path, clear=False):
        if not isinstance(path, STRING_SET):
            raise WorkspaceError('path must be strings.')
        self.default_path = os.path.abspath(path)
        if os.path.exists(path):
            if os.listdir(path):
                logger.debug('It is not bacant folder in the path.')
                if clear:
                    try:
                        for f in os.listdir(path):
                            shutil.rmtree(os.path.join(path, f))
                    except OSError:
                        logger.traceback()
                        raise WorkspaceError('It must be vacant folder in the path.')
            else:
                self._mkdir_recursive(self.default_path)

    def _mkdir_recursive(self, path):
        """ Mkdir Recursive.

        Arguments:
            path(str): target path.
        """
        sub_path = os.path.dirname(path)
        if not os.path.exists(sub_path):
            self._mkdir_recursive(sub_path)
        if not os.path.exists(path):
            os.mkdir(path)

    def root(self):
        """ Get Workspace Module Root.

        Returns:
            default_path(str): default path.
        """
        return self.default_path
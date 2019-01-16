""" YoRHa base module : exceptions. """
import sys
import traceback
from typing import Dict

from yorha import STRING_SET


class YoRHaError(Exception):
    """ YoRHa Exception Base Class.

    Attributes:
        details({<string>:<base type>, ... }) : Exception details.
            - details must have 2 members. 'message' and 'type'.
    """
    details = None  # {<string>: <base type>, ... }

    def __init__(self, details):
        if not isinstance(details, Dict):
            raise Exception('YoRHa Error : Details must be a dictionary. ')
        for key in details:
            if not isinstance(key, STRING_SET):
                raise Exception('YoRHa Error : Detail keys must be strings. ')
        if 'message' not in details:
            raise Exception('YoRHa Error : Detail must have "message" field. ')
        if 'type' not in details:
            details['type'] = type(self).__name__

        self.details = details
        super(YoRHaError, self).__init__(self.details['message'])

    def __str__(self):
        message = self.message.encode('utf8')
        trace = self.format_trace()
        if trace:
            trace = trace.encode('utf8')
            return '%s\n Server side traceback: \n%s' % (message, trace)
        return message

    def __getattr__(self, attribute) -> str:
        return self.details[attribute]

    @property
    def message(self) -> str:
        """ Return message attribute in details.

        Returns:
            message(str): messages in details.
        """
        return self.details['message']

    def json(self) -> Dict[str, str]:
        """ Flush details all. format : json format.

        Returns:
            details({<string>:<base type>, ...}): flush details.
        """
        return self.details

    def has_trace(self) -> str or None:
        """ Does trace attribute have.

        Returns:
            trace(str): return trace or None.
        """
        return self.details['trace'] if 'trace' in self.details else None

    def format_trace(self) -> str:
        """ Return formatted trace attribute.

        Returns:
            formatted_trace(str): formatted trace strings.
        """
        if self.has_trace() is not None:
            convert = []
            for entry in self.trace:
                convert.append(tuple(entry))
            formatted = traceback.format_list(convert)
            return ''.join(formatted)
        return ''

    def print_trace(self):
        """ Print out trace attribute.
        """
        sys.stderr.write(self.format_trace())
        sys.stderr.flush()


class RunError(YoRHaError):
    """ Runtime Error.

    Attributes:
        cmd(str) : Command Line Args invoked Runtime Error.
        out(str) : Standard Out.
        message(str) : Exception Messages.

    """

    def __init__(self, cmd, out, message=''):
        details = {'cmd': cmd or '', 'ptyout': out or '', 'out': out or '', 'message': message or ''}
        YoRHaError.__init__(self, details)

    def __str__(self) -> str:
        return '%s:\n%s:\n%s' % (self.cmd, self.message, self.out)
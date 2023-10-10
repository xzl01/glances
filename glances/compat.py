# -*- coding: utf-8 -*-
#
# This file is part of Glances.
#
# SPDX-FileCopyrightText: 2022 Nicolas Hennion <nicolas@nicolargo.com>
#
# SPDX-License-Identifier: LGPL-3.0-only
#

# flake8: noqa
# pylint: skip-file
"""Python 2/3 compatibility shims."""

from __future__ import print_function, unicode_literals

import operator
import sys
import unicodedata
import types
import subprocess
import os
from datetime import datetime
import re

from glances.logger import logger

PY3 = sys.version_info[0] == 3

if PY3:
    import queue
    from configparser import ConfigParser, NoOptionError, NoSectionError
    from statistics import mean
    from xmlrpc.client import Fault, ProtocolError, ServerProxy, Transport, Server
    from xmlrpc.server import SimpleXMLRPCRequestHandler, SimpleXMLRPCServer
    from urllib.request import Request, urlopen, base64
    from urllib.error import HTTPError, URLError
    from urllib.parse import urlparse

    # Correct issue #1025 by monkey path the xmlrpc lib
    from defusedxml.xmlrpc import monkey_patch

    monkey_patch()

    input = input
    range = range
    map = map

    text_type = str
    binary_type = bytes
    bool_type = bool
    long = int

    PermissionError = OSError
    FileNotFoundError = FileNotFoundError

    viewkeys = operator.methodcaller('keys')
    viewvalues = operator.methodcaller('values')
    viewitems = operator.methodcaller('items')

    def printandflush(string):
        """Print and flush (used by stdout* outputs modules)"""
        print(string, flush=True)

    def to_ascii(s):
        """Convert the bytes string to a ASCII string

        Useful to remove accent (diacritics)
        """
        if isinstance(s, binary_type):
            return s.decode()
        return s.encode('ascii', 'ignore').decode()

    def to_hex(s):
        """Convert the bytes string to a hex string"""
        return s.hex()

    def listitems(d):
        return list(d.items())

    def listkeys(d):
        return list(d.keys())

    def listvalues(d):
        return list(d.values())

    def iteritems(d):
        return iter(d.items())

    def iterkeys(d):
        return iter(d.keys())

    def itervalues(d):
        return iter(d.values())

    def u(s, errors='replace'):
        if isinstance(s, text_type):
            return s
        return s.decode('utf-8', errors=errors)

    def b(s, errors='replace'):
        if isinstance(s, binary_type):
            return s
        return s.encode('utf-8', errors=errors)

    def n(s):
        '''Only in Python 2...
        from future.utils import bytes_to_native_str as n
        '''
        return s

    def nativestr(s, errors='replace'):
        if isinstance(s, text_type):
            return s
        elif isinstance(s, (int, float)):
            return s.__str__()
        else:
            return s.decode('utf-8', errors=errors)

    def system_exec(command):
        """Execute a system command and return the result as a str"""
        try:
            res = subprocess.run(command.split(' '), stdout=subprocess.PIPE).stdout.decode('utf-8')
        except Exception as e:
            logger.debug('Can not evaluate command {} ({})'.format(command, e))
            res = ''
        return res.rstrip()

else:
    from future.utils import bytes_to_native_str as n
    import Queue as queue
    from itertools import imap as map
    from ConfigParser import SafeConfigParser as ConfigParser, NoOptionError, NoSectionError
    from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler, SimpleXMLRPCServer
    from xmlrpclib import Fault, ProtocolError, ServerProxy, Transport, Server
    from urllib2 import Request, urlopen, HTTPError, URLError, base64
    from urlparse import urlparse

    # Correct issue #1025 by monkey path the xmlrpc lib
    from defusedxml.xmlrpc import monkey_patch

    monkey_patch()

    input = raw_input
    range = xrange
    ConfigParser.read_file = ConfigParser.readfp

    text_type = unicode
    binary_type = str
    bool_type = types.BooleanType
    long = long

    PermissionError = OSError
    FileNotFoundError = IOError

    viewkeys = operator.methodcaller('viewkeys')
    viewvalues = operator.methodcaller('viewvalues')
    viewitems = operator.methodcaller('viewitems')

    def printandflush(string):
        """Print and flush (used by stdout* outputs modules)"""
        print(string)
        sys.stdout.flush()

    def mean(numbers):
        return float(sum(numbers)) / max(len(numbers), 1)

    def to_ascii(s):
        """Convert the unicode 's' to a ASCII string

        Useful to remove accent (diacritics)
        """
        if isinstance(s, binary_type):
            return s
        return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore')

    def to_hex(s):
        """Convert the string to a hex string in Python 2"""
        return s.encode('hex')

    def listitems(d):
        return d.items()

    def listkeys(d):
        return d.keys()

    def listvalues(d):
        return d.values()

    def iteritems(d):
        return d.iteritems()

    def iterkeys(d):
        return d.iterkeys()

    def itervalues(d):
        return d.itervalues()

    def u(s, errors='replace'):
        if isinstance(s, text_type):
            return s.encode('utf-8', errors=errors)
        return s.decode('utf-8', errors=errors)

    def b(s, errors='replace'):
        if isinstance(s, binary_type):
            return s
        return s.encode('utf-8', errors=errors)

    def nativestr(s, errors='replace'):
        if isinstance(s, binary_type):
            return s
        elif isinstance(s, (int, float)):
            return s.__str__()
        else:
            return s.encode('utf-8', errors=errors)

    def system_exec(command):
        """Execute a system command and return the result as a str"""
        try:
            res = subprocess.check_output(command.split(' '))
        except Exception as e:
            logger.debug('Can not execute command {} ({})'.format(command, e))
            res = ''
        return res.rstrip()


# Globals functions for both Python 2 and 3


def subsample(data, sampling):
    """Compute a simple mean subsampling.

    Data should be a list of numerical itervalues

    :return: a sub-sampled list of sampling length
    """
    if len(data) <= sampling:
        return data
    sampling_length = int(round(len(data) / float(sampling)))
    return [mean(data[s * sampling_length : (s + 1) * sampling_length]) for s in range(0, sampling)]


def time_serie_subsample(data, sampling):
    """Compute a simple mean subsampling.

    Data should be a list of set (time, value)

    :return: a sub-sampled list of sampling length
    """
    if len(data) <= sampling:
        return data
    t = [t[0] for t in data]
    v = [t[1] for t in data]
    sampling_length = int(round(len(data) / float(sampling)))
    t_sub_sampled = [t[s * sampling_length : (s + 1) * sampling_length][0] for s in range(0, sampling)]
    v_sub_sampled = [mean(v[s * sampling_length : (s + 1) * sampling_length]) for s in range(0, sampling)]
    return list(zip(t_sub_sampled, v_sub_sampled))


def to_fahrenheit(celsius):
    """Convert Celsius to Fahrenheit."""
    return celsius * 1.8 + 32


def is_admin():
    """Return if current user is an admin or not

    The inner function fails unless you have Windows XP SP2 or higher.
    The failure causes a traceback to be printed and this function to return False.

    https://stackoverflow.com/a/19719292

    :return: True if the current user is an 'Admin' whatever that means (root on Unix), otherwise False.
    """

    if os.name == 'nt':
        import ctypes
        import traceback

        # WARNING: requires Windows XP SP2 or higher!
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception as e:
            traceback.print_exc()
            return False
    else:
        # Check for root on Posix
        return os.getuid() == 0


def key_exist_value_not_none(k, d):
    # Return True if:
    # - key k exists
    # - d[k] is not None
    return k in d and d[k] is not None


def key_exist_value_not_none_not_v(k, d, value='', lengh=None):
    # Return True if:
    # - key k exists
    # - d[k] is not None
    # - d[k] != value
    # - if lengh is not None and len(d[k]) >= lengh
    return k in d and d[k] is not None and d[k] != value and (lengh is None or len(d[k]) >= lengh)


def disable(class_name, var):
    """Set disable_<var> to True in the class class_name."""
    setattr(class_name, 'enable_' + var, False)
    setattr(class_name, 'disable_' + var, True)


def enable(class_name, var):
    """Set disable_<var> to False in the class class_name."""
    setattr(class_name, 'enable_' + var, True)
    setattr(class_name, 'disable_' + var, False)


def pretty_date(time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    Source: https://stackoverflow.com/questions/1551382/user-friendly-time-format-in-python
    """
    now = datetime.now()
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time, datetime):
        diff = now - time
    elif not time:
        diff = 0
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(second_diff) + " secs"
        if second_diff < 120:
            return "a min"
        if second_diff < 3600:
            return str(second_diff // 60) + " mins"
        if second_diff < 7200:
            return "an hour"
        if second_diff < 86400:
            return str(second_diff // 3600) + " hours"
    if day_diff == 1:
        return "yesterday"
    if day_diff < 7:
        return str(day_diff) + " days"
    if day_diff < 31:
        return str(day_diff // 7) + " weeks"
    if day_diff < 365:
        return str(day_diff // 30) + " months"
    return str(day_diff // 365) + " years"


def urlopen_auth(url, username, password):
    """Open a url with basic auth"""
    return urlopen(
        Request(
            url,
            headers={'Authorization': 'Basic ' + base64.b64encode(('%s:%s' % (username, password)).encode()).decode()},
        )
    )


def string_value_to_float(s):
    """Convert a string with a value and an unit to a float.
    Example:
    '12.5 MB' -> 12500000.0
    '32.5 GB' -> 32500000000.0
    Args:
        s (string): Input string with value and unit
    Output:
        float: The value in float
    """
    convert_dict = {
        None: 1,
        'B': 1,
        'KB': 1000,
        'MB': 1000000,
        'GB': 1000000000,
        'TB': 1000000000000,
        'PB': 1000000000000000,
    }
    unpack_string = [
        i[0] if i[1] == '' else i[1].upper() for i in re.findall(r'([\d.]+)|([^\d.]+)', s.replace(' ', ''))
    ]
    if len(unpack_string) == 2:
        value, unit = unpack_string
    elif len(unpack_string) == 1:
        value = unpack_string[0]
        unit = None
    else:
        return None
    try:
        value = float(unpack_string[0])
    except ValueError:
        return None
    return value * convert_dict[unit]

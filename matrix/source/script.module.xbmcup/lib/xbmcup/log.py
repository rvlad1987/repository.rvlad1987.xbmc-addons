# -*- coding: utf-8 -*-

__author__ = 'hal9000'
__all__ = ['log', 'debug', 'error', 'fatal', 'info', 'notice', 'severe', 'warning']

import sys

import xbmc

_ADDON = sys.argv[0].replace('plugin://', '').replace('/', '').upper()

_LEVEL = dict(
    debug = xbmc.LOGDEBUG,
    error = xbmc.LOGERROR,
    fatal = xbmc.LOGFATAL,
    info = xbmc.LOGINFO,
    none = xbmc.LOGNONE,
    notice = xbmc.LOGNOTICE,
    severe = xbmc.LOGSEVERE,
    warning = xbmc.LOGWARNING
)

def _dump(obj):
    if isinstance(obj, str):
        return '"' + str(obj).replace('\x00', '') + '"'

    elif isinstance(obj, unicode):
        return 'u"' + str(obj.encode('utf8')).replace('\x00', '') + '"'

    elif isinstance(obj, list):
        return '[' + ', '.join([_dump(x) for x in obj]) + ']'

    elif isinstance(obj, tuple):
        return '(' + ', '.join([_dump(x) for x in obj]) + (')' if len(obj) > 1 else ', )')

    elif isinstance(obj, dict):
        return '{' + ', '.join([': '.join([_dump(k), _dump(v)]) for k, v in obj.iteritems()]) + '}'

    else:
        return str(obj).replace('\x00', '')

def log(*args, **kwargs):
    msg = [_ADDON]
    for m in args:
        msg.append(': ' if isinstance(msg[-1], str) else '; ')
        msg.append(m.encode('utf8') if isinstance(m, unicode) else m)
    xbmc.log(msg=''.join([(x if isinstance(x, basestring) else _dump(x)) for x in msg]), level=_LEVEL[kwargs.get('level', 'notice')])

def debug(*args):
    log(*args, level='debug')

def error(*args):
    log(*args, level='error')

def fatal(*args):
    log(*args, level='fatal')

def info(*args):
    log(*args, level='info')

def notice(*args):
    log(*args, level='notice')

def severe(*args):
    log(*args, level='severe')

def warning(*args):
    log(*args, level='warning')

def set_prefix(prefix):
    global _ADDON
    _ADDON = prefix.upper()


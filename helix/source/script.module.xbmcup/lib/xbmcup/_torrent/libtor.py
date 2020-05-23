# -*- coding: utf-8 -*-

__author__ = 'hal9000'
__all__ = ['LibTorrent']

try:
    import libtorrent
except ImportError, e:
    _IS_LIBTORRENT = False
    file('C:\\Users\\hal9000\\AppData\\Roaming\\XBMC\\addons\\script.module.xbmcup.test\\loglog.txt', 'wb').write(str(e))
else:
    _IS_LIBTORRENT = True

class LibTorrent(object):
    def __init__(self):
        self.support = _IS_LIBTORRENT

    def info(self, torrent):
        pass

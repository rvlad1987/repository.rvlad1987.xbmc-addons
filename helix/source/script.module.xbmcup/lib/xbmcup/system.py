# -*- coding: utf-8 -*-

__author__ = 'hal9000'
__all__ = ['sleep', 'isabort', 'sound', 'rpc', 'execute', 'server', 'restart', 'shutdown', 'monitor', 'config', 'FS', 'fs']

import sys
import os.path

import xbmc
import xbmcvfs

from xbmc import sleep
from xbmc import abortRequested as isabort


def sound(status):
    xbmc.enableNavSounds(status)

def rpc():
    # TODO: Create RPC API
    pass

def execute():
    # TODO: Create execute
    pass

def server(type, status, wait=False):
    servers = dict(
        air = xbmc.SERVER_AIRPLAYSERVER,
        event = xbmc.SERVER_EVENTSERVER,
        rpc = xbmc.SERVER_JSONRPCSERVER,
        upnpr = xbmc.SERVER_UPNPRENDERER,
        upnp = xbmc.SERVER_UPNPSERVER,
        web = xbmc.SERVER_WEBSERVER,
        zeroconf = xbmc.SERVER_ZEROCONF
    )
    return xbmc.startServer(servers[type], status, wait)

def restart():
    xbmc.restart()

def shutdown():
    xbmc.shutdown()

class Monitor(xbmc.Monitor):
    def __init__(self, **kwargs):
        self._call = kwargs

    def onAbortRequested(self):
        if 'abort' in self._call:
            self._call['abort']()

    def onDatabaseUpdated(self, db):
        if 'db' in self._call:
            self._call['db'](db)

    def onScreensaverActivated(self):
        if 'saver' in self._call:
            self._call['saver'](True)

    def onScreensaverDeactivated(self):
        if 'saver' in self._call:
            self._call['saver'](False)

    def onSettingsChanged(self):
        if 'setting' in self._call:
            self._call['setting']()


def monitor(**kwargs):
    mon = Monitor(**kwargs)
    return mon


class Config(object):
    _support = {'all': []}
    _region = {}
    _platform = -1
    def __getattr__(self, key):
        value = self._get(key)
        return value

    def __getitem__(self, key):
        return self._get(key)

    def _get(self, key):
        if key == 'lang':
            return xbmc.getLanguage()

        elif key == 'langname':
            langname = xbmc.getLanguage()
            if langname.find('Oromo') != -1:
                langname = 'Oromo'
            else:
                for tag in (' (', ';', ','):
                    i = langname.find(tag)
                    if i != -1:
                        langname = langname[0:i]
                        break
            try:
                LANGCODE[langname]
            except KeyError:
                return 'English'
            else:
                return langname

        elif key == 'langcode':
            return LANGCODE[self._get('langname')]

        elif key == 'dvd':
            state = {0: 'open', 1: 'notready', 2: 'ready', 3: 'empty', 4: 'present', 5: None}
            return state[xbmc.getDVDState()]

        elif key == 'mem':
            return xbmc.getFreeMem() # MB

        elif key == 'time':
            return xbmc.getGlobalIdleTime()

        elif key == 'skin':
            return xbmc.getSkinDir()

        elif key == 'ip':
            return xbmc.getIPAddress()

        elif key == 'platform':
            if self._platform == -1:
                for platform in ('linux', 'windows', 'android', 'atv2', 'ios', 'osx'):
                    if xbmc.getCondVisibility('system.platform.' + platform):
                        self._platform = platform
                        break
                else:
                    self._platform = None
            return self._platform

        elif key == 'is_64bits':
            return sys.maxsize > 2**32

        elif key == 'support':
            if not self._support['all']:
                for src, dst in (('video', 'video'), ('music', 'audio'), ('picture', 'picture')):
                    self._support[dst] = [x[1:] for x in xbmc.getSupportedMedia(src).split('|')]
                    self._support['all'].extend(self._support[dst])
            return self._support

        elif key == 'region':
            if not self._region:
                for tag in ('dateshort', 'datelong', 'time', 'meridiem', 'tempunit', 'speedunit'):
                    self._region[tag] = xbmc.getRegion(tag)
            return self._region

        else:
            raise AttributeError, key

config = Config()


class FS(object):
    def __init__(self, addon=None):
        if not addon:
            addon = sys.argv[0].replace('plugin://', '').replace('/', '')
        self._sandbox = addon
        self._special = 'xbmc://', 'home://', 'temp://', 'masterprofile://', 'profile://', 'subtitles://', 'userdata://', 'database://', 'thumbnails://',\
                        'recordings://', 'screenshots://', 'musicplaylists://', 'videoplaylists://', 'cdrips://', 'skin://', 'logpath://'
        self.mkdir('sandbox://')

    def __call__(self, path=None):
        if not path:
            path = 'sandbox://'
        return self._path(path)

    def _path(self, path):
        if path.startswith('sandbox://'):
            path = path.replace('sandbox://', 'temp://xbmcup/' + self._sandbox + '/')
        special = [x for x in self._special if path.startswith(x)]
        if special:
            return os.path.normpath(xbmc.translatePath(path.replace(special[0], 'special://' + special[0].replace(':/', ''))))
        return os.path.normpath(path)

    # FILE SYSTEM

    def file(self, filename, mode=None):
        if mode is None:
            mode = 'r'
        elif mode in ('w', 'a'):
            self.check(filename)
        return xbmcvfs.File(self._path(filename), mode + 'b')

    def listdir(self, dirname, full=False):
        filelist = xbmcvfs.listdir(self._path(dirname))
        if not full:
            return filelist
        return [os.path.join(dirname, x) for x in filelist[0]], [os.path.join(dirname, x) for x in filelist[1]]

    def exists(self, path):
        return xbmcvfs.exists(self._path(path))

    def copy(self, src, dst):
        # TODO: create the method of copy
        pass

    def move(self, src, dst):
        # TODO: create the method of move
        pass

    def rename(self, src, dst):
        # TODO: create the method of rename
        pass

    def delete(self, path, inner=False):
        dirlist, filelist = self.listdir(path, full=True)
        [xbmcvfs.delete(self._path(x)) for x in filelist]
        [self.delete(self._path(x)) for x in dirlist]
        if not inner:
            if not xbmcvfs.delete(self._path(path)):
                xbmcvfs.rmdir(self._path(path))

    def mkdir(self, dirname):
        if self.exists(dirname):
            return True
        return xbmcvfs.mkdirs(self._path(dirname))

    def check(self, filename):
        return self.mkdir(os.path.dirname(self._path(filename)))

# for current plugin
fs = FS()


LANGCODE = dict((

('Afar', 'aa'),
('Abkhazian', 'ab'),
('Afrikaans', 'af'),
('Amharic', 'am'),
('Arabic', 'ar'),
('Assamese', 'as'),
('Aymara', 'ay'),
('Azerbaijani', 'az'),
('Bashkir', 'ba'),
('Byelorussian', 'be'),
('Bulgarian', 'bg'),
('Bihari', 'bh'),
('Bislama', 'bi'),
('Bengali', 'bn'),
('Tibetan', 'bo'),
('Breton', 'br'),
('Catalan', 'ca'),
('Corsican', 'co'),
('Czech', 'cs'),
('Welsh', 'cy'),
('Danish', 'da'),
('German', 'de'),
('Bhutani', 'dz'),
('Greek', 'el'),
('English', 'en'),
('Esperanto', 'eo'),
('Spanish', 'es'),
('Estonian', 'et'),
('Basque', 'eu'),
('Persian', 'fa'),
('Finnish', 'fi'),
('Fiji', 'fj'),
('Faeroese', 'fo'),
('French', 'fr'),
('Frisian', 'fy'),
('Irish', 'ga'),
('Scots Gaelic', 'gd'),
('Galician', 'gl'),
('Guarani', 'gn'),
('Gujarati', 'gu'),
('Hausa', 'ha'),
('Hindi', 'hi'),
('Croatian', 'hr'),
('Hungarian', 'hu'),
('Armenian', 'hy'),
('Interlingua', 'ia'),
('Interlingue', 'ie'),
('Inupiak', 'ik'),
('Indonesian', 'in'),
('Icelandic', 'is'),
('Italian', 'it'),
('Hebrew', 'iw'),
('Japanese', 'ja'),
('Yiddish', 'ji'),
('Javanese', 'jw'),
('Georgian', 'ka'),
('Kazakh', 'kk'),
('Greenlandic', 'kl'),
('Cambodian', 'km'),
('Kannada', 'kn'),
('Korean', 'ko'),
('Kashmiri', 'ks'),
('Kurdish', 'ku'),
('Kirghiz', 'ky'),
('Latin', 'la'),
('Lingala', 'ln'),
('Laothian', 'lo'),
('Lithuanian', 'lt'),
('Latvian', 'lv'),
('Malagasy', 'mg'),
('Maori', 'mi'),
('Macedonian', 'mk'),
('Malayalam', 'ml'),
('Mongolian', 'mn'),
('Moldavian', 'mo'),
('Marathi', 'mr'),
('Malay', 'ms'),
('Maltese', 'mt'),
('Burmese', 'my'),
('Nauru', 'na'),
('Nepali', 'ne'),
('Dutch', 'nl'),
('Norwegian', 'no'),
('Occitan', 'oc'),
('Oromo', 'om'),
('Oriya', 'or'),
('Punjabi', 'pa'),
('Polish', 'pl'),
('Pashto', 'ps'),
('Portuguese', 'pt'),
('Quechua', 'qu'),
('Rhaeto-Romance', 'rm'),
('Kirundi', 'rn'),
('Romanian', 'ro'),
('Russian', 'ru'),
('Kinyarwanda', 'rw'),
('Sanskrit', 'sa'),
('Sindhi', 'sd'),
('Sangro', 'sg'),
('Serbo-Croatian', 'sh'),
('Singhalese', 'si'),
('Slovak', 'sk'),
('Slovenian', 'sl'),
('Samoan', 'sm'),
('Shona', 'sn'),
('Somali', 'so'),
('Albanian', 'sq'),
('Serbian', 'sr'),
('Siswati', 'ss'),
('Sesotho', 'st'),
('Sundanese', 'su'),
('Swedish', 'sv'),
('Swahili', 'sw'),
('Tamil', 'ta'),
('Tegulu', 'te'),
('Tajik', 'tg'),
('Thai', 'th'),
('Tigrinya', 'ti'),
('Turkmen', 'tk'),
('Tagalog', 'tl'),
('Setswana', 'tn'),
('Tonga', 'to'),
('Turkish', 'tr'),
('Tsonga', 'ts'),
('Tatar', 'tt'),
('Twi', 'tw'),
('Ukrainian', 'uk'),
('Urdu', 'ur'),
('Uzbek', 'uz'),
('Vietnamese', 'vi'),
('Volapuk', 'vo'),
('Wolof', 'wo'),
('Xhosa', 'xh'),
('Yoruba', 'yo'),
('Chinese', 'zh'),
('Zulu', 'zu')

))

# -*- coding: utf-8 -*-

__author__ = 'hal9000'
__all__ = ['Plugin', 'Handler', 'Lang', 'lang', 'Setting', 'setting', 'Addon', 'addon']

import time
import sys
import json
import urllib

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

from system import config as configLang


def add_item(obj, obj_item, total=0):
    if obj is None:
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), '', xbmcgui.ListItem(), False, total)
    else:

        item = obj_item.to_item()

        if obj['menu']:
            menu = []
            for title, link in obj['menu']:
                url = 'XBMC.RunPlugin(%s)' % (sys.argv[0] + '?json' + urllib.quote_plus(json.dumps({
                    'source': 'menu',
                    'folder': obj['folder'],
                    'parent': obj_item.to_dict(),
                    'url': link
                })))
                menu.append((title, url))
            item.addContextMenuItems(menu, obj['menu_replace'])

        if not obj['folder'] and obj['url'][0] == 'play':
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), obj['url'][1], item, obj['folder'], total)

        else:
            url = sys.argv[0] + '?json' + urllib.quote_plus(json.dumps({
                'source': 'item',
                'folder': obj['folder'],
                'parent': obj_item.to_dict(),
                'url': obj['url']
            }))

            if not obj['folder'] and obj['url'][0] == 'resolve':
                # TODO: Check the support for 'plugin' action
                item.setProperty('isPlayable', 'True')

            xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, item, obj['folder'], total)


def compile_link(method, handler, *args, **kwargs):
    argv = None
    if args:
        argv = args
    elif kwargs:
        argv = kwargs
    return method, handler, argv



class Item(object):
    def __init__(self, jsobj=None):
        if not jsobj:
            jsobj = {}
        self.to_object(jsobj)

    def to_object(self, jsobj):
        self.path = jsobj.get('path')
        self.title = jsobj.get('title', u' ')
        self.label = jsobj.get('label')
        self.media = jsobj.get('media')
        self.info = jsobj.get('info', {})
        self.property = jsobj.get('property', {})
        self.icon = jsobj.get('icon')
        self.cover = jsobj.get('cover')
        self.fanart = jsobj.get('fanart')
        self.color1 = jsobj.get('color1')
        self.color2 = jsobj.get('color2')
        self.color3 = jsobj.get('color3')

    def to_dict(self):
        return {
            'path': self.path,
            'title': self.title,
            'label': self.label,
            'media': self.media,
            'info': self.info,
            'property': self.property,
            'icon': self.icon,
            'cover': self.cover,
            'fanart': self.fanart,
            'color1': self.color1,
            'color2': self.color2,
            'color3': self.color3
        }

    def to_item(self):
        item = xbmcgui.ListItem(label=self.title)

        if self.path:
            item.setPath(self.path)

        if self.label:
            item.setLabel2(self.label)

        if self.icon:
            item.setIconImage(self.icon)

        if self.cover:
            item.setThumbnailImage(self.cover)

        if self.media and self.info:
            media = self.media
            if media == 'audio':
                media = 'music'
            elif media == 'picture':
                media = 'pictures'
            item.setInfo(media, self.info)

        for key, value in (('image', self.fanart), ('color1', self.color1), ('color2', self.color2), ('color3', self.color3)):
            key = 'fanart_' + key
            if value and key not in self.property:
                item.setProperty(key, value)

        for key, value in self.property.iteritems():
            item.setProperty(key, value)

        return item


class Handler(object):
    def __init__(self, argv, parent, replace, **kwargs):
        self.argv = argv
        self.parent = Item(parent)
        self.params = kwargs
        self._variables = {
            'is_replace': replace,
            'is_item': False,
            'is_render': False,
            'is_reset': False,
            'reset': []
        }

    def handle(self):
        pass

    def reset(self):
        self._variables['is_item'] = False
        self._variables['is_reset'] = True
        self._variables['reset'] = []

    def render(self, **kwargs):
        """
        kwargs:
            title=str|unicode
            content="files, songs, artists, albums, movies, tvshows, episodes, musicvideos"
            sort=str
            mode="list, biglist, info, icon, bigicon, view, view2, thumb, round, fanart1, fanart2, fanart3"
            fanart=path
            color1=color
            color2=color
            color3=color
            replace=bool(False)
            cache=bool(True)
        """

        replace = self._variables['is_replace']
        if 'replace' in kwargs and isinstance(kwargs['replace'], bool):
            replace = kwargs['replace']

        if self._variables['is_reset']:
            self._variables['is_item'] = False

            app = {'reset': self._variables['reset'], 'render': kwargs}

            if replace:
                xbmc.executebuiltin('XBMC.Container.Update(%s,replace)' % (sys.argv[0] + '?json' + urllib.quote_plus(json.dumps(app))))
            else:
                xbmc.executebuiltin('XBMC.Container.Update(%s)' % (sys.argv[0] + '?json' + urllib.quote_plus(json.dumps(app))))

        else:

            if kwargs.get('content') and kwargs['content'] in ('files', 'songs', 'artists', 'albums', 'movies', 'tvshows', 'episodes', 'musicvideos'):
                xbmcplugin.setContent(int(sys.argv[1]), kwargs['content'])

            if kwargs.get('title') and isinstance(kwargs['title'], basestring):
                xbmcplugin.setPluginCategory(int(sys.argv[1]), kwargs['title'])

            fanart = {}
            if kwargs.get('fanart') and isinstance(kwargs['fanart'], basestring):
                fanart['image'] = kwargs['fanart']
            for i in range(1,4):
                key = 'color' + str(i)
                if kwargs.get(key) and isinstance(kwargs[key], basestring):
                    fanart[key] = kwargs[key]
            if fanart:
                xbmcplugin.setPluginFanart(int(sys.argv[1]), **fanart)

            if kwargs.get('sort'):
                sort = {
                    'album': xbmcplugin.SORT_METHOD_ALBUM,
                    'album_ignore_the': xbmcplugin.SORT_METHOD_ALBUM_IGNORE_THE,
                    'artist': xbmcplugin.SORT_METHOD_ARTIST,
                    'ignore_the': xbmcplugin.SORT_METHOD_ARTIST_IGNORE_THE,
                    'bitrate': xbmcplugin.SORT_METHOD_BITRATE,
                    'date': xbmcplugin.SORT_METHOD_DATE,
                    'drive_type': xbmcplugin.SORT_METHOD_DRIVE_TYPE,
                    'duration': xbmcplugin.SORT_METHOD_DURATION,
                    'episode': xbmcplugin.SORT_METHOD_EPISODE,
                    'file': xbmcplugin.SORT_METHOD_FILE,
                    'genre': xbmcplugin.SORT_METHOD_GENRE,
                    'label': xbmcplugin.SORT_METHOD_LABEL,
                    'label_ignore_the': xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,
                    'listeners': xbmcplugin.SORT_METHOD_LISTENERS,
                    'mpaa_rating': xbmcplugin.SORT_METHOD_MPAA_RATING,
                    'none': xbmcplugin.SORT_METHOD_NONE,
                    'playlist_order': xbmcplugin.SORT_METHOD_PLAYLIST_ORDER,
                    'productioncode': xbmcplugin.SORT_METHOD_PRODUCTIONCODE,
                    'program_count': xbmcplugin.SORT_METHOD_PROGRAM_COUNT,
                    'size': xbmcplugin.SORT_METHOD_SIZE,
                    'song_rating': xbmcplugin.SORT_METHOD_SONG_RATING,
                    'studio': xbmcplugin.SORT_METHOD_STUDIO,
                    'studio_ignore_the': xbmcplugin.SORT_METHOD_STUDIO_IGNORE_THE,
                    'title': xbmcplugin.SORT_METHOD_TITLE,
                    'title_ignore_the': xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE,
                    'tracknum': xbmcplugin.SORT_METHOD_TRACKNUM,
                    'unsorted': xbmcplugin.SORT_METHOD_UNSORTED,
                    'video_rating': xbmcplugin.SORT_METHOD_VIDEO_RATING,
                    'video_runtime': xbmcplugin.SORT_METHOD_VIDEO_RUNTIME,
                    'video_sort_title': xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE,
                    'video_sort_title_ignore_the': xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE_IGNORE_THE,
                    'video_title': xbmcplugin.SORT_METHOD_VIDEO_TITLE,
                    'video_year': xbmcplugin.SORT_METHOD_VIDEO_YEAR
                }
                if kwargs['sort'] in sort:
                    # TODO: Check param "label2Mask": http://mirrors.xbmc.org/docs/python-docs/xbmcplugin.html#-addSortMethod
                    xbmcplugin.addSortMethod(int(sys.argv[1]), sort[kwargs['sort']])

            if kwargs.get('property') and isinstance(kwargs['property'], dict):
                for key, value in kwargs['property'].iteritem():
                    xbmcplugin.setProperty(int(sys.argv[1]), key, value)

            if kwargs.get('mode'):
                mode = {
                    'list': 50,
                    'biglist': 51,
                    'info': 52,
                    'icon': 54,
                    'bigicon': 501,
                    'view': 53,
                    'view2': 502,
                    'thumb': 500,
                    'round': 501,
                    'fanart1': 57,
                    'fanart2': 59,
                    'fanart3': 510
                }
                if kwargs['mode'] in mode:
                    xbmc.executebuiltin("Container.SetViewMode(%s)" % mode[kwargs['mode']])

            cache = True
            if 'cache' in kwargs and not kwargs['cache']:
                cache = False

            xbmcplugin.endOfDirectory(int(sys.argv[1]), True, replace, cache)


    def link(self, handler, *args, **kwargs):
        return compile_link('link', handler, *args, **kwargs)

    def replace(self, handler, *args, **kwargs):
        return compile_link('replace', handler, *args, **kwargs)

    def resolve(self, handler, *args, **kwargs):
        return compile_link('resolve', handler, *args, **kwargs)

    def plugin(self, plugin, *args, **kwargs):
        return compile_link('plugin', handler, *args, **kwargs)

    def play(self, url):
        return 'play', url

    def item(self, title, url, **kwargs):
        self._variables['is_item'] = True

        total = int(kwargs.get('total', 0))

        if isinstance(url, basestring):
            url = self.play(url)

        item = Item(dict([(x, kwargs.get(x)) for x in ('label', 'media', 'icon', 'cover', 'fanart', 'color1', 'color2', 'color3')]))
        item.title = title
        item.info = kwargs.get('info', {})
        item.property = dict([(x.lower(), y) for x, y in kwargs.get('property', {}).items()])

        obj = {
            'url': url,
            'folder': kwargs.get('folder', False),
            'menu': kwargs.get('menu', []),
            'menu_replace': kwargs.get('menu_replace', False)
        }

        self._variables['reset'].append((obj, item.to_dict())) if self._variables['is_reset'] else add_item(obj, item, total)

    def null(self, total=0):
        self._variables['reset'].append((None, None)) if self._variables['is_reset'] else add_item(None, None, total)


class Plugin(object):
    _index = None
    _handler = {}

    def route(self, route, handler):
        if route is None:
            self._index = handler
        else:
            self._handler[route] = handler

    def run(self, **kwargs):
        self.app = None
        self.params = kwargs
        
        if len(sys.argv) < 3 or not sys.argv[2]:
            self.app = {'folder': True, 'source': 'item', 'parent': {}, 'url': ('link', None, None)}

        else:
            if sys.argv[2][0:5] == '?json':
                self.app = json.loads(urllib.unquote_plus(sys.argv[2][5:]))
            else:
                # TODO: Export API
                pass
        
        if self.app:

            if 'reset' in self.app:
                self._action_reset()

            elif self.app['url'][0] == 'resolve':
                self._action_resolve()

            elif self.app['url'][0] == 'play':
                self._action_play()

            elif self.app['url'][0] == 'plugin':
                self._action_plugin()

            else:
                self._action_link()


    def _action_reset(self):
        total = len(self.app['reset'])
        for item in self.app['reset']:
            add_item(item[0], Item(item[1]), total)
        Handler(None, None, False).render(**self.app['render'])


    def _action_plugin(self):
        # TODO: Call an outside plugin
        pass


    def _action_link(self):
        if not self.app['folder'] or self.app['source'] == 'menu':
            self.app['source'] = 'item'
            self.app['folder'] = True
            xbmc.executebuiltin('XBMC.Container.Update(%s)' % (sys.argv[0] + '?json' + urllib.quote_plus(json.dumps(self.app))))

        else:
            app, res = self._action()
            if app:
                if app._variables['is_item']:
                    app.render()



    def _action_play(self):
        item = Item(self.app['parent']).to_item()
        item.setPath(self.app['url'][1])
        player = xbmc.Player()
        player.play(self.app['url'][1], item)
        while True:
            time.sleep(0.2)
            if not player.isPlaying():
                break


    def _action_resolve(self):
        app, res = self._action()
        if app:
            if self.app['folder'] or self.app['source'] == 'menu':
                if res:
                    item = self._item(app, res)
                    player = xbmc.Player()
                    player.play(item.getfilename(), item)
                    while True:
                        time.sleep(0.2)
                        if not player.isPlaying():
                            break
            else:
                if res:
                    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, self._item(app, res))
                else:
                    xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, xbmcgui.ListItem())


    def _action(self):
        handler = None
        if self.app['url'][1] is None:
            handler = self._index
        else:
            try:
                handler = self._handler[self.app['url'][1]]
            except KeyError:
                # TODO: Handler not found
                pass

        if not handler:
            return None, None
        
        app = handler(self.app['url'][2], self.app['parent'], bool(self.app['url'][0] == 'replace'), **self.params)
        
        try:
            res = app.handle()
        except Exception, e:
            # TODO: Exception App
            #return None, None
            print str(e)
            raise
        else:
            return app, res

    def _item(self, app, obj):
        if isinstance(obj, basestring):
            item = app.parent.to_item()
            item.setPath(obj)
        elif isinstance(obj, dict):
            item = Item(obj).to_item()
        else:
            item = obj.to_item()
        return item


class Service(object):
    def run(self):
        loop = time.time()

        while True:

            if xbmc.abortRequested:
                break

            if time.time() > loop:
                timeout = self.handle()
                if timeout:
                    loop += timeout
                    
            xbmc.sleep(100)

    def handle(self):
        pass


class BaseDict(object):
    def __init__(self, addon=None):
        if not addon:
            addon = sys.argv[0].replace('plugin://', '').replace('/', '')
        self._addon = xbmcaddon.Addon(id=addon)

    def __getattr__(self, key):
        value = self._get(key)
        return value

    def __setattr__(self, key, value):
        if key == '_addon':
            self.__dict__[key] = value
        else:
            self._set(key, value)

    def __getitem__(self, key):
        return self._get(key)

    def __setitem__(self, key, value):
        self._set(key, value)

    def _set(self):
        pass


class Lang(BaseDict):
    _map = {}

    def _get(self, key):
        if isinstance(key, basestring):
            key = self._map[key]
        return self._addon.getLocalizedString(id=key)

    def map(self, key, value=None):
        if isinstance(key, dict):
            self._map.update(key)
        elif isinstance(key, (tuple, list)):
            self._map.update(dict(key))
        else:
            self._map[key] = value

# for current plugin
lang = Lang()


class Plural:
    def __init__(self, addon=None):
        self.lang = Lang(addon)
        self.current = configLang.langcode

    def parse(self, number, lang_key, sep=u'|'):
        text = self.lang[lang_key]
        if self.current == 'ru':
            return self._ru(number, text, sep)
        else:
            return self._en(number, text, sep)

    def _en(self, number, text, sep):
        plural = text.split(sep)
        if number < 0:
            number *= -1
        return self.format(number, plural[1] if number > 1 else plural[0])

    def _ru(self, number, text, sep):
        plural = text.split(sep)
        if not number:
            return self.format(number, plural[0])
        if number < 0:
            number *= -1
        nmod10 = number - 10*int(number/10)
        nmod100 = number - 100*int(number/100)
        if number == 1 or (nmod10 == 1 and nmod100 != 11):
            return self.format(number, plural[1])
        elif nmod10 > 1 and nmod10 < 5 and nmod100 != 12 and nmod100 != 13 and nmod100 != 14:
            return self.format(number, plural[2])
        else:
            return self.format(number, plural[3])

    def format(self, number, text):
        return text % number if text.find(u'%d') != -1 else text


# for current plugin
plural = Plural()


class Setting(BaseDict):
    def _get(self, key):
        return self._addon.getSetting(id=key)

    def _set(self, key, value):
        self._addon.setSetting(id=key, value=value)

# for current plugin
setting = Setting()


class Addon(BaseDict):
    def _get(self, key):
        return self._addon.getAddonInfo(key)

# for current plugin
addon = Addon()

# -*- coding: utf-8 -*-

__author__ = 'hal9000'
__all__ = ['window', 'control', 'number', 'date', 'time', 'ip', 'select', 'confirm', 'setting',
           'alert', 'prompt', 'password', 'captcha', 'browse', 'text', 'progress']

import sys

import xbmc
import xbmcgui

import _window as window
import _control as control

def _title(title):
    if not title:
        from .app import addon
        title = addon.name
    return title

def _numeric(format, title, default):
    args = [format, _title(title)]
    if default is not None:
        args.append(default)
    return xbmcgui.Dialog().numeric(*args)

def _keyboard(hidden, title, default):
    title = _title(title)
    if default is None:
        default = ''
    k = xbmc.Keyboard(default, title, hidden)
    k.doModal()
    if k.isConfirmed():
        return k.getText()

def _lines(*args, **kwargs):
    params = {'heading': _title(kwargs.get('title'))}
    lines = []
    for line in args:
        for lin in line.split('\n'):
            lines.append(lin)
    if not lines:
        lines = ['']
    params['line1'] = lines[0]
    if len(lines) > 1:
        params['line2'] = lines[1]
    if len(lines) > 2:
        params['line3'] = lines[2]
    return params


def number(title=None, default=None):
    return _numeric(0, title, default)


def date(title=None, default=None):
    return _numeric(1, title, default)


def time(title=None, default=None):
    return _numeric(2, title, default)


def ip(title=None, default=None):
    return _numeric(3, title, default)


def select(title=None, items=None):
    if isinstance(title, (list, tuple)):
        items = title[:]
        title = None
    title = _title(title)
    if not items:
        items = []
    if len(items)>0 and not isinstance(items[0], (list, tuple)):
        items = [(i, x) for i, x in enumerate(items)]
    sel = xbmcgui.Dialog().select(title, [x[1] for x in items])
    if sel == -1:
        return None
    else:
        return items[sel][0]


def alert(*args, **kwargs):
    params = _lines(*args, **kwargs)
    xbmcgui.Dialog().ok(**params)


def confirm(*args, **kwargs):
    params = _lines(*args, **kwargs)
    if kwargs.get('yes'):
        params['yeslabel'] = kwargs['yes']
    if kwargs.get('no'):
        params['nolabel'] = kwargs['no']
    return xbmcgui.Dialog().yesno(**params)


def message(msg, **kwargs):
    title = kwargs.get('title')
    icon = kwargs.get('icon')
    ttl = kwargs.get('ttl', 5)
    if title is None or icon is None:
        from .app import addon
        if title is None:
            title = addon.name
        if icon is None:
            icon = addon.icon
    xbmc.executebuiltin('XBMC.Notification("%s","%s","%s","%s")' % (msg, title, 1000*ttl, icon))


def prompt(title=None, default=None):
    return _keyboard(False, title, default)


def password(title=None, default=None):
    return _keyboard(True, title, default)


def setting(addon=None):
    import xbmcaddon
    if not addon:
        addon = sys.argv[0].replace('plugin://', '').replace('/', '')
    xbmcaddon.Addon(id=addon).openSettings()


def browse():
    # TODO: Create method browse
    pass


def captcha(url, width, height, title=None, headers=None, is_number=False):
    from .net import http
    if not headers:
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Charset': 'utf-8,*;q=0.3',
            'Accept-Encoding': 'gzip,deflate',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.57 Safari/537.17'
        }

    try:
        response = http.get(url, headers=headers)
    except http.exceptions.RequestException, e:
        return None

    import tempfile
    filename = tempfile.gettempdir() + '/captcha'
    file(filename, 'wb').write(response.content)

    # TODO: Change methods for Window in Capthca
    win = window.window()
    image = control.Image(win.getWidth()/2 - int(width/2), 20, width, height, filename)
    win.addControl(image)
    code = number(title=_title(title)) if is_number else prompt(title=_title(title))
    win.removeControl(image)
    return code



class Text(window.XMLDialog):
    def __init__(self, *args, **kwargs):
        self._title = _title(kwargs.get('title'))
        self._body = kwargs.get('body', '')

    def onInit(self):
        self.getControl(1).setLabel(self._title)
        self.getControl(5).setText(self._body)

    def onFocus(self, control):
        pass

def text(title=None, body=None):
    win = Text('DialogTextViewer.xml', sys.argv[0], title=title, body=body)
    win.doModal()
    del win



class Progress(object):
    progress = None
    title = ''
    lines = [None, None, None]
    count = None
    total = None
    is_cancel = False

    instance = None

    def __new__(cls):
        if cls.instance is None:
            cls.instance = super(Progress, cls).__new__(cls)
        return cls.instance

    def __call__(self, *args):
        self.close()

        self.title, self.count, self.total, self.is_cancel = '', 0, 0, False

        args_str = [x for x in args if isinstance(x, basestring)]
        if args_str:
            self.title = args_str[0]
            self.lines = [(args_str[i + 1] if i < len(args_str) - 1 else None) for i in range(0,3)]

        args_num = [x for x in args if isinstance(x, (int, float))]
        if args_num:
            self.total = args_num[0]


    def render(self, *args, **kwargs):
        if self.progress and self.progress.iscanceled():
            self.is_cancel = True
            self.close()

        if self.is_cancel:
            return False

        args_str = [x for x in args if isinstance(x, basestring)]
        if args_str:
            self.lines = [(args_str[i] if i < len(args_str) else None) for i in range(0,3)]

        if 'line1' in kwargs:
            self.lines[0] = kwargs['line1']
        if 'line2' in kwargs:
            self.lines[1] = kwargs['line2']
        if 'line3' in kwargs:
            self.lines[2] = kwargs['line3']

        args_num = [x for x in args if isinstance(x, (int, float))]
        if args_num:
            if args_num[0] < 0:
                self.count -= args_num[0]
            else:
                self.count = args_num[0]
            if len(args_num) > 1:
                self.total = args_num[1]

        if self.count and self.count == self.total:
            percent = 100
        elif not self.total:
            percent = 0
        else:
            percent = int(float(self.count) / (float(self.total) / 100.0))

        if not self.progress:
            self.progress = xbmcgui.DialogProgress()
            self.progress.create(self.title)

        self.progress.update(percent, *[x for x in self.lines if x is not None])

        return True

    def close(self):
        if self.progress:
            self.progress.close()
            self.progress = None

# TODO: Check progress object
progress = Progress()


"""
class TextXML(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.parent = kwargs['parent']

    def onInit(self):
        self.title = self.getControl(1)
        self.text = self.getControl(5)
        self.parent._oninit()

    def onFocus(self, control):
        pass

    def onAction(self, action):
        id = action.getId()
        if id == 1:
            self.parent.onleft()
        elif id == 2:
            self.parent.onright()
        elif id in (9, 10, 92):
            if not self.parent.onclose():
                self.close()



class Text:
    def __init__(self, *args):
        if len(args) > 1:
            self._title, self._text = args[0], args[1]
        elif len(args) > 0:
            self._title, self._text = None, args[1]

        self.window = TextXML('DialogTextViewer.xml', sys.argv[0], parent=self)
        self.window.doModal()
        del self.window

    def title(self, title):
        self.window.title.setLabel(title)

    def text(self, text):
        self.window.text.setText(text)

    def _oninit(self):
        if self._title:
            self.title(self._title)
        if self._text:
            self.text(self._text)
        self.oninit()

    # EVENT

    def oninit(self):
        pass

    def onleft(self):
        pass

    def onright(self):
        pass

    def onclose(self):
        pass


class Gui:
    progress = Progress()
    def text(self, *args):
        Text(*args)

"""
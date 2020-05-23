# -*- coding: utf-8 -*-

__author__ = 'hal9000'
__all__ = ['re', 'clear', 'html']

import htmlentitydefs
import re as regex

class RE(object):
    _compile = {}
    _flag = {'I': regex.I, 'L': regex.L, 'M': regex.M, 'S': regex.S, 'U': regex.U, 'X': regex.X}

    def __call__(self, pattern, string, flag=None):
        return self.find(pattern, string, flag)

    def find(self, pattern, string, flag=None):
        r = self._build(pattern, flag=None).search(string)
        return [x.strip() for x in r.groups()] if r else None

    def all(self, pattern, string, flag=None):
        r = self._build(pattern, flag=None).findall(string)
        if not r:
            return []
        return r if isinstance(r[0], tuple) else [(x,) for x in r]

    def _build(self, pattern, flag=None):
        flag = 'US' if flag is None else flag.upper()

        key = u':'.join([flag, pattern])
        try:
            return self._compile[key]
        except KeyError:
            self._compile[key] = regex.compile(pattern, reduce(lambda r,f: r|f, [self._flag[x] for x in flag]))
            return self._compile[key]


re = RE()


class Clear:
    _compile = dict(
        space  = regex.compile('[ ]{2,}', regex.U|regex.S),
        cl     = regex.compile('[\n]{2,}', regex.U|regex.S),
        br     = regex.compile('<\s*br[\s/]*>', regex.U|regex.S),
        inner  = regex.compile('<[^>]*>[^<]+<\s*/[^>]*>', regex.U|regex.S),
        html   = regex.compile('<[^>]*>', regex.U|regex.S),
        entity = regex.compile('&#?\w+;', regex.U)
    )

    _unsupport_chars = {'&#151;': '-'}

    def text(self, text, inner=False):
        text = self._unsupport(text).replace(u'\r', u'\n')
        text = self._compile['br'].sub(u'\n', text)
        if inner:
            text = self._compile['inner'].sub(u'', text)
        text = self._compile['html'].sub(u'', text)
        text = self.char(text)
        text = self._compile['space'].sub(u' ', text)
        return self._compile['cl'].sub(u'\n', text).strip()
    
    def string(self, text, space=u''):
        return self.text(text).replace(u'\n', space).strip()
    
    def char(self, text):
        return self._compile['entity'].sub(self._unescape, self._unsupport(text))
    
    def _unsupport(self, text):
        for tag, value in self._unsupport_chars.iteritems():
            text = text.replace(tag, value)
        return text
    
    def _unescape(self, m):
        text = m.group(0)
        if text[:2] == u"&#":
            try:
                if text[:3] == u"&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text


clear = Clear()


def html(string):
    from bs4 import BeautifulSoup
    return BeautifulSoup(string, 'html.parser')

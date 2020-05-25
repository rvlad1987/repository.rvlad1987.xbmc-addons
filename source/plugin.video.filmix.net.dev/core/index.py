# -*- coding: utf-8 -*-

import xbmcup.app, cover
from auth import Auth

class Index(xbmcup.app.Handler):
    def handle(self):
        Auth().autorize()
        self.item(xbmcup.app.lang[30112], self.link('search'),                        folder=True, icon=cover.search)
        self.item(xbmcup.app.lang[30120], self.link('filter', {'window' : ''}),       folder=True, icon=cover.search)

        if(xbmcup.app.setting['is_logged'] == 'true'):
            self.item(xbmcup.app.lang[30146], self.link('bookmarks',  {'url' : ''}),       folder=True, icon=cover.bookmarks)
            self.item(xbmcup.app.lang[30173], self.link('collections',  {'url' : ''}),       folder=True, icon=cover.collections)
            self.item(xbmcup.app.lang[30175], self.link('my_news',  {'url' : ''}),       folder=True, icon=cover.news)
            self.item(xbmcup.app.lang[30162], self.link('watch_later',  {'url' : ''}),       folder=True, icon=cover.watchlater)

            self.item(xbmcup.app.lang[30160], self.link('null', {}),       folder=False, icon=cover.empty)

        self.item(' - '+xbmcup.app.lang[30114], self.link('list', {'dir' : 'films'}),       folder=True, icon=cover.films)
        self.item(' - '+xbmcup.app.lang[30115], self.link('list', {'dir' : 'serialy'}),     folder=True, icon=cover.serialy)
        self.item(' - '+xbmcup.app.lang[30116], self.link('list', {'dir' : 'multfilmy'}),   folder=True, icon=cover.films)
        self.item(' - '+xbmcup.app.lang[30117], self.link('list', {'dir' : 'multserialy'}),   folder=True, icon=cover.serialy)

        if(xbmcup.app.setting['hide_donate'] == 'false'):
            self.item(xbmcup.app.lang[37000], self.link('donate', {'hide' : '1'}), folder=True, cover=cover.info, icon=cover.info)
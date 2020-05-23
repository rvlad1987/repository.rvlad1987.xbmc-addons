# -*- coding: utf-8 -*-

import urlparse, urllib,sys, xbmc,traceback

#process STRM files

split_vars = sys.argv[0].split('/')
if(split_vars[-1] == 'play'):
    split_vars[-1] = ''
    params = urlparse.parse_qs(sys.argv[2].replace('?', ''))
    try:
        test = params['folder']
    except:
        params['folder'] = ['']
    sys.argv[0] = '/'.join(split_vars)
    toplay = '{"url": ["resolve", "resolve", [{"page_url": "'+params['page_url'][0]+'", "resolution": "'+params['resolution'][0]+'", "file": "'+params['file'][0]+'", "folder" : "'+params['folder'][0]+'"}]], "source": "item", "folder": false, "parent" : {}}'
    sys.argv[2] = '?json'+urllib.quote_plus(toplay)

# process United Search request
try:
    search_vars = sys.argv[2].split('?')
    search_vars = search_vars[-1].split('&')
    if search_vars[0] == 'usearch=True':
        params = urlparse.parse_qs(sys.argv[2].replace('?', ''))
        united_search = '{"url": ["link", "search", [{"vsearch": "'+(params['keyword'][0])+'", "usersearch": "'+(params['keyword'][0])+'", "page": 0, "is_united" : "1"}]], "source": "item", "folder": true, "parent" : {}}'
        sys.argv[2] = '?json'+urllib.quote_plus(united_search)
except:
    xbmc.log(traceback.format_exc())


import xbmcup.app, sys
from core.index import Index
from core.list import MovieList, BookmarkList, QualityList, SearchList, Watch_Later, My_News, Collections
from core.http import ResolveLink
from core.filter import Filter
from core.context import ContextMenu
from core.donate import Donate
from core.strm_generator import SaveMovieHandler

# log = open(xbmcup.system.fs('sandbox://myprog.log').decode('utf-8'), "a")
# sys.stdout = log

plugin = xbmcup.app.Plugin()

plugin.route(None, Index)
plugin.route('list', MovieList)
plugin.route('quality-list', QualityList)
plugin.route('search', SearchList)
plugin.route('filter', Filter)
plugin.route('bookmarks', BookmarkList)
plugin.route('watch_later', Watch_Later)
plugin.route('my_news', My_News)
plugin.route('collections', Collections)
plugin.route('context', ContextMenu)
plugin.route('resolve', ResolveLink)
plugin.route('donate', Donate)
plugin.route('generate-strm', SaveMovieHandler)

plugin.run()
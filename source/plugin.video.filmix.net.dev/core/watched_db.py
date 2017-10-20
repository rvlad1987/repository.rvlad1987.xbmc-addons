# -*- coding: utf-8 -*-

import os, re, sys, json, urllib, hashlib, traceback
import xbmcup.app, xbmcup.db, xbmcup.system, xbmcup.net, xbmcup.parser, xbmcup.gui
import xbmc, cover, xbmcplugin, xbmcgui
#from http import HttpData
from auth import Auth
from common import Render
from defines import *

try:
    from sqlite3 import dbapi2 as sqlite
except:
    from pysqlite2 import dbapi2 as sqlite

CACHE = xbmcup.db.Cache(xbmcup.system.fs('sandbox://'+CACHE_DATABASE))
SQL = xbmcup.db.SQL(xbmcup.system.fs('sandbox://'+CACHE_DATABASE))

class Watched(xbmcup.app.Handler):
    def __init__(self):
        SQL.set('CREATE TABLE IF NOT EXISTS watched(id INTEGER PRIMARY KEY AUTOINCREMENT, movie_id INTEGER, season INTEGER, episode INTEGER, UNIQUE(movie_id, season, episode) ON CONFLICT IGNORE)')

    def set(self, movie_id, season, episode):
        SQL.set('INSERT INTO watched (movie_id, season, episode) VALUES (%i,%i,%i)' % (movie_id, season, episode))

    def set_all_episodes(self, movie_id):
        print SQL.get('SELECT * FROM watched ORDER BY movie_id DESC, season DESC, episode DESC')
        pass

    def get_not_watched(self):
        print SQL.get('SELECT id, movie_id, season, episode FROM watched ORDER BY movie_id DESC, season DESC, episode DESC')
        pass
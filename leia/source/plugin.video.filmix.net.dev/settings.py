# -*- coding: utf-8 -*-

import sys, xbmc, xbmcaddon

sys.argv[0] = 'plugin.video.filmix.net.dev'#PLUGIN_ID
import os, xbmcup.app, xbmcup.system, xbmcup.db, xbmcup.gui
from core.defines import *

from core.auth import Auth
import core.cover


# log = open(xbmcup.system.fs('sandbox://myprog.log').decode('utf-8'), "a")
# sys.stdout = log

def clear_cache_db():
    CACHE = xbmcup.db.Cache(xbmcup.system.fs('sandbox://'+CACHE_DATABASE))
    CACHE.flush()
    SQL = xbmcup.db.SQL(xbmcup.system.fs('sandbox://'+CACHE_DATABASE))
    try:
        SQL.set('DELETE FROM search')
    except:
        pass


def show_message(key):
    xbmcup.gui.message( xbmcup.app.lang[key].encode('utf-8') )


def openAddonSettings(addonId, id1=None, id2=None):
    xbmc.executebuiltin('Addon.OpenSettings(%s)' % addonId)
    if id1 != None:
        xbmc.executebuiltin('SetFocus(%i)' % (id1 + 200))
    if id2 != None:
        xbmc.executebuiltin('SetFocus(%i)' % (id2 + 100))

if(sys.argv[1] == 'clear_cache'):
    clear_cache_db()
    show_message(32001)

if(sys.argv[1] == 'login'):
    is_logged = Auth().autorize()
    if(is_logged):
        show_message(32002)
    else:
        show_message(32003)
    openAddonSettings(PLUGIN_ID, 1, 0)


if(sys.argv[1] == 'logout'):
    Auth().reset_auth(True)
    show_message(32004)
    openAddonSettings(PLUGIN_ID, 1, 0)


if(sys.argv[1] == 'apply_list_settings'):
    clear_cache_db()
    show_message(32005)
    openAddonSettings(PLUGIN_ID, 1, 0)


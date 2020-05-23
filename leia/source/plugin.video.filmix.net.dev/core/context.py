# -*- coding: utf-8 -*-

import os, re, sys, json, urllib, hashlib, traceback
import xbmcup.app, xbmcup.db, xbmcup.system, xbmcup.net, xbmcup.parser, xbmcup.gui
import xbmc, cover, xbmcplugin, xbmcgui

from http import HttpData
from auth import Auth
from wmodal import MovieInfo
from common import Render
from defines import *
from watched_db import Watched

class ContextMenu(xbmcup.app.Handler, HttpData, Render):

    def handle(self):
        self.is_logged = Auth().autorize()
        try:
            params = self.argv[0]
        except:
            params = {}

        try:
            eval('self.'+params['action'])(params)
        except:
            xbmcup.gui.message('Addon internal error', title='Call to undefined method ContextMenu::%s()' % params['action'])
            print traceback.format_exc()

    def add_bookmark(self, params):

        if not self.is_logged:
            xbmcup.gui.message(xbmcup.app.lang[30153].encode('utf-8'))
            return False
        resp = self.ajax('%s/engine/ajax/favorites.php?fav_id=%s&action=plus&skin=Filmix&alert=0' % (SITE_URL, params['id']))
        try:
            if(resp.find("doFavorites('%s', 'minus', 0);" % params['id']) != -1):
                xbmcup.gui.message(xbmcup.app.lang[30150].encode('utf-8'))
            else:
                xbmcup.gui.message(xbmcup.app.lang[30154].encode('utf-8'))
                # print resp
        except:
            pass

    def del_bookmark(self, params):
        resp = self.ajax('%s/engine/ajax/favorites.php?fav_id=%s&action=minus&skin=Filmix&alert=0' % (SITE_URL, params['id']))
        try:
            resp = json.loads(resp)
            if(resp.find("doFavorites('%s', 'plus', 0);" % params['id']) != -1):
                xbmcup.gui.message(xbmcup.app.lang[30151].encode('utf-8'))
            else:
                xbmcup.gui.message(xbmcup.app.lang[30155].encode('utf-8'))
        except:
            pass
        xbmc.executebuiltin('Container.Refresh()')

    def add_watch_later(self, params):

        if not self.is_logged:
            xbmcup.gui.message(xbmcup.app.lang[30169].encode('utf-8'))
            return False

        post_data={'action' : 'add', 'post_id' : params['id']}
        resp = self.ajax('%s/engine/ajax/watch_later.php' % SITE_URL, post_data)
        try:
            if(resp.find("watch_later('%s',false);" % params['id']) != -1):
                xbmcup.gui.message(xbmcup.app.lang[30165].encode('utf-8'))
            else:
                xbmcup.gui.message(xbmcup.app.lang[30167].encode('utf-8'))
        except:
            pass

    def del_watch_later(self, params):
        post_data={'action' : 'rm', 'post_id' : params['id']}
        resp = self.ajax('%s/engine/ajax/watch_later.php' % SITE_URL, post_data)
        try:
            if(resp.find("watch_later('%s',true);" % params['id']) != -1):
                xbmcup.gui.message(xbmcup.app.lang[30166].encode('utf-8'))
            else:
                xbmcup.gui.message(xbmcup.app.lang[30168].encode('utf-8'))
        except:
            pass
        xbmc.executebuiltin('Container.Refresh()')

    def show_movieinfo(self, params):
        # xbmc.executebuiltin("RunScript(script.extendedinfo,info=%s,name=%s)" % ("extendedinfo",params['movie']['name']))
        movieInfo = self.get_modal_info(params['movie']['url'])
        if(movieInfo['error']):
            xbmcup.gui.message(xbmcup.app.lang[34031].encode('utf8'))
            return

        skin_dir = xbmc.getSkinDir()
        if skin_dir == 'skin.estuary':
            movieinfo_xml = 'movieinfo_estuary.xml'
        else:
            movieinfo_xml = 'movieinfo.xml'
        w = MovieInfo(movieinfo_xml, xbmcup.app.addon['path'], "Default")
        w.doModal(movieInfo)

    def add_episodes_to_watched_db(self, params):
        movieInfo = self.get_movie_info( params['movie']['url'] )
        if Watched().set_watched_all_episodes( int(params['movie']['id']), movieInfo ):
            xbmcup.gui.message(xbmcup.app.lang[30172].encode('utf-8'))
        else:
            xbmcup.gui.message(xbmcup.app.lang[30171].encode('utf-8'))
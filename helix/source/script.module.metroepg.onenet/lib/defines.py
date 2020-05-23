# -*- coding: utf-8 -*-

# Copyright © 2017 Rudnitskii Vlad <rvlad1987@mail.ru>
# License: GPL-2
# Website: https://github.com/rvlad1987/repository.rvlad1987.xbmc-addons

from sys import platform

AUTOSTART_TIMEOUT = 10000
M3U_URL           = 'http://onenet.by/pl.m3u'
JTV_URL           = 'http://onenet.by/tv/jtv.zip'
PLUGIN_ID         = 'script.module.metroepg.onenet'
PVR_ID            = 'pvr.iptvsimple'
FRIENDLY_NAME     = 'МетроEPG'
LOGO_PACK_URL     = 'https://github.com/rvlad1987/repository.rvlad1987.xbmc-addons/raw/master/resources/logo_pack.zip'

IS_WIN            = ( (platform == 'win32') or (platform == 'win64') )

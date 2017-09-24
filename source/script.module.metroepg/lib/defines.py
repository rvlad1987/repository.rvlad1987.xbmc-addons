# -*- coding: utf-8 -*-
from sys import platform

M3U_URL         = 'https://cabinet.metro-set.ru/get/iptv.m3u.php'
JTV_URL         = 'http://www.metro-set.ru/jtv.zip'
PLUGIN_ID       = 'script.module.metroepg'
PVR_ID          = 'pvr.iptvsimple'
FRIENDLY_NAME   = 'МетроEPG'

IS_WIN          = ( (platform == 'win32') or (platform == 'win64') )

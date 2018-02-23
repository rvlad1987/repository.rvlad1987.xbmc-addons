# -*- coding: utf-8 -*-
import xbmcup.app

s_https = ''
if xbmcup.app.setting['use_https'] == 'true': s_https = 's'

SITE_DOMAIN = xbmcup.app.setting['site_domain']
SITE_URL = 'http' + s_https + '://' + SITE_DOMAIN
COLLECTIONS_URL = SITE_URL + '/playlists/my'
PLUGIN_ID = 'plugin.video.filmix.net.dev'
CACHE_DATABASE = 'filmix.cache.db'
COOKIE_FILE = 'filmix_cookie.txt'

SORT_TYPES = ['view', 'rate', 'new']
QUALITYS = [None, '360', '480', '720', '1080']
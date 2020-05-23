# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from core.strm_generator import WatchService
import xbmcup.app

if __name__ == '__main__':
    if xbmcup.app.setting['start_strm_service'] == 'true':
        WatchService().run()
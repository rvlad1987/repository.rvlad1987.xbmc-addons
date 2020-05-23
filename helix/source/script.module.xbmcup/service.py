# -*- coding: utf-8 -*-

__author__ = 'hal9000'

import os
import sys

def run():
    sys.path = [os.path.dirname(__file__) + '/lib'] + sys.path
    from xbmcup.cache import CacheServer
    CacheServer().run()

if __name__ == '__main__':
    run()

# -*- coding: utf-8 -*-

__author__ = 'rvlad1987'

import os
import sys
import xbmc

def run():
    sys.path = [os.path.dirname(__file__) + '/lib'] + sys.path
    from core import MetroEPG
    MetroEPG().run()

if __name__ == '__main__':
    run()

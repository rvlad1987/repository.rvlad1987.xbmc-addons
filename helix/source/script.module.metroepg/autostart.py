# -*- coding: utf-8 -*-

# Copyright © 2017 Rudnitskii Vlad <rvlad1987@mail.ru>
# License: GPL-2
# Website: https://github.com/rvlad1987/repository.rvlad1987.xbmc-addons

__author__ = 'rvlad1987'

import os
import sys

def run():
    sys.path = [os.path.dirname(__file__) + '/lib'] + sys.path
    from core import MetroEPG
    MetroEPG().run(autostart=True)

if __name__ == '__main__':
    run()

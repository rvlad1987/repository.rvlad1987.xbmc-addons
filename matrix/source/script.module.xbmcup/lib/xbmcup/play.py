# -*- coding: utf-8 -*-

__author__ = 'hal9000'
__all__ = ['clean', 'sfx', 'Player']

import xbmc

# TODO: Create our class Player
from xbmc import Player

def clean(path, folder=False):
    return xbmc.getCleanMovieTitle(path, folder)

def sfx(filename):
    xbmc.playSFX(filename)

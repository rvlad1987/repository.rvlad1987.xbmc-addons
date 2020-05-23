# -*- coding: utf-8 -*-

__author__ = 'hal9000'
__all__ = ['name', 'condition', 'label', 'image', 'has', 'screenshot']

import xbmc

name = xbmc.getSkinDir()

def condition(cond):
    return True if xbmc.getCondVisibility(cond) else False

def label(tag):
    return xbmc.getInfoLabel(tag)

def image(tag):
    return xbmc.getInfoImage(tag)

def has(filename):
    return True if xbmc.skinHasImage(filename) else False

def screenshot(width, height, filename=None):
    cap = xbmc.RenderCapture()
    cap.capture(width, height, 2)
    state = 0
    while True:
        state = cap.getCaptureState()
        if state != 0:
            break
        cap.waitForCaptureStateChangeEvent()

    # TODO: Create the convert from BGRA to RGBA

    if state == 4:
        return None
    if filename is None:
        return cap.getImage()
    file(filename, 'wb').write(cap.getImage())
    return True

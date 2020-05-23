# -*- coding: utf-8 -*-

__author__ = 'hal9000'
__all__ = ['Window', 'XML', 'Dialog', 'DialogXML', 'wid', 'did', 'window', 'dialog']

from xbmcgui import Window, WindowDialog, WindowXML, WindowXMLDialog, getCurrentWindowId, getCurrentWindowDialogId

#ACTION_PREVIOUS_MENU = (9, 10, 92, 216, 247, 257, 275, 61467, 61448)

XML = WindowXML
Dialog = WindowDialog
XMLDialog = WindowXMLDialog

def wid():
    return getCurrentWindowId()

def did():
    return getCurrentWindowDialogId()

def window():
    id = wid()
    return Window(id) if id else None

def dialog():
    id = did()
    return Dialog(id) if id else None

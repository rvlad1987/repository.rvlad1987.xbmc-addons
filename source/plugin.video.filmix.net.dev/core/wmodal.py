# -*- coding: utf-8 -*-

import sys, urllib, urllib2, re, os, cookielib, traceback, datetime
import xbmc, xbmcgui, xbmcaddon, xbmcup
from http import HttpData

KEY_BUTTON_BACK = 275
KEY_KEYBOARD_ESC = 61467
KEY_BUTTON_LEFT = [61570,169]#[keyboard,yatse]
KEY_BUTTON_RIGHT = [61571,168]
KEY_BUTTON_UP = [61568,166]
KEY_BUTTON_DOWN = [61569,167]
ACTION_PREVIOUS_MENU = 10
ACTION_NAV_BACK = 92

class MovieInfo(xbmcgui.WindowXMLDialog, HttpData):
    scroll_pos = 0
    row_count = 0
    def formatRating(self, rating):
        ratingcolor = 'green'
        rating = int(rating)
        if(rating < 0):
             ratingcolor = 'red'
        return '[COLOR blue]Рейтинг:[/COLOR] [COLOR '+ratingcolor+']'+str(rating)+'[/COLOR]'

    def onInit(self):
        print "onInit(): Window Initialized"
        # print self.movieInfo
        self.getControl(1).setLabel(self.movieInfo['title'])
        self.getControl(32).setText(self.movieInfo['desc'])
        self.getControl(31).setImage(self.movieInfo['poster'])

        self.trailer = self.getControl(33)
        if(self.movieInfo['trailer'] != False):
            self.trailer.setEnabled(True)
        else:
            self.trailer.setEnabled(False)

        self.setFocus(self.getControl(22))


    def onAction(self, action):
        buttonCode =  action.getButtonCode()
        #print buttonCode
        if action in [ACTION_NAV_BACK, ACTION_PREVIOUS_MENU, KEY_BUTTON_BACK, KEY_KEYBOARD_ESC]: self.close()
        if buttonCode in KEY_BUTTON_LEFT and self.movieInfo['trailer'] != False: self.setFocus(self.getControl(33))
        if buttonCode in KEY_BUTTON_RIGHT: self.setFocus(self.getControl(22))
        if buttonCode in KEY_BUTTON_UP:
            self.scroll_pos -= 1
            if self.scroll_pos < 0: self.scroll_pos = 0
            self.getControl(32).scroll(self.scroll_pos)
        if buttonCode in KEY_BUTTON_DOWN:
            self.scroll_pos += 1
            if self.scroll_pos > self.row_count + 10: self.scroll_pos = self.row_count
            self.getControl(32).scroll(self.scroll_pos)

    def onClick(self, controlID):
        if (controlID == 2 or controlID == 22):
            self.close()

        if(controlID == 33):
            self.close()
            self.listitem = xbmcgui.ListItem(xbmcup.app.lang[34028]+' '+self.movieInfo['title'], iconImage=self.movieInfo['poster'], thumbnailImage=self.movieInfo['poster'])
            link = self.get_trailer(self.movieInfo['trailer'])
            if(link != False):
                xbmc.Player().play(link, self.listitem)
            else:
                xbmcup.gui.message(xbmcup.app.lang[34032].encode('utf8'))

    def onFocus(self, controlID):
        print "onFocus(): control %i" % controlID
        pass


    def doModal(self, movieInfo):
        self.movieInfo = movieInfo
        self.row_count = len(re.findall(r"[\n']+?", movieInfo['desc']))
        xbmcgui.WindowXMLDialog.doModal(self)
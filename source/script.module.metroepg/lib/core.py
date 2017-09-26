# -*- coding: utf-8 -*-

# Copyright © 2017 Rudnitskii Vlad <rvlad1987@mail.ru>
# License: GPL-2
# Website: https://github.com/rvlad1987/repository.rvlad1987.xbmc-addons

__author__ = 'rvlad1987'
__all__ = ['MetroEPG']

import os, io
import sys, urllib, zipfile

import xbmc, xbmcaddon, xbmcgui

import math

from datetime import datetime, timedelta
from time import strftime

from defines import *
from jtv import *

class Base:
    _log_enabled     = False
    
    _addon           = xbmcaddon.Addon(id = PLUGIN_ID)
    _addon_patch     = xbmc.translatePath(_addon.getAddonInfo('path'))
    _tmp_path        = xbmc.translatePath( os.path.join( "special://temp", PLUGIN_ID ) )
    _addon_data_path = xbmc.translatePath( os.path.join( "special://profile/addon_data", PLUGIN_ID) )
    
    
    if IS_WIN:
        _addon_patch = _addon_patch.decode('utf-8')
        _tmp_path     = _tmp_path.decode('utf-8')
        _addon_data_path = _addon_data_path.decode('utf-8')    
    
    if not os.path.exists(_tmp_path): os.makedirs(_tmp_path)
    
    _xmltv_file_path = os.path.join( _addon_data_path, 'xmltv.xml' )
    _icon_           = _addon.getAddonInfo( 'icon' )
    
    _epgTimeShift    = '0.000000'
    _m3uUrl          = M3U_URL

    def lang(self, key):
        return Base._addon.getLocalizedString(id=key).encode('utf-8')

    def vbool(self, value):
        if value == 'true':
            return True
        else:
            return False

class MetroEPG(Base):
    def __init__(self):
        self.setting = Setting()
        
        if self._log_enabled:
            log = open(self._tmp_path+'_log.txt','ab')
            sys.stdout = log
        
        try:    
            Base._iptv_simple_addon = xbmcaddon.Addon(id=PVR_ID)
        except:
            self.notification(message=self.lang(34003), time=5000)
            sys.exit()
        
        Base._PVR_data_path = check_win_path( xbmc.translatePath( os.path.join( "special://profile/addon_data", PVR_ID) ) )
    
    def run(self):
        if sys.argv[1] == 'start':
            if not self.setting.enabled: sys.exit()
            
            if not os.path.exists(self._addon_data_path): os.makedirs(self._addon_data_path)

            if self.setting.onstart:
                self.addjob(s=30)
            else:        
                try:
                    dtsettings=datetime.strptime(self.setting.nextstart, "%Y-%m-%d %H:%M:%S") 
                except:
                    dtsettings=datetime.now()
                    self.setting.set("nextstart", dtsettings.strftime('%Y-%m-%d %H:%M:%S'))
                
                if (datetime.now() >= dtsettings):
                    self.addjob()
                else:
                    nextstart = dtsettings - datetime.now()
                    nextstarts= nextstart.total_seconds()
                    h=int(nextstarts//3600)
                    m=int((nextstarts//60)%60)
                    self.addjob( h, m, 0 )
        
        elif sys.argv[1] == 'chsettings':
            self.deljob()
            if self.setting.enabled: self.addjob()

        elif sys.argv[1] == 'onTimer':    
            getjtv( JTV_URL, self._tmp_path, '1', self._m3uUrl, self._xmltv_file_path, self.setting.codepage, not self.setting.notalert)
            
            nextstart = datetime.now()+timedelta(days=self.setting.interval)
            self.setting.set("nextstart", nextstart.strftime('%Y-%m-%d %H:%M:%S'))
            self.deljob()
            self.addjob(self.setting.interval*24,0,0)
            
            if not self.setting.notalert: self.notification( self.lang(34002) )
            
        elif sys.argv[1] == 'update':
            self.addjob(s=1)

        elif sys.argv[1] == 'update_icon':
            xbmc.executebuiltin('PVR.SearchMissingChannelIcons')
            self.notification( self.lang(34001) )
            
        elif sys.argv[1] == 'chsettingsiptv':
            self.deljob()
            self.downloadlogo()
            if self.setting.enabled: self.addjob(s=1)
            self.setting.set_iptv_setting()

        elif sys.argv[1] == 'downloadlogo':
            self.downloadlogo()

        else:
            self._addon.openSettings()
    
    def notification(self, message, title = FRIENDLY_NAME, time = 20):
        xbmc.executebuiltin('XBMC.Notification(%s ,%s, %i, %s)' % (title, message, time, self._icon_))
    
    def addjob(self, h=0, m=0, s=5):
        xbmc.executebuiltin('XBMC.AlarmClock(metroepg,XBMC.RunScript(' + PLUGIN_ID + ', onTimer),%s:%s:%s ,silent)'%(h,m,s))
    
    def deljob(self):
        xbmc.executebuiltin('XBMC.CancelAlarm(metroepg, True)')
    
    def downloadlogo(self):
        def DownloaderClass(url,dest, dp):
            urllib.urlretrieve(url,dest,lambda nb, bs, fs, url=url: _pbhook(nb,bs,fs,url,dp))
         
        def _pbhook(numblocks, blocksize, filesize, url=None,dp=None):
            try:
                percent = min((numblocks*blocksize*100)/filesize, 100)
                dp.update(percent)
            except:
                percent = 100
                dp.update(percent)
        
        out_file = os.path.join(self._tmp_path, 'downloadlogo.zip')
        
        dp = xbmcgui.DialogProgressBG()
        dp.create( FRIENDLY_NAME, self.lang(34011) )
        
        DownloaderClass( LOGO_PACK_URL, out_file, dp)
        
        zip = zipfile.ZipFile(out_file, 'r')
        zip_namelist = zip.namelist()
        
        dp.update(0, message=lang(34012) )
        i_per = 1
        zip_namelist_count = len(zip_namelist)

        #f_logo_path = check_win_path( self.setting.logo_path )
        
        for name in zip_namelist:
            dp.update( (i_per * 100) // zip_namelist_count )
            i_per += 1
            
            try:
                unicode_name = name.decode('UTF-8').encode('UTF-8')
            except UnicodeDecodeError:
                if IS_WIN:
                    unicode_name = name.decode('cp866')
                else:
                    unicode_name = name.encode('utf-8')
            
            f = open( os.path.join( self.setting.logo_path, unicode_name), 'wb')
            f.write(zip.read(name))
            f.close()            

        dp.close()        
        zip.close()
        
        if IS_WIN: out_file = out_file.encode('utf-8')
        
        try:
            os.remove(out_file)
        except:
            print 'Can\'t delete zip ...'
        
        self.notification( self.lang(34010) )

class Setting(Base):
    def __init__(self):
        self.read_setting()

    def get(self, key):
        return self._addon.getSetting(key)

    def set(self, key, value):
        return self._addon.setSetting(key, value)
    
    def get_xml_str(self, key, value):
        return '    <setting id="' + key + '" value="' + value + '" />\n'

    def set_iptv_setting(self):
        if not os.path.exists(Base._PVR_data_path): os.makedirs(Base._PVR_data_path)
        
        fname_setting = os.path.join(Base._PVR_data_path, 'settings.xml')
        fname_new_setting = os.path.join(Base._PVR_data_path, 'new_settings.xml')
        
        if IS_WIN:
            f_xmltv = Base._xmltv_file_path.encode('utf-8')
            f_logo  = self.logo_path.encode('utf-8')
        else:
            f_xmltv = Base._xmltv_file_path
            f_logo  = self.logo_path
        
        f_set = io.open(fname_new_setting , 'wb')
        f_set.write('<settings>\n')
        f_set.write( self.get_xml_str('epgCache',      'true') )
        f_set.write( self.get_xml_str('epgPath',       f_xmltv) )
        f_set.write( self.get_xml_str('epgPathType',   '0') )
        f_set.write( self.get_xml_str('epgTSOverride', 'false') )
        f_set.write( self.get_xml_str('epgTimeShift',  Base._epgTimeShift) )
        f_set.write( self.get_xml_str('epgUrl',        '') )
        f_set.write( self.get_xml_str('interval',      str(self.interval) ) )
        f_set.write( self.get_xml_str('logoBaseUrl',   '') )
        f_set.write( self.get_xml_str('logoFromEpg',   '0') )
        f_set.write( self.get_xml_str('logoPath',      f_logo) )
        f_set.write( self.get_xml_str('logoPathType',  '0') )
        f_set.write( self.get_xml_str('m3uCache',      'true') )
        f_set.write( self.get_xml_str('m3uPath',       '') )
        f_set.write( self.get_xml_str('m3uPathType',   '1') )
        f_set.write( self.get_xml_str('m3uUrl',        Base._m3uUrl) )
        f_set.write( self.get_xml_str('sep1',          '') )
        f_set.write( self.get_xml_str('sep2',          '') )
        f_set.write( self.get_xml_str('sep3',          '') )
        f_set.write( self.get_xml_str('startNum',      '1') )
        f_set.write('</settings>')
        
        f_set.close()
        
        if os.path.isfile(fname_setting): os.remove(fname_setting)
        os.rename(fname_new_setting, fname_setting)
        
        xbmc.executeJSONRPC( '{"jsonrpc":"2.0", "method":"Settings.SetSettingValue", "params":{"setting":"pvrmenu.iconpath","value":"%s"}, "id":1}' % f_logo.replace('\\','\\\\') ) 
        xbmcgui.Dialog().ok( FRIENDLY_NAME, self.lang(34008), self.lang(34009) )
        
    def read_setting(self):
        self.enabled        = self.vbool( self.get("enabled") )
        self.interval       = int( self.get("interval") )
        self.onstart        = self.vbool( self.get("onstart") )
        self.nextstart      = self.get("nextstart")
        self.notalert       = self.vbool( self.get("notalert") )
        self.codepage       = self.get("codepage").strip()
        self.myfolderlogo   = self.vbool( self.get("myfolderlogo") )
        
        if self.myfolderlogo:
            self.logo_path = os.path.join( Base._addon_data_path, 'logo_tv' )
        else:
            self.logo_path = self.get("otherfolderlogo").strip()
        
        if not os.path.exists(self.logo_path): os.makedirs(self.logo_path)
        
        city_ = self.get("city")
        
        if   '1' == city_:# Сургут
            self.city = 'sg'
            Base._epgTimeShift = '-5.000000'
            
        elif '2' == city_:# Радужный
            self.city = 'rd'
            Base._epgTimeShift = '-5.000000'
            
        elif '3' == city_:# Нефтеюганск
            self.city = 'nu'
            Base._epgTimeShift = '-5.000000'
            
        elif '4' == city_:# Стрежевой
            self.city = 'st'
            Base._epgTimeShift = '-7.000000'
            
        elif '5' == city_:# Ноябрьск         
            self.city = 'no'
            Base._epgTimeShift = '-5.000000'
            
        else:# Нижневартовск
            self.city = 'nv'
            Base._epgTimeShift = '-5.000000'
        
        Base._m3uUrl = M3U_URL + '?city=' + self.city.strip()

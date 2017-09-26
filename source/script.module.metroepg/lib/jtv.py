# -*- coding: utf-8 -*-

# Copyright © 3 Aug 2015 snakefishh, link: https://github.com/snakefishh/mnn-xbmc-repo/blob/master/script.service.jtvtoxmltv/resources/lib/jtv.py

# Copyright © 2017 Rudnitskii Vlad <rvlad1987@mail.ru>
# License: GPL-2
# Website: https://github.com/rvlad1987/repository.rvlad1987.xbmc-addons


import sys, os, shutil
import re, urllib, zipfile, StringIO

import xbmc, xbmcaddon, xbmcgui

import struct
from ctypes import *
from defines import *

from datetime import datetime

_DialogProgressBG = None
_addon            = xbmcaddon.Addon(id = PLUGIN_ID)

def lang(key):
    return _addon.getLocalizedString(id=key).encode('utf-8')

def check_win_path(path):
    if IS_WIN:
        return path.decode('utf-8')
    else:
        return path

def filetime_to_dt(ft):
    (s, ns100) = divmod(ft - 116444736000000000, 10000000)
    dt = datetime.utcfromtimestamp(s)
    dt = dt.replace(microsecond=(ns100 // 10))
    return dt
    
def jtvtoxml(jtvunzip_path, urljtv, locat, show_progress=False):
    global _DialogProgressBG

    jtvunzip_path = check_win_path(jtvunzip_path)

    if not os.path.exists(jtvunzip_path): os.makedirs(jtvunzip_path)

    if locat=='1':
        webFile = urllib.urlopen(urljtv)
        buf = webFile.read()
        sio = StringIO.StringIO(buf)
        zip = zipfile.ZipFile(sio, 'r')
    else:
        zip = zipfile.ZipFile(urljtv, 'r')
    
    zip_namelist = zip.namelist()

    if show_progress:
        _DialogProgressBG.update( message=lang(34007) )
        i_per = 1
        zip_namelist_count = len(zip_namelist)
    
    for name in zip_namelist:
        
        if show_progress:
            _DialogProgressBG.update( (i_per * 25) // zip_namelist_count )
            i_per += 1
        
        try:
            unicode_name = name.decode('UTF-8').encode('UTF-8')
        except UnicodeDecodeError:
            unicode_name = name.decode('cp866')#.decode('cp866').encode('UTF-8')
        
        f = open(jtvunzip_path+unicode_name, 'wb')
        f.write(zip.read(name))
        f.close()
    
    zip.close() 
    files = os.listdir(jtvunzip_path)
    jtvch=[]
    jtvprog=[]
    
    i_per = 1
    zip_namelist_count = len(files)
    
    for ndx in filter(lambda x: x.endswith('.ndx'), files):
    
        if show_progress:
            _DialogProgressBG.update( 25 + (((i_per * 25) // zip_namelist_count)) )
            i_per += 1

        fndx = open(jtvunzip_path+ndx, 'rb')
        pdt = os.path.splitext(ndx)[0]
        
        if IS_WIN:
            updt=pdt.encode('utf-8')
        else:
            updt=pdt
        
        pdt= pdt+'.pdt'
        fpdt = open(jtvunzip_path+pdt, 'rb')
        
        tmp1=[]
        try:
            x1 = fndx.read(2)
            for i in xrange(struct.unpack('h',x1)[0]):
                x1 = fndx.read(12)
                struc = struct.unpack('<hqH',x1)
                fpdt.seek(struc[2])
                len1 = fpdt.read(2)
                len1 = struct.unpack('h',len1)[0]
                x1 = fpdt.read(len1)
                
                ftm=struc[1]
                stm=str(filetime_to_dt(ftm)).replace('-','').replace(':','').replace(' ','')

                if not i==0:
                    tmp[1]=stm
                    tmp1.append(tmp)
                tmp = [stm, '', x1]

            tmp[1] = int(stm)+1
            tmp1.append(tmp)
        except Exception, e:
            print "JTV error: "+str(e)+" "+ndx
        finally:
            fndx.close()
            fpdt.close()
        jtvch.append(updt)
        jtvprog.append(tmp1)
        
    shutil.rmtree(jtvunzip_path)
    return (jtvch, jtvprog)

def getjtv(urljtv, tmp_path, locat, urlm3u, nxmltv, codepage, show_progress=False):
    global _DialogProgressBG
    
    if show_progress:
        _DialogProgressBG = xbmcgui.DialogProgressBG()
        _DialogProgressBG.create( FRIENDLY_NAME, lang(34005) )

    jtvunzip_path = xbmc.translatePath(os.path.join(tmp_path, 'jtvunzip/'))
    
    prg = jtvtoxml(jtvunzip_path, urljtv, locat, show_progress)
    
    xmlzag = '<?xml version="1.0" encoding="utf-8" ?>\n\n<tv>\n'
    xmlcan = '<channel id="%s"><display-name lang="ru">%s</display-name></channel>\n'
    xmlprog= '<programme start="%s" stop="%s" channel="%s"><title lang="ru">%s</title></programme>\n'

    xmltv=''
    xmltv2=''

    if show_progress:
        _DialogProgressBG.update( message=lang(34004) )

    webFile = urllib.urlopen(urlm3u)
    buf = webFile.read()
    qqq=re.compile(' tvg-name="(.*)" group-title="(.*)",(.*)').findall(buf)
    webFile.close()

    if show_progress:
        _DialogProgressBG.update( message=lang(34006) )
        i_per = 1
        channel_count = len(qqq)
 
    for key, gp, title in qqq:
        if show_progress:
            _DialogProgressBG.update( 50 + (((i_per * 50) // channel_count)) )
            i_per += 1

        try:
            ind = prg[0].index(key)            
        except:
            continue
        
        xmltv = xmltv + xmlcan % (str(ind), title.strip())
        
        for j in prg[1][ind]:
            xmltv2 = xmltv2+ xmlprog % (j[0], j[1], str(ind), j[2].decode(codepage).encode('UTF-8'))
    
    fxmltv = open(nxmltv,'w')
    fxmltv.write(xmlzag+xmltv+xmltv2+'\n</tv>')
    fxmltv.close()
    
    if show_progress:
        _DialogProgressBG.update(100)
        _DialogProgressBG.close()

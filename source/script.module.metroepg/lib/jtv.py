#!/usr/bin/python
# -*- coding: utf-8 -*-


import sys, os, shutil
import re, urllib, zipfile, StringIO

import xbmc

import struct
from ctypes import *

from datetime import datetime

_IS_WIN = ((sys.platform == 'win32') or (sys.platform == 'win64')) 

def check_win_path(path):
    if _IS_WIN:
        return path.decode('utf-8')
    else:
        return path

def filetime_to_dt(ft):
    (s, ns100) = divmod(ft - 116444736000000000, 10000000)
    dt = datetime.utcfromtimestamp(s)
    dt = dt.replace(microsecond=(ns100 // 10))
    return dt
    
def jtvtoxml(jtvunzip_path, urljtv, locat):
    jtvunzip_path = check_win_path(jtvunzip_path)

    if not os.path.exists(jtvunzip_path): os.makedirs(jtvunzip_path)

    if locat=='1':
        webFile = urllib.urlopen(urljtv)
        buf = webFile.read()
        sio = StringIO.StringIO(buf)
        zip = zipfile.ZipFile(sio, 'r')
    else:
        zip = zipfile.ZipFile(urljtv, 'r')
    
    for name in zip.namelist():
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
    for ndx in filter(lambda x: x.endswith('.ndx'), files):
    
        fndx = open(jtvunzip_path+ndx, 'rb')
        pdt = os.path.splitext(ndx)[0]
        
        if _IS_WIN:
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

def getjtv(urljtv, tmp_path, locat, urlm3u, nxmltv, codepage):
    jtvunzip_path = xbmc.translatePath(os.path.join(tmp_path, 'jtvunzip/'))
    
    prg = jtvtoxml(jtvunzip_path, urljtv, locat)
    
    xmlzag = '<?xml version="1.0" encoding="utf-8" ?>\n\n<tv>\n'
    xmlcan = '<channel id="%s"><display-name lang="ru">%s</display-name></channel>\n'
    xmlprog= '<programme start="%s" stop="%s" channel="%s"><title lang="ru">%s</title></programme>\n'

    xmltv=''
    xmltv2=''

    webFile = urllib.urlopen(urlm3u)
    buf = webFile.read()
    qqq=re.compile(' tvg-name="(.*)" group-title="(.*)",(.*)').findall(buf)
    webFile.close()

    for key, gp, title in qqq:
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

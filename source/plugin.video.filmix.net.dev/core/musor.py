# -*- coding: utf-8 -*-
# (c) matkin  2019

import string
#------------------------------------------------------------------
def Beg_End_Musor(data):
    c_data = data[:]
    Beg_End = []
    Ns = 0
    while Ns < len(c_data):
        s = c_data[Ns]
        if (s in "+0123456789"+string.ascii_letters): c_data = c_data.replace(c_data[Ns], "X", 1)
        Ns = Ns+1
    str_Symbols = ""
    Ns = 0
    while Ns < len(c_data):
        if (not (c_data[Ns] == "X")):
            str_Symbols = str_Symbols+c_data[Ns]
        Ns = Ns+1
    Ns = 0
    while True:
        if (str_Symbols[:Ns] in c_data):
             Ns = Ns+1
             continue
        Beg_End.append(str_Symbols[:Ns-1])
        break
    Ns = -1
    while True:
        if (str_Symbols[Ns:] in c_data):
            Ns = Ns-1
            continue
        Beg_End.append(str_Symbols[Ns+1:])
        break
    return Beg_End
#------------------------------------------------------------------
def Clear_Musor(data):
    c_data = data.replace("#2","")
    Beg_End = Beg_End_Musor(c_data)
    m_beg = Beg_End[0]
    m_end = Beg_End[1]
    Ns = 0
    index = 0
    while (index<100):
        index += 1
        Beg = c_data[Ns:].find(m_beg)
        if (Beg < 0): return c_data
        End = c_data[Ns:].find(m_end)
        t_data = c_data[Ns+Beg+len(m_beg):Ns+End]
        if (m_beg in t_data):
            Ns = Ns + 1
            continue
        else:
            c_data = c_data.replace(m_beg+t_data+m_end,"")
            Ns = 0
            continue
        break
    return None
#-------------------------------------------------------------------------------
def Clear_Musor24(data):
    c_data = data.replace("#2","")
    mlen = 27
    index = 0
    if ":<:" in c_data:
        while index<1000:
          index += 1
          Beg = c_data.rfind(":<:")
          if Beg >=0:
             c_data=c_data.replace(c_data[Beg:Beg+mlen],"")
          else:
               for i in range(0, len(c_data)):
                  if c_data[i] not in ("=+0123456789"+string.ascii_letters):
                     return None
               return c_data
    return None

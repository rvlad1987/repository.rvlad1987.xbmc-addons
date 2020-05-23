# -*- coding: utf-8 -*-

__author__ = 'hal9000'
__all__ = ['Cache', 'CacheServer']

import socket
import time
import json
import hashlib

from sqlite3 import dbapi2 as sqlite

import xbmc

import log
import gui
import system

SOCKET = '127.0.0.1', 59999
CLEAR = 60*60*24 # 1 day


class SQL:
    def __init__(self, name, version):
        self.fs = system.FS('cache')
        if self.fs.exists('sandbox://' + name + '.sqlite'):
            self.con = sqlite.connect(self.fs('sandbox://' + name + '.sqlite'))
        else:
            self.con = sqlite.connect(self.fs('sandbox://' + name + '.sqlite'))
            self.sql_set('pragma auto_vacuum=1')
            self.sql_set('create table meta(data text)')
            self.sql_set('insert into meta(data) values(?)', (json.dumps({'version': version, 'timeout': int(time.time()) + CLEAR}),))
            self.sql_set('create table cache(token varchar(32) unique, expire integer, data text)')
            self.sql_set('create index dataindex on cache(expire)')
        self.meta_load()


    def health(self, version):
        if self.meta['version'] != version:
            self.meta_save('version', version)
            self.clear()
        elif self.meta['timeout'] < int(time.time()):
            self.sql_set('delete from cache where expire<?', (int(time.time()), ))
            self.meta_save('timeout', int(time.time()) + CLEAR)


    def get(self, token):
        return self.sql_get('select data from cache where token=? and expire>? limit 1', (hashlib.md5(str(token)).hexdigest(), int(time.time())))


    def set(self, token, expire, data):
        try:
            jsdata = json.dumps(data)
        except:
            pass
        else:
            self.sql_set('replace into cache(token,expire,data) values(?,?,?)', (hashlib.md5(str(token)).hexdigest(), int(time.time()) + expire, jsdata))


    def clear(self):
        self.sql_set('delete from cache')
        self.meta_save('timeout', int(time.time()) + CLEAR)



    # Private

    def sql_get(self, sql, *args):
        cur = self.con.cursor()
        cur.execute(sql, *args)
        rows = cur.fetchall()
        cur.close()
        try:
            return json.loads(rows[0][0])
        except:
            return None


    def sql_set(self, sql, *args):
        cur = self.con.cursor()
        cur.execute(sql, *args)
        self.con.commit()
        cur.close()


    def meta_load(self):
        self.meta = self.sql_get('select data from meta')
        if not self.meta:
            self.meta = {'version': '', 'timeout': 0}


    def meta_save(self, key, value):
        self.meta[key] = value
        self.sql_set('update meta set data=?', (json.dumps(self.meta),))





class Base:
    def recv(self, sock):
        data = ''
        length = ''
        idle = time.time()
        while True:
            try:
                if isinstance(length, basestring):
                    c = sock.recv(1)
                    if c == '.':
                        length = int(length)
                    else:
                        length += c
                else:
                    data = sock.recv(length - len(data))
            except socket.error, e:
                if not e.errno in (10035, 35):
                    self.log('Recive', repr(e))

                if e.errno in (22,):
                    self.log('Socket error 22')
                    return None

                if idle + 10 < time.time():
                    self.log('Timeout')
                    return None
            else:
                if not isinstance(length, basestring) and len(data) == length:
                    try:
                        return json.loads(data)
                    except Exception, e:
                        self.log('JSON', repr(e))
                        return None

    def send(self, sock, data):
        try:
            jsdata = json.dumps(data)
        except:
            jsdata = 'null'
        sock.send(str(len(jsdata)) + '.' + jsdata)

    def log(self, *args):
        log.error(str(self.__class__.__name__), *args)



class Cache(Base):
    def __init__(self, name, version=None):
        self.name = str(name).strip()
        self.version = str(version).strip()

    def call(self, token, fun, *args, **kwargs):
        cache = self._call([1, token])
        if cache is not None:
            return cache

        res = fun(*args, **kwargs)
        if res is None:
            return None
        else:
            if isinstance(res, tuple) and len(res) == 2 and isinstance(res[0], int):
                self._call([2, token, res[0], res[1]])
                return res[1]
            else:
                return res


    def clear(self):
        self._call('clear')


    def _call(self, data):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect(SOCKET)
        except socket.error, e:
            if e.errno in (111,):
                self.log("CacheServer isn't running")
            else:
                self.log('Connect', repr(e))
            return None
        except:
            return None
        else:
            self.send(sock, [self.name, self.version] + data)
            r = self.recv(sock)
            sock.close()
            return r



class CacheServer(Base):
    def __init__(self):
        self.sql = {}

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(SOCKET)
        except Exception, e:
            self.log('Bind', repr(e))
            gui.message('Failed to start CacheServer. Check log.')
        else:

            sock.listen(1)
            sock.setblocking(0)

            idle = time.time()
            while not xbmc.abortRequested:
                try:
                    (client, address) = sock.accept()
                except socket.error, e:
                    if e.errno == 11 or e.errno == 10035 or e.errno == 35:
                        if idle + 3 < time.time():
                            time.sleep(0.5)
                        continue
                    self.log('Accept', repr(e))
                    continue
                except:
                    continue
                else:
                    self.send(client, self.command(self.recv(client)))
                    idle = time.time()

            sock.close()


    def command(self, data):
        if not data or not isinstance(data, list) or len(data) < 3 or data[2] not in (1, 2, 3):
            return None


        sql = self.open(data[0], data[1])
        if not sql:
            return None


        if data[2] == 1 and len(data) == 4 and isinstance(data[3], basestring):
            return sql.get(data[3])

        elif data[2] == 2 and len(data) == 6 and isinstance(data[3], basestring) and isinstance(data[4], int):
            sql.set(data[3], data[4], data[5])
            return 1

        elif data[2] == 3:
            sql.clear()
            return 1

        return None

    def open(self, db, version):
        name = str(db).strip()
        if not name:
            return None
        ver = str(version).strip()
        if db not in self.sql:
            self.sql[db] = SQL(db, ver)
        self.sql[db].health(ver)
        return self.sql[db]

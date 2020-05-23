# -*- coding: utf-8 -*-

__author__ = 'hal9000'
__all__ = ['SQL', 'NoSQL', 'Cache']

import time
import json
import re
import pickle
import threading

try:
    from sqlite3 import dbapi2 as sqlite
except:
    from pysqlite2 import dbapi2 as sqlite

from system import FS

class SQL(object):
    def __init__(self, filename):
        self._filename = filename
        self._re_upgrade = re.compile('^upgrade_?([0-9]+)$')
        self.db = None

        if not FS().exists(self._filename):
            self._meta = {'version': 0}
            self.set('pragma auto_vacuum=1')
            self.set('create table xbmcup_meta(data text)')
            self.set('insert into xbmcup_meta(data) values(?)', (json.dumps(self._meta),))
            self.create()
        else:
            self._meta = json.loads(self.get('select data from xbmcup_meta')[0][0])

        upgrade = [(int(x.replace('upgrade_', '').replace('upgrade', '')), x) for x in dir(self) if self._re_upgrade.search(x)]
        upgrade.sort(lambda x, y: cmp(x[0], y[0]))
        upgrade = [x for x in upgrade if self._meta['version'] < x[0]]
        if upgrade:
            [getattr(self, x[1])() for x in upgrade]
            self._meta['version'] = upgrade[-1][0]
            self.set('update xbmcup_meta set data=?', (json.dumps(self._meta),))

    def create(self):
        pass

    def __call__(self, sql, *args):
        self.connect()
        self.cur.execute(sql, *args)
        while True:
            row = self.cur.fetchone()
            if row is None:
                self.close()
                break
            else:
                yield row

    def get(self, sql, *args):
        self.connect()
        self.cur.execute(sql, *args)
        rows = self.cur.fetchall()
        self.close()
        return rows

    def set(self, sql, *args):
        self.connect()
        self.cur.execute(sql, *args)
        self.db.commit()
        res = self.cur.lastrowid, self.cur.rowcount
        self.close()
        return res

    def connect(self):
        if self.db is None:
            self.db = sqlite.connect(self._filename)
            self.cur = self.db.cursor()

    def close(self):
        if self.db is not None:
            self.cur.close()
            self.db.close()
            self.db = None


class _NoSqlSQL(SQL):
    def create(self):
        self.set('create table nosql(id varchar(255) unique, data blob)')


class NoSQL(object):
    """
    -- INIT:
        db = NoSQL(filename)

    -- GET:
        value = db[key]
        value = db.key
        [value1, value2, ..., valueN] = db(key1, key2, ..., keyN)

    -- SET:
        db[key] = value
        sb.key = value
        db({keys: values})
    """

    def __init__(self, filename):
        self._sql = _NoSqlSQL(filename)

    def __call__(self, *args):
        if len(args) == 1 and isinstance(args[0], dict):
            for key, value in args[0].iteritems():
                self._set(key, value)
        else:
            res = dict.fromkeys(args)
            for row in self._sql('select id,data from nosql where id in (' + ','.join(len(args)*'?') + ')', args):
                try:
                    res[row[0]] = pickle.loads(row[1])
                except:
                    pass
            return [res[x] for x in args]

    def __getattr__(self, key):
        return self._get(key)

    def __getitem__(self, key):
        return self._get(key)

    def __setattr__(self, key, value):
        if key == '_sql':
            self.__dict__[key] = value
        else:
            self._set(key, value)

    def __setitem__(self, key, value):
        self._set(key, value)

    def _get(self, key):
        row = self._sql.get('select id,data from nosql where id=? limit 1', (key, ))
        if not row:
            return None
        else:
            try:
                return pickle.loads(row[0][1])
            except:
                return None

    def _set(self, key, value):
        self._sql.set('replace into nosql(id,data) values(?,?)', (key, sqlite.Binary(pickle.dumps(value))))


class _CacheSQL(SQL):
    def create(self):
        self.set('create table cache(id varchar(255) unique, expire integer, data blob)')


class Cache(object):
    def __init__(self, filename):
        self.sql = _CacheSQL(filename)

    def __call__(self, token, callback, *args, **kwargs):
        rows = self.sql.get('select expire,data from cache where id=? limit 1', (token, ))
        if rows:
            if rows[0][0] and rows[0][0] < int(time.time()):
                pass
            else:
                try:
                    obj = pickle.loads(rows[0][1])
                except:
                    pass
                else:
                    return obj

        response = callback(*args, **kwargs)
        if not response:
            return response

        if response[0]:
            self.sql.set('replace into cache(id,expire,data) values(?,?,?)',
                (token, None if isinstance(response[0], bool) else (int(time.time()) + response[0]),
                 sqlite.Binary(pickle.dumps(response[1]))))

        return response[1]

    def get(self, tokens, expire=None):
        if not isinstance(tokens, (list, dict)):
            tokens = [tokens]

        result = dict.fromkeys(tokens)

        for row in self.sql.get('select id,expire,data from cache where id in (' + ','.join(len(tokens)*'?') + ')', tokens):
            if expire is None:
                if row[1] and row[1] < int(time.time()):
                    pass
                else:
                    try:
                        obj = pickle.loads(row[2])
                    except:
                        pass
                    else:
                        result[row[0]] = obj

            elif expire:
                if row[1] and row[1] < int(time.time()):
                    try:
                        obj = pickle.loads(row[2])
                    except:
                        pass
                    else:
                        result[row[0]] = obj

            else:
                try:
                    obj = pickle.loads(row[2])
                except:
                    pass
                else:
                    result[row[0]] = obj


        return result


    def set(self, token, data, expire=None):
        if expire:
            expire += int(time.time())
        self.sql.set('replace into cache(id,expire,data) values(?,?,?)', (token, expire, sqlite.Binary(pickle.dumps(data))))


    def multi(self, prefix, ids, method, live):

        def fetch(id):
            response[prefix + id] = method(id)

        if not isinstance(ids, (list, tuple)):
            ids = [ids]
        tokens = [prefix + x for x in ids]
        result = self.get(tokens)

        request = [x.split(':')[1] for x, y in result.iteritems() if not y]
        if request:
            response, pool = {}, []

            for id in request:
                pool.append(threading.Thread(target=fetch, args=(id,)))

            for t in pool:
                t.start()

            for t in pool:
                t.join()

            for token, data in response.iteritems():
                self.set(token, data, live)

            result.update(response)

        return dict([(x, result[prefix + x]) for x in ids])


    def import_cache(self, filename):
        # TODO: Import cache
        pass

    def export_cache(self, filename):
        # TODO: Export cache
        pass

    def flush(self):
        self.sql.set('delete from cache')


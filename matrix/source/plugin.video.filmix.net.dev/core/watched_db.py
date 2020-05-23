# -*- coding: utf-8 -*-

import xbmcup.db
from .defines import *

try:
    from sqlite3 import dbapi2 as sqlite
except:
    from pysqlite2 import dbapi2 as sqlite

SQL = xbmcup.db.SQL(xbmcup.system.fs('sandbox://'+CACHE_DATABASE))

class Watched:
    def __init__(self):
        SQL.set('CREATE TABLE IF NOT EXISTS watched(id INTEGER PRIMARY KEY AUTOINCREMENT, movie_id INTEGER, season INTEGER, episode INTEGER, UNIQUE(movie_id, season, episode) ON CONFLICT IGNORE)')

    def set_watched(self, movie_id, season, episode):
        SQL.set('INSERT INTO watched (movie_id, season, episode) VALUES (%i,%i,%i)' % (movie_id, season, episode))

    def set_watched_all_episodes(self, movie_id, movieInfo):
        sql = 'INSERT INTO watched (movie_id, season, episode) VALUES '
        result = []
        
        try:
            for movies in movieInfo['movies']:
                for quality in movies['movies']:
                    for episode in movies['movies'][quality]:
                        temp = [ episode[1], episode[2] ]
                        if temp not in result:
                            result.append( temp )
                            sql += '(%i,%i,%i),' % ( movie_id, temp[0], temp[1] )
            
            SQL.set( sql[:-1] )
            self.get_not_watched()
            
            return True
        except:
            return False

    def get_not_watched(self):
        pass
        
    def is_watched(self, movie_id, season, episode):
        result = SQL.get('SELECT count(movie_id) FROM watched WHERE movie_id = %i AND season = %i AND episode = %i' % (movie_id, season, episode))
        return result[0][0] > 0
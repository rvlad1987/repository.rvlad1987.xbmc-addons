# -*- coding: utf-8 -*-

import os, re, sys, json, urllib, hashlib, traceback
import xbmcup.app, xbmcup.db, xbmcup.system, xbmcup.net, xbmcup.parser, xbmcup.gui
import xbmc, cover, xbmcplugin, xbmcgui
from http import HttpData
from auth import Auth
from common import Render
from defines import *
from watched_db import Watched

try:
    from sqlite3 import dbapi2 as sqlite
except:
    from pysqlite2 import dbapi2 as sqlite

CACHE = xbmcup.db.Cache(xbmcup.system.fs('sandbox://'+CACHE_DATABASE))
SQL = xbmcup.db.SQL(xbmcup.system.fs('sandbox://'+CACHE_DATABASE))

# fix if cache file delete
SQL.set('CREATE TABLE IF NOT EXISTS cache(id varchar(255) unique, expire integer, data blob)')
SQL.set('CREATE INDEX IF NOT EXISTS dataindex ON cache(expire)')

class AbstactList(xbmcup.app.Handler, HttpData, Render):
    def add_movies(self, response, ifempty=30111):
        if(len(response['data']) > 0):
            for movie in response['data']:
                menu = []
                
                menu.append([xbmcup.app.lang[34033], self.link('context', {'action': 'show_movieinfo', 'movie' : movie})])
                if xbmcup.app.setting['watched_db'] == 'true' and xbmcup.app.setting['strm_url'] == 'true':
                    menu.append([xbmcup.app.lang[30170], self.link('context', {'action': 'add_episodes_to_watched_db', 'movie' : movie})])

                if(self.__class__.__name__ != 'BookmarkList'):
                    menu.append([xbmcup.app.lang[30147], self.link('context', {'action': 'add_bookmark', 'id' : movie['id']})])
                else:
                    menu.append([xbmcup.app.lang[30148], self.link('context', {'action': 'del_bookmark', 'id' : movie['id']})])
                    
                if(self.__class__.__name__ != 'Watch_Later'):
                    menu.append([xbmcup.app.lang[30163], self.link('context', {'action': 'add_watch_later', 'id' : movie['id']})])
                else:
                    menu.append([xbmcup.app.lang[30164], self.link('context', {'action': 'del_watch_later', 'id' : movie['id']})])

                not_movie = ''
                if(movie['not_movie'] == True):
                    not_movie = xbmcup.app.lang[34028]+' '

                self.item(not_movie+movie['name']+' '+movie['year']+' '+movie['quality'],
                          self.link('quality-list', {'movie_page' : movie['url'], 'cover' : movie['img']}),
                          folder=True, cover=movie['img'], menu=menu)
        else:
            self.item(u'[COLOR red]['+xbmcup.app.lang[ifempty]+'][/COLOR]', self.link('null'), folder=False, cover=cover.info)


class MovieList(AbstactList):
    def handle(self):
        params = self.argv[0]
        try:
            page = int(params['page'])
        except:
            params['page'] = 0
            page = 0


        page_url = "/"+params['dir']+"/"

        md5 = hashlib.md5()
        md5.update(page_url+'/page/'+str(page)+'?v='+xbmcup.app.addon['version'])

        response = CACHE(str(md5.hexdigest()), self.get_movies, page_url, page)
        if(response['page']['pagenum'] > 1):
            params['page'] = page-1
            self.item('[COLOR green]'+xbmcup.app.lang[30106]+'[/COLOR]', self.replace('list', params), cover=cover.prev, folder=True)
            params['page'] = page+1

        self.add_movies(response)

        params['page'] = page+1
        if(response['page']['maxpage'] >= response['page']['pagenum']+1):
            self.item('[COLOR green]'+xbmcup.app.lang[30107]+'[/COLOR]', self.replace('list', params), cover=cover.next, folder=True)

class SearchList(AbstactList):
    def handle(self):
        try:
            params = self.argv[0]
        except:
            params = {}

        try:
            is_united_search = int(params['is_united'])
        except:
            is_united_search = 0

        try:
            page = int(params['page'])
        except:
            params['page'] = 0
            page = 0
        history = []
        try:
            req_count = int(xbmcup.app.setting['search_history'])
        except:
            req_count = 0

        try:
            usersearch = params['usersearch']
            vsearch = params['vsearch']
        except:
            history = []

            if(req_count > 0):
                SQL.set('create table if not exists search(id INTEGER PRIMARY KEY AUTOINCREMENT, value varchar(255) unique)')
                history = SQL.get('SELECT id,value FROM search ORDER BY ID DESC')
            else:
                SQL.set('DELETE FROM search')

            if(len(history)):
                history = list(history)
                values = ['[COLOR yellow]'+xbmcup.app.lang[30108]+'[/COLOR]']
                for item in history:
                   values.append(item[1])
                ret = xbmcup.gui.select(xbmcup.app.lang[30161], values)

                if ret == None:
                    return

                if(ret > 0):
                    usersearch = values[ret]
                    vsearch = usersearch.encode('utf-8').decode('utf-8')
                    params['vsearch'] = vsearch
                    params['usersearch'] = urllib.quote_plus(usersearch.encode('utf-8'))
                else:
                    params['vsearch'] = ''
            else:
                params['vsearch'] = ''

            if(params['vsearch'] == ''):
                keyboard = xbmc.Keyboard()
                keyboard.setHeading(xbmcup.app.lang[30112])
                keyboard.doModal()
                usersearch = keyboard.getText(0)
                vsearch = usersearch.decode('utf-8')
                params['vsearch'] = vsearch
                params['usersearch'] = urllib.quote_plus(usersearch)

        if not usersearch: return
        try:
            SQL.set('INSERT INTO search (value) VALUES ("%s")' % (vsearch))
        except sqlite.IntegrityError:
            SQL.set('DELETE FROM search WHERE `value` = "%s"' % (vsearch))
            SQL.set('INSERT INTO search (value) VALUES ("%s")' % (vsearch))
        except:
            pass

        if(len(history) >= req_count):
            SQL.set('DELETE FROM search WHERE `id` = (SELECT MIN(id) FROM search)')
        
        '''
        #page_url = "search/index/index/usersearch/"+params['usersearch']
        page_url = "/engine/ajax/sphinx_search.php?story=%s&search_start=%s" % (params['usersearch'], page+1)
        # print page_url
        md5 = hashlib.md5()
        #md5.update(page_url+'/page/'+str(page))
        md5.update(params['usersearch'].encode('utf8')+'?v='+xbmcup.app.addon['version'])
        response = CACHE(str(md5.hexdigest()), self.get_movies, page_url, page, '', False, usersearch)
        '''
        post_data={'search_word' : params['vsearch']}
        post_result = self.ajax(SITE_URL + '/api/search/suggest',post_data, SITE_URL + '/')
        json_result = json.loads(post_result)
        # print json_result
        response = {'page': {}, 'data': []}
        re_info = re.compile('<.*?>')
        for m in json_result['message']:
            year_info = ''
            if(m['year'] != ''):
                year_info = m['year']+', '
            year_info += re.sub(re_info, '', m['categories'])
            
            response['data'].append({
                    'name': m['title'].strip(),
                    'img': m['poster'].replace('/w40/','/w220/'),
                    'url': m['link'],
                    'not_movie': False,
                    'year': '[COLOR white]['+year_info+'][/COLOR]',
                    'quality': '',
                    'id': m['id']
                })
        
        if(is_united_search == 0):
            self.item(u'[COLOR yellow]'+xbmcup.app.lang[30108]+'[/COLOR]', self.link('search'), folder=True, cover=cover.search)
            self.item('[COLOR blue]['+xbmcup.app.lang[30109]+': '+vsearch+'][/COLOR]',
                  self.link('null'), folder=False, cover=cover.info)
        '''
        if(is_united_search==0 and response['page']['pagenum'] > 1):
            params['page'] = page-1
            self.item('[COLOR green]'+xbmcup.app.lang[30106]+'[/COLOR]', self.replace('search', params), cover=cover.prev, folder=True)
            params['page'] = page+1
        '''
        self.add_movies(response)
        '''
        params['page'] = page+1
        if(is_united_search == 0):
            if(response['page']['maxpage'] >= response['page']['pagenum']+1):
                self.item(u'[COLOR green]'+xbmcup.app.lang[30107]+'[/COLOR]', self.replace('search', params), cover=cover.next, folder=True)
        '''


class BookmarkList(AbstactList):

    def handle(self):
        Auth().autorize()

        try:
            params = self.argv[0]
        except:
            params = {}

        try:
            url = params['url']
        except:
            url = ''

        try:
            page = params['page']
        except:
            page = 0

        if(xbmcup.app.setting['is_logged'] == 'false'):
            xbmcup.gui.message(xbmcup.app.lang[30149].encode('utf-8'))
            return False

        self.show_movies(url, page)
        self._variables['is_item'] = False
        self.render(cache=False)


    def show_movies(self, url, page):
        params = {}
        params['url'] = url
        url = 'favorites'#'playlist/22517-pervyy'#'favorites'
        md5 = hashlib.md5()
        md5.update(url+'?v='+xbmcup.app.addon['version'])
        response = CACHE(str(md5.hexdigest()), self.get_movies, url, page, 'dle-content', True)

        if(page > 0):
            params['page'] = page-1
            self.item('[COLOR green]'+xbmcup.app.lang[30106]+'[/COLOR]', self.replace('bookmarks', params), cover=cover.prev, folder=True)
            params['page'] = page+1

        self.add_movies(response, 30152)

        params['page'] = page+1
        if(response['page']['maxpage'] >= response['page']['pagenum']+1):
            self.item(u'[COLOR green]'+xbmcup.app.lang[30107]+'[/COLOR]', self.replace('bookmarks', params), cover=cover.next, folder=True)



class Watch_Later(AbstactList):

    def handle(self):
        Auth().autorize()

        try:
            params = self.argv[0]
        except:
            params = {}

        try:
            url = params['url']
        except:
            url = ''

        try:
            page = params['page']
        except:
            page = 0

        if(xbmcup.app.setting['is_logged'] == 'false'):
            xbmcup.gui.message(xbmcup.app.lang[30149].encode('utf-8'))
            return False

        self.show_movies(url, page)
        self._variables['is_item'] = False
        self.render(cache=False)


    def show_movies(self, url, page):
        params = {}
        params['url'] = url
        url = 'watch_later'
        md5 = hashlib.md5()
        md5.update(url+'?v='+xbmcup.app.addon['version'])
        response = CACHE(str(md5.hexdigest()), self.get_movies, url, page, 'dle-content', True)

        if(page > 0):
            params['page'] = page-1
            self.item('[COLOR green]'+xbmcup.app.lang[30106]+'[/COLOR]', self.replace('watch_later', params), cover=cover.prev, folder=True)
            params['page'] = page+1

        self.add_movies(response, 30152)

        params['page'] = page+1
        if(response['page']['maxpage'] >= response['page']['pagenum']+1):
            self.item(u'[COLOR green]'+xbmcup.app.lang[30107]+'[/COLOR]', self.replace('watch_later', params), cover=cover.next, folder=True)


class My_News(AbstactList):

    def handle(self):
        Auth().autorize()

        try:
            params = self.argv[0]
        except:
            params = {}

        try:
            url = params['url']
        except:
            url = ''

        try:
            page = params['page']
        except:
            page = 0

        if(xbmcup.app.setting['is_logged'] == 'false'):
            xbmcup.gui.message(xbmcup.app.lang[30149].encode('utf-8'))
            return False

        self.show_news(url, page)
        self._variables['is_item'] = False
        self.render(cache=False)


    def show_news(self, url, page):
        params = {}
        params['url'] = url
        url = 'my_news'
        md5 = hashlib.md5()
        md5.update(url+'?v='+xbmcup.app.addon['version'])
        response = CACHE(str(md5.hexdigest()), self.get_my_news, url, page, 'dle-content', True)
        
        if(page > 0):
            params['page'] = page-1
            self.item('[COLOR green]'+xbmcup.app.lang[30106]+'[/COLOR]', self.replace('my_news', params), cover=cover.prev, folder=True)
            params['page'] = page+1

        self.add_movies(response, 30152)

        params['page'] = page+1
        if(response['page']['maxpage'] >= response['page']['pagenum']+1):
            self.item(u'[COLOR green]'+xbmcup.app.lang[30107]+'[/COLOR]', self.replace('my_news', params), cover=cover.next, folder=True)


class Collections(AbstactList):

    def handle(self):
        Auth().autorize()

        try:
            params = self.argv[0]
        except:
            params = {}

        try:
            url = params['url']
        except:
            url = ''

        try:
            page = params['page']
        except:
            page = 0

        if(xbmcup.app.setting['is_logged'] == 'false'):
            xbmcup.gui.message(xbmcup.app.lang[30149].encode('utf-8'))
            return False

        if url == '':
            collectionsInfo = self.get_collections_info()
            if collectionsInfo == []:
                self.item(u'[COLOR red]['+xbmcup.app.lang[30174]+'][/COLOR]', self.link('null'), folder=False, cover=cover.info)
            else:            
                for collectionInfo in collectionsInfo:
                    self.item(collectionInfo['title'], self.link('collections',  {'url' : collectionInfo['url']}), folder=True, cover=collectionInfo['img'])
        else:
            self.show_movies(url, page)

        self._variables['is_item'] = False
        self.render(cache=False)


    def show_movies(self, url, page):
        params = {}
        params['url'] = url
        md5 = hashlib.md5()
        md5.update(url+'?v='+xbmcup.app.addon['version'])
        response = CACHE(str(md5.hexdigest()), self.get_movies, url, page, 'dle-content', True)
        
        if(page > 0):
            params['page'] = page-1
            self.item('[COLOR green]'+xbmcup.app.lang[30106]+'[/COLOR]', self.replace('collections', params), cover=cover.prev, folder=True)
            params['page'] = page+1

        self.add_movies(response, 34026)

        params['page'] = page+1
        if(response['page']['maxpage'] >= response['page']['pagenum']+1):
            self.item(u'[COLOR green]'+xbmcup.app.lang[30107]+'[/COLOR]', self.replace('collections', params), cover=cover.next, folder=True)



class QualityList(xbmcup.app.Handler, HttpData, Render):
    movieInfo = None

    def get_icon(self, quality):
        if(quality in cover.res_icon):
            return cover.res_icon[quality]
        else:
            return cover.res_icon['default']

    def handle(self):
        self.params = self.argv[0]

        # fix for old versions
        if 'movieInfo' in self.params and 'movie_page' not in self.params:
            self.params['movie_page'] = self.params['movieInfo']['page_url']
            del self.params['movieInfo']

        md5 = hashlib.md5()
        md5.update( 'movieInfo:%s?v=%s' % (self.params['movie_page'], xbmcup.app.addon['version']) )
        cache_key = str( md5.hexdigest() )
        self.movieInfo = CACHE.get(cache_key)[cache_key]
        # print 'try get from cache :', cache_key
        if not self.params.get('cache') or not self.movieInfo:
            self.movieInfo = self.get_movie_info(self.params['movie_page'])
            CACHE.set(cache_key, self.movieInfo, 60*60)
            # print 'set to cache :', cache_key

        try:
            self.params['sub_dir'] = int(self.params['sub_dir'])
        except:
            self.params['sub_dir'] = None

        quality_settings = int(xbmcup.app.setting['quality'])
        default_quality = QUALITYS[quality_settings]

        try:
            self.params['quality_dir'] = self.int_quality(self.params['quality_dir'])
        except:
            self.params['quality_dir'] = None

        if(self.params['sub_dir'] == None):
            self.def_dir = 0
        else:
            self.def_dir=  self.params['sub_dir']

        if(default_quality != None and self.params['quality_dir'] == None):
            try:
                test = self.movieInfo['movies'][self.def_dir]['movies'][self.str_quality(default_quality)]
                self.params['quality_dir'] = self.str_quality(default_quality)
            except:
                if(xbmcup.app.setting['lowest_quality'] == 'true'):
                    quality_settings -= 1
                    if(quality_settings > 1):
                        try:
                            default_quality = str(QUALITYS[quality_settings])
                            test = self.movieInfo['movies'][self.def_dir]['movies'][self.str_quality(default_quality)]
                            self.params['quality_dir'] = default_quality
                        except:
                            quality_settings -= 1
                            if(quality_settings > 1):
                                try:
                                    default_quality = str(QUALITYS[quality_settings])
                                    test = self.movieInfo['movies'][self.def_dir]['movies'][self.str_quality(default_quality)]
                                    self.params['quality_dir'] = default_quality
                                except:
                                    pass

        #если на сайте несколько папок с файлами
        if((len(self.movieInfo['movies']) > 1 and self.params['sub_dir'] == None) or self.movieInfo['no_files'] != None):
            self.show_folders()

        #если эпизоды есть в разном качестве
        elif(self.movieInfo['episodes'] == True and
            len(self.movieInfo['movies'][self.def_dir]['movies']) > 1 and
            self.params['quality_dir'] == None):

            self.show_quality_folder()

        elif(self.movieInfo['episodes'] == True):
            self.show_episodes()


    def show_folders(self):
        if(self.movieInfo['no_files'] == None):
            i = 0
            for movie in self.movieInfo['movies']:
                self.item(movie['folder_title'],
                           self.link('quality-list',
                                    {
                                        'sub_dir' : i,
                                        'movie_page': self.params['movie_page'],
                                        'cache': True,
                                    }
                           ),
                           folder=True,
                           cover = self.movieInfo['cover']
                )
                i = i+1
        else:
            self.item(u'[COLOR red]['+self.movieInfo['no_files'].decode('utf-8')+'][/COLOR]', self.link('null'), folder=False, cover=cover.info)

    def int_quality(self, quality):
        if quality == '1080p':
            i_quality = 1080
        elif quality == '1440p':
            i_quality = 1440
        elif quality == '2160p':
            i_quality = 2160
        else:
            i_quality = int(quality)
        return i_quality

    def str_quality(self, quality):
        if quality == 1080:
            s_quality = '1080p'
        elif quality == 1440:
            s_quality = '1440p'
        elif quality == 2160:
            s_quality = '2160p'
        else:
            s_quality = str(quality)
        return s_quality

    def check_proplus_quality(self, quality):
        return self.int_quality(quality) < 1080 or self.movieInfo['is_proplus'] > 0

    def show_episodes(self):
        show_first_quality = False

        if(self.params['quality_dir']):
            if(xbmcup.app.setting['quality'] != '0' and xbmcup.app.setting['lowest_quality'] == 'true'):
                movies = []
                max_episode = 1
                for quality in self.movieInfo['movies'][self.def_dir]['movies']:
                    for movie in self.movieInfo['movies'][self.def_dir]['movies'][quality]:
                        if max_episode < movie[2]: max_episode = movie[2]
                for episode_num in xrange(1, max_episode + 1):
                    for quality in self.movieInfo['movies'][self.def_dir]['movies']:
                        if self.int_quality(self.params['quality_dir']) >= self.int_quality(quality) and self.check_proplus_quality(quality):
                            for movie in self.movieInfo['movies'][self.def_dir]['movies'][quality]:
                                episode_exist = False
                                for _movie in movies:
                                    if _movie[2] == episode_num:
                                        episode_exist = True
                                        break
                                if episode_num == movie[2] and not episode_exist: movies.append(movie)
            else:
                movies = self.movieInfo['movies'][self.def_dir]['movies'][self.str_quality(self.params['quality_dir'])]
        else:
            show_first_quality = True
            movies = self.movieInfo['movies'][self.def_dir]['movies']

        if(show_first_quality):
            for quality in movies:
                for movie in movies[quality]:
                    self.add_playable_item(movie)
                break
        else:
            for movie in movies:
                self.add_playable_item(movie)

        self.render_items()

    def show_quality_folder(self):
        if(len(self.movieInfo['movies']) > 1):
            movies = self.movieInfo['movies'][self.params['sub_dir']]['movies']
        else:
            movies = self.movieInfo['movies'][0]['movies']

        resolutions = []
        for movie in movies:
            if( self.check_proplus_quality(movie) ):
                resolutions.append( self.int_quality(movie) )

        resolutions.sort()

        for movie in resolutions:
            self.item((str(movie) if movie != 0 else 'FLV'),
                self.link('quality-list',
                    {
                        'sub_dir' : self.params['sub_dir'],
                        'quality_dir' : str(movie),
                        'movie_page': self.params['movie_page'],
                        'cache': True,
                    }
                ),
                folder=True,
                cover=self.get_icon(str(movie))
            )

    def get_info(self):
        return {
                'Genre'     : self.movieInfo['genres'],
                'year'      : self.movieInfo['year'],
                'director'  : self.movieInfo['director'],
                # 'rating'    : self.movieInfo['ratingValue'],
                'duration'  : self.movieInfo['durarion'],
                # 'votes'     : self.movieInfo['ratingCount'],
                'plot'      : self.movieInfo['description'],
                'title'     : self.movieInfo['title'],
                'originaltitle' : self.movieInfo['title']
                # 'playcount' : 1,
                # 'date': '%d.%m.%Y',
                # 'count' : 12
            }

    def get_info_strm(self, movie):
        info = {
                'Genre'     : self.movieInfo['genres'],
                'year'      : self.movieInfo['year'],
                # 'rating'    : self.movieInfo['ratingValue'],
                # 'userrating'    : int(self.movieInfo['ratingValue']),
                'duration'  : self.movieInfo['durarion'],
                # 'votes'     : self.movieInfo['ratingCount'],
                'director'  : self.movieInfo['director'],
                # 'title'     : self.movieInfo['title'],
                'plot'      : self.movieInfo['description'][:350]+u'...'
                }

        if xbmcup.app.setting['watched_db'] == 'true' and xbmcup.app.setting['strm_url'] == 'true':
            try:
                movie_id = self.movieInfo['movie_id']
            except:
                movie_id = self.get_movie_id( self.movieInfo['page_url'] )
            
            if Watched().is_watched( movie_id, movie[1], movie[2] ):
                info['playcount'] = 1

        return info

    def get_name(self, file_name):
        result = re.match(r'^(.*?)(?:s(?P<s>\d+))?(?:e(?P<e>[\d-]+))?(?:_(?P<q>\d+))?$', file_name)
        if result and result.groupdict()['s'] and result.groupdict()['e']:
            title = self.movieInfo.get('originaltitle', '') or self.movieInfo['title']
            return '{title} S{s}E{e} [{q}]'.format(title=title.encode('utf8'), **result.groupdict(''))
        return file_name

    def add_playable_item(self, movie):
        file_name        = os.path.basename( os.path.splitext(str(movie[0]))[0] )
        filmix_file_name = file_name

        try:
            file_name = self.get_name(file_name)
        except Exception:
            pass

        if(xbmcup.app.setting['strm_url'] == 'false'):
            self.item(file_name,
                               str(movie[0]),
                               folder=False,
                               media='video',
                               info=self.get_info(),
                               cover = self.movieInfo['cover'],
                               fanart = self.movieInfo['fanart']
            )
        else:
            self.movieInfo['movies']
            for movies in self.movieInfo['movies']:
                for q in movies['movies']:
                    for episode in movies['movies'][q]:
                        if episode[0] == movie[0]:
                            quality      = q
                            folder_title = movies['folder_title']

            play_url = self.resolve('resolve',
                        {
                            'page_url'      : self.movieInfo['page_url'],
                            'resolution'    : quality,
                            'folder'        : folder_title,
                            'file'          : filmix_file_name
                        }
            )

            self.item(file_name,
                               play_url,
                               folder=False,
                               media='video',
                               info=self.get_info_strm(movie),
                               cover = self.movieInfo['cover'],
                               fanart = self.movieInfo['fanart']
            )
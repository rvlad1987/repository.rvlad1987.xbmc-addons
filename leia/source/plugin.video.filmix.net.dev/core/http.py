# -*- coding: utf-8 -*-

import os, re, sys, json, urllib, hashlib, traceback,base64
import xbmcup.app, xbmcup.db, xbmcup.system, xbmcup.net, xbmcup.parser, xbmcup.gui
import xbmc, cover, xbmcplugin, xbmcgui
from common import Render
from auth import Auth
from defines import *
from watched_db import Watched
from itertools import izip_longest

try:
    cache_minutes = 60*int(xbmcup.app.setting['cache_time'])
except:
    cache_minutes = 0

class HttpData:

    mycookie = None

    def load(self, url):
        try:
            self.auth = Auth()
            self.cookie = self.auth.get_cookies()
            cook = self.mycookie if self.cookie == None else self.cookie
            response = xbmcup.net.http.get(url, cookies=cook, verify=False)
            if(self.cookie == None):
                self.mycookie = response.cookies
        except xbmcup.net.http.exceptions.RequestException:
            print traceback.format_exc()
            return None
        else:
            if(response.status_code == 200):
                if(self.auth.check_auth(response.text) == False):
                    self.auth.autorize()
                return response.text
            return None

    def post(self, url, data):
        try:
            data
        except:
            data = {}
        try:
            self.auth = Auth()
            self.cookie = self.auth.get_cookies()
            cook = self.mycookie if self.cookie == None else self.cookie
            response = xbmcup.net.http.post(url, data, cookies=cook, verify=False)

            if(self.cookie == None):
                self.mycookie = response.cookies

        except xbmcup.net.http.exceptions.RequestException:
            print traceback.format_exc()
            return None
        else:
            if(response.status_code == 200):
                if(self.auth.check_auth(response.text) == False):
                    self.auth.autorize()
                return response.text
            return None


    def ajax(self, url, data={}, referer=False):
        try:
            self.auth = Auth()
            self.cookie = self.auth.get_cookies()
            headers = {
                'X-Requested-With' : 'XMLHttpRequest'
            }
            if(referer):
                headers['Referer'] = referer


            cook = self.mycookie if self.cookie == None else self.cookie
            if(len(data) > 0):
                response = xbmcup.net.http.post(url, data, cookies=cook, headers=headers, verify=False)
            else:
                response = xbmcup.net.http.get(url, cookies=cook, headers=headers, verify=False)

            if(self.cookie == None):
                self.mycookie = response.cookies

        except xbmcup.net.http.exceptions.RequestException:
            print traceback.format_exc()
            return None
        else:
            return response.text if response.status_code == 200 else None


    def get_my_news(self, url, page, idname='dle-content', nocache=False, search="", itemclassname="shortstory"):
        page = int(page)

        url = SITE_URL+"/api/notifications/get"

        if(page > 0 and search == ''):
            page += 1
        else:
            page = 1

        post_data={'page' : page}

        html = self.ajax(url, post_data, SITE_URL + '/')

        if not html:
            return None, {'page': {'pagenum' : 0, 'maxpage' : 0}, 'data': []}
        result = {'page': {'pagenum' : page, 'maxpage' : 10000}, 'data': []}

        try:
            json_result = json.loads(html)
            result['page']['maxpage'] = len(json_result['message']['items'])

            for item_news in json_result['message']['items']:
                movie_name = item_news['data']['movie_name']
                movie_url = item_news['data']['movie_link']
                movie_id = item_news['id']
                quality_s = item_news['date_string']
                dop_info = 'S'+str(item_news['data']['season']) + 'E'+ str(item_news['data']['episode'])
                not_movie = False

                result['data'].append({
                        'url': movie_url,
                        'id': movie_id,
                        'not_movie': not_movie,
                        'quality': '[COLOR ff3BADEE]'+quality_s+'[/COLOR]',
                        'year': '[COLOR ffFFB119]'+dop_info+'[/COLOR]',
                        'name': movie_name.strip(),
                        'img': None
                    })
        except:
            print traceback.format_exc()

        if(nocache):
            return None, result
        else:
            return cache_minutes, result


    def get_movies(self, url, page, idname='dle-content', nocache=False, search="", itemclassname="shortstory"):
        page = int(page)

        if(page > 0 and search == ''):
            url = SITE_URL+"/"+url.strip('/')+"/page/"+str(page+1)
        else:
            url = SITE_URL+"/"+url.strip('/')

        # print url

        if(search != ''):
            html = self.ajax(url)
        else:
            html = self.load(url)

        if not html:
            return None, {'page': {'pagenum' : 0, 'maxpage' : 0}, 'data': []}
        result = {'page': {}, 'data': []}
        soup = xbmcup.parser.html(self.strip_scripts(html))

        if(search != ''):
            result['page'] = self.get_page_search(soup)
        else:
            result['page'] = self.get_page(soup)

        if(idname != ''):
            center_menu = soup.find('div', id=idname)
        else:
            center_menu = soup
        try:
            for div in center_menu.find_all('article', class_=itemclassname):
                href = div.find('div', class_='short')#.find('a')

                movie_name = div.find('div', class_='full').find('h2', class_='name').find('a').get_text()
                movie_url = href.find('a', class_='watch').get('href')
                movie_id = re.compile('/([\d]+)-', re.S).findall(movie_url)[0]

                not_movie = True
                try:
                    not_movie_test = div.find('span', class_='not-movie').get_text()
                except:
                    not_movie = False

                try:
                    quality = div.find('div', class_='full').find('div', class_='quality').get_text().strip()
                except:
                    quality = ''

                dop_information = []
                try:
                    likes = soup.find(class_='like', attrs={'data-id' : movie_id}).find('span').get_text()
                    i_likes = int(likes)
                    if i_likes != 0:
                        if i_likes > 0:
                            likes = '[COLOR ff59C641]' + likes + '[/COLOR]'
                        else:
                            likes = '[COLOR ffDE4B64]' + likes + '[/COLOR]'
                        dop_information.append(likes)
                except:
                    pass

                try:
                    year = div.find('div', class_='item year').find('a').get_text().strip()
                    dop_information.append(year)
                except:
                    pass

                try:
                    genre = div.find('div', class_='category').find(class_='item-content').get_text().strip()
                    dop_information.append(genre)
                except:
                    print traceback.format_exc()

                information = ''
                if(len(dop_information) > 0):
                    information = '[COLOR white]['+', '.join(dop_information)+'][/COLOR]'

                movieposter = self.format_poster_link( href.find('img', class_='poster poster-tooltip').get('src') )

                result['data'].append({
                        'url': movie_url,
                        'id': movie_id,
                        'not_movie': not_movie,
                        'quality': self.format_quality(quality),
                        'year': information,
                        'name': movie_name.strip(),
                        'img': None if not movieposter else movieposter
                    })
        except:
            print traceback.format_exc()

        if(nocache):
            return None, result
        else:
            return cache_minutes, result

    def decode_base64(self, encoded_url):
        codec_a = ("l", "u", "T", "D", "Q", "H", "0", "3", "G", "1", "f", "M", "p", "U", "a", "I", "6", "k", "d", "s", "b", "W", "5", "e", "y", "=")
        codec_b = ("w", "g", "i", "Z", "c", "R", "z", "v", "x", "n", "N", "2", "8", "J", "X", "t", "9", "V", "7", "4", "B", "m", "Y", "o", "L", "h")
        i = 0
        for a in codec_a:
            b = codec_b[i]
            i += 1
            encoded_url = encoded_url.replace(a, '___')
            encoded_url = encoded_url.replace(b, a)
            encoded_url = encoded_url.replace('___', b)
        return base64.b64decode(encoded_url)
        
    def decode_base64_2(self, encoded_url):
        tokens = ("//Y2VyY2EudHJvdmEuc2FnZ2V6emE=", "//c2ljYXJpby4yMi5tb3ZpZXM=", "//a2lub2NvdmVyLnc5OC5uamJo")
        clean_encoded_url = encoded_url[2:].replace("\/","/")
        
        for token in tokens:
            clean_encoded_url = clean_encoded_url.replace(token, "")
        
        return base64.b64decode(clean_encoded_url)

    def decode_unicode(self, encoded_url):

        def grouper(n, iterable, fillvalue=None):
            "grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
            args = [iter(iterable)] * n
            return izip_longest(fillvalue=fillvalue, *args)

        _ = (encoded_url[1:] if encoded_url.find('#') != -1 else encoded_url)
        tokens = map(lambda items: '\u0'+''.join(items), grouper(3, _))
        return ''.join(tokens).decode('unicode_escape')

    def decode_direct_media_url(self, encoded_url, checkhttp=False):
        if(checkhttp == True and (encoded_url.find('http://') != -1 or encoded_url.find('https://') != -1)):
            return False

        try:
            if encoded_url.find('#') != -1:
                if encoded_url[:2] == '#2':
                    return self.decode_base64_2(encoded_url)
                else:
                    return self.decode_unicode(encoded_url)
            else:
                return self.decode_base64(encoded_url)
        except:
            return False

    def format_poster_link(self, link):
        # fix for .cc
        r_link = link.replace('https://filmix.co' , SITE_URL)
        # fix for .live .co .net
        return r_link if r_link.find( SITE_URL ) != -1 else SITE_URL + r_link

    def format_direct_link(self, source_link, q):
        # regex = re.compile("\[([^\]]+)\]", re.IGNORECASE)
        # return regex.sub(q, source_link)
        for link in source_link:
            if link[0].find(q) != -1:
                _or_ = link[1].find(b' or ')
                if _or_ != -1:
                    return link[1][_or_+4:]
                else:
                    return link[1]

    def get_qualitys(self, source_link):
        try:
            avail_quality = re.compile("\[([^\]]+)\]", re.S).findall(source_link)
            # return avail_quality.split(',')
            return avail_quality
        except:
            # return '0'.split()
            return []

    def get_collections_info(self):
        html = self.load(COLLECTIONS_URL)
        collectionsInfo = []
        
        html = html.encode('utf-8')
        soup = xbmcup.parser.html(self.strip_scripts(html))
        
        collections = soup.find_all('a', class_='poster-link poster-hover')
        for collection in collections:
            url_collection = collection.get('href').replace(SITE_URL,'')
            obj_poster = collection.find(class_ = 'poster')
            title_collection = obj_poster.get('alt')
            img_collection = self.format_poster_link( obj_poster.get('src') )
            if img_collection.find('/none.png') > 0: img_collection = cover.treetv
            
            collectionsInfo.append({'url':url_collection, 'img':img_collection, 'title':title_collection});

        return collectionsInfo

    def get_movie_info(self, url):
        html = self.load(url)

        movieInfo = {}
        
        movieInfo['page_url'] = url
        
        movieInfo['no_files'] = None
        movieInfo['episodes'] = True
        movieInfo['movies'] = []
        movieInfo['resolutions'] = []

        if not html:
            movieInfo['no_files'] = 'HTTP error'
            return movieInfo

        html = html.encode('utf-8')
        soup = xbmcup.parser.html(self.strip_scripts(html))

        try:
            movieInfo['is_proplus'] = len(soup.find('span', class_='proplus'))
        except:
            movieInfo['is_proplus'] = 0

        try:
            try:
                film_id = re.compile('film_id ?= ?([\d]+);', re.S).findall(html)[0].decode('string_escape').decode('utf-8')
                movieInfo['movie_id'] = int( film_id )
                js_string = self.ajax(SITE_URL+'/api/movies/player_data', {'post_id' : film_id}, url)
                player_data =  json.loads(js_string, 'utf-8')
                # player_data = player_data['message']['translations']['flash']
                # player_data = player_data['message']['translations']['html5']
                player_data = player_data['message']['translations']['video']
                if player_data == []:
                    movieInfo['no_files'] = xbmcup.app.lang[34026].encode('utf8')
            except:
                movieInfo['no_files'] = xbmcup.app.lang[34026].encode('utf8')
                raise

            serie_q = re.compile('(\d+)', re.S)
            serie_num = re.compile('s(\d+)e(\d+)', re.S)

            for translate in player_data:
                js_string = self.decode_direct_media_url(player_data[translate], True)

                if (js_string == False):
                    continue
                    
                if (js_string.find('.txt') != -1):
                    playlist = self.decode_direct_media_url(self.load(js_string))
                    movies = json.loads(playlist, 'utf-8')

                    try:
                        folders = movies[0]['folder']
                    except:
                        movies = [{ 'folder' : movies, 'title' : 'Season 1' }]

                    for season in movies:
                        current_movie = {'folder_title' : season['title']+' ('+translate+')', 'movies': {}, 'translate': translate}

                        for movie in season['folder']:
                            avail_quality = self.get_qualitys(movie['file'])
                            array_links = re.compile(b'\[([^\]]+)\]([^,]+)', re.S).findall(movie['file']);
                            for q in avail_quality:
                                
                                if(q == ''): continue
                                
                                direct_link = self.format_direct_link(array_links, q) if q != 0 else movie['file']

                                serie_num_res = serie_num.findall(movie['id'])
                                
                                try:
                                    iseason = int(serie_num_res[0][0])
                                except:
                                    iseason = 0
                                
                                try:
                                    iserieId = int(serie_num_res[0][1])
                                except:
                                    iserieId = 0

                                if (q == '4K UHD'):
                                    qq = '2160'
                                elif (q == '2K'):
                                    qq = '1440'
                                else:
                                    qq = serie_q.findall(q)[0]
                                
                                try:
                                    current_movie['movies'][qq].append([direct_link, iseason, iserieId])
                                except:
                                    current_movie['movies'][qq] = []
                                    current_movie['movies'][qq].append([direct_link, iseason, iserieId])
                                
                                current_movie['season'] = iseason

                        movieInfo['movies'].append(current_movie)

                elif(js_string.find('http://') != -1 or js_string.find('https://') != -1):
                    avail_quality = self.get_qualitys(js_string)
                    array_links = re.compile(b'\[([^\]]+)\]([^,]+)', re.S).findall(js_string);
                    current_movie = {'folder_title': translate, 'translate': translate, 'movies': {}}
                    for q in avail_quality:
                        if(q == ''): continue
                        direct_link = self.format_direct_link(array_links, q) if q != 0 else js_string

                        if (q == '4K UHD'):
                            qq = '2160'
                        elif (q == '2K'):
                            qq = '1440'
                        else:
                            qq = serie_q.findall(q)[0]

                        try:
                            current_movie['movies'][qq].append([direct_link, 1, 1])
                        except:
                            current_movie['movies'][qq] = []
                            current_movie['movies'][qq].append([direct_link, 1, 1])

                    movieInfo['movies'].append(current_movie)

            movieInfo['title'] = soup.find('h1', class_='name').get_text()
            try:
                movieInfo['originaltitle'] = soup.find('div', class_='origin-name').get_text().strip()
            except:
                movieInfo['originaltitle'] = ''

            try:
                r_kinopoisk = soup.find('span', class_='kinopoisk btn-tooltip icon-kinopoisk').find('p').get_text().strip()
                if float(r_kinopoisk) == 0: r_kinopoisk = ''
            except:
                r_kinopoisk = ''

            try:
                r_imdb = soup.find('span', class_='imdb btn-tooltip icon-imdb').find('p').get_text().strip()
                movieInfo['ratingValue'] = float(r_imdb)
                movieInfo['ratingCount'] = r_imdb
            except:
                r_imdb = ''
                movieInfo['ratingValue'] = 0
                movieInfo['ratingCount'] = 0

            if r_kinopoisk != '': r_kinopoisk = ' [COLOR orange]Кинопоиск[/COLOR] : '.decode('cp1251') + r_kinopoisk

            if movieInfo['ratingValue'] != 0:
                r_imdb = ' [COLOR yellow]IMDB[/COLOR] : ' + r_imdb
            else:
                r_imdb = ''

            s_rating = r_kinopoisk + r_imdb + ' \n '
            
            try:
                movieInfo['description'] = s_rating + soup.find('div', class_='full-story').get_text().strip()
            except:
                movieInfo['description'] = ''

            try:
                movieInfo['fanart'] = SITE_URL + soup.find('ul', class_='frames-list').find('a').get('href')
            except:
                movieInfo['fanart'] = ''
            try:
                movieInfo['cover'] = soup.find('a', class_='fancybox').get('href')
            except:
                movieInfo['cover'] = ''

            try:
                movieInfo['genres'] = []
                genres = soup.find_all(attrs={'itemprop' : 'genre'})
                for genre in genres:
                   movieInfo['genres'].append(genre.get_text().strip())
                movieInfo['genres'] = ' / '.join(movieInfo['genres']).encode('utf-8')
            except:
                movieInfo['genres'] = ''

            try:
                movieInfo['year'] = soup.find('div', class_='item year').find('a').get_text()
            except:
                movieInfo['year'] = ''

            try:
                movieInfo['durarion'] = soup.find('div', class_='item durarion').get('content')
                movieInfo['durarion'] = int(movieInfo['durarion'])*60
            except:
                movieInfo['durarion'] = ''

            movieInfo['is_serial'] = soup.find('div', class_='item xfgiven_added') is not None

            # try:
                # movieInfo['ratingValue'] = float(soup.find(attrs={'itemprop' : 'ratingValue'}).get_text())
            # except:
                # movieInfo['ratingValue'] = 0

            # try:
                # movieInfo['ratingCount'] = int(soup.find(attrs={'itemprop' : 'ratingCount'}).get_text())
            # except:
                # movieInfo['ratingCount'] = 0

            try:
                movieInfo['director'] = []
                directors = soup.find('div', class_='item directors').findAll('a')
                for director in directors:
                   movieInfo['director'].append(director.get_text().strip())
                movieInfo['director'] = ', '.join(movieInfo['director']).encode('utf-8')
            except:
                movieInfo['director'] = ''
        except:
            print traceback.format_exc()

        #print movieInfo

        return movieInfo

    def get_modal_info(self, url):
        html = self.load(url)
        movieInfo = {}
        movieInfo['error'] = False
        if not html:
            movieInfo['error'] = True
            return movieInfo

        html = html.encode('utf-8')
        soup = xbmcup.parser.html(self.strip_scripts(html))

        try:
            movieInfo['desc'] = soup.find('div', class_='full-story').get_text().strip()
        except:
            movieInfo['desc'] = ''

        try:
            movieInfo['title'] = soup.find('h1', class_='name').get_text()
        except:
            movieInfo['title'] = ''

        try:
            movieInfo['originaltitle'] = soup.find('div', class_='origin-name').get_text().strip()
        except:
            movieInfo['originaltitle'] = ''

        if(movieInfo['originaltitle'] != ''):
             movieInfo['title'] = '%s / %s' % (movieInfo['title'],  movieInfo['originaltitle'])

        try:
            movieInfo['poster'] = self.format_poster_link( soup.find('img', class_='poster poster-tooltip').get('src') )
        except:
            movieInfo['poster'] = ''

        movieInfo['desc'] = ''
        try:
            infos = soup.find('div', class_='full min').find_all('div', class_="item")
            skip = True
            for div in infos:
                if(skip):
                    skip = False
                    continue
                movieInfo['desc'] += self.format_desc_item(div.get_text().strip())+"\n"
        except:
           movieInfo['desc'] = traceback.format_exc()

        try:
            div = soup.find('div', class_='full-panel').find('span', class_='kinopoisk')
            rvalue = div.find('div', attrs={'itemprop' : 'ratingValue'}).get_text().strip()
            rcount = div.find('div', attrs={'itemprop' : 'ratingCount'}).get_text().strip()
            kp = xbmcup.app.lang[34029] % (self.format_rating(rvalue), rvalue, rcount)
            movieInfo['desc'] += kp+"\n"
        except:
            pass

        try:
            div = soup.find('div', class_='full-panel').find('span', class_='imdb').find_all('div')
            rvalue = div[0].get_text().strip()
            rcount = div[1].get_text().strip()
            kp = xbmcup.app.lang[34030] % (self.format_rating(rvalue), rvalue, rcount)
            movieInfo['desc'] += kp+"\n"
        except:
            pass

        try:
            desc = soup.find('div', class_='full-story').get_text().strip()
            movieInfo['desc'] = '\n[COLOR blue]%s[/COLOR]\n%s' % (xbmcup.app.lang[34027], desc) + '\n' + movieInfo['desc']
        except:
            movieInfo['desc'] = traceback.format_exc()

        try:
            movieInfo['trailer'] = soup.find('li', attrs={'data-id' : "trailers"}).find('a').get('href')
        except:
            movieInfo['trailer'] = False

        return movieInfo

    def my_int(self, str):
        if(str == ''):
            return 0
        return int(str)

    def get_trailer(self, url):
        progress = xbmcgui.DialogProgress()
        progress.create(xbmcup.app.addon['name'])
        progress.update(0)
        html = self.load(url)
        movieInfo = {}
        movieInfo['error'] = False
        if not html:
            xbmcup.gui.message(xbmcup.app.lang[34031].encode('utf8'))
            progress.update(0)
            progress.close()
            return False

        progress.update(50)
        html = html.encode('utf-8')
        soup = xbmcup.parser.html(self.strip_scripts(html))

        link = self.decode_direct_media_url(soup.find('input', id='video5-link').get('value'))
        avail_quality = max(map(self.my_int, self.get_qualitys(link)))
        progress.update(100)
        progress.close()
        return self.format_direct_link(link, str(avail_quality))

    def format_desc_item(self, text):
        return re.compile(r'^([^:]+:)', re.S).sub('[COLOR blue]\\1[/COLOR] ', re.sub(r'\s+', ' ', text) )


    def strip_scripts(self, html):
        html = re.compile(r'<head[^>]*>(.*?)</head>', re.S).sub('<head></head>', html)
        #удаляет все теги <script></script> и их содержимое
        #сделал для того, что бы html parser не ломал голову на тегах в js
        return re.compile(r'<script[^>]*>(.*?)</script>', re.S).sub('', html)

    def format_rating(self, rating):
        rating = float(rating)
        if(rating == 0):
            return 'white'
        elif(rating > 7):
            return 'ff59C641'
        elif(rating > 4):
            return 'ffFFB119'
        else:
            return 'ffDE4B64'


    def format_quality(self, quality):
        if(quality == ''): return ''
        if(quality.find('1080') != -1):
            q = 'HD'
        elif(quality.find('720') != -1):
            q = 'HQ'
        elif(quality.find('480') != -1):
            q = 'SQ'
        else:
            q = 'LQ'

        qualitys = {'HD' : 'ff3BADEE', 'HQ' : 'ff59C641', 'SQ' : 'ffFFB119', 'LQ' : 'ffDE4B64'}
        if(q in qualitys):
            return "[COLOR %s][%s][/COLOR]" % (qualitys[q], quality)
        return ("[COLOR ffDE4B64][%s][/COLOR]" % quality if quality != '' else '')


    def get_page(self, soup):
        info = {'pagenum' : 0, 'maxpage' : 0}
        try:
            wrap  = soup.find('div', class_='navigation')
            info['pagenum'] = int(wrap.find('span', class_='').get_text())
            try:
                info['maxpage'] = len(wrap.find('a', class_='next'))
                if(info['maxpage'] > 0):
                    info['maxpage'] = info['pagenum']+1
            except:
                info['maxpage'] = info['pagenum']
                print traceback.format_exc()

        except:
            info['pagenum'] = 1
            info['maxpage'] = 1
            print traceback.format_exc()

        return info


    def get_page_search(self, soup):
        info = {'pagenum' : 0, 'maxpage' : 0}
        try:
            wrap  = soup.find('div', class_='navigation')
            current_page = wrap.find_all('span', class_='')
            info['pagenum'] = 1
            for cpage in current_page:
                if(cpage.get_text().find('...') == -1):
                    info['pagenum'] = int(cpage.get_text())
                    break

            try:
                clicks = wrap.find_all('span', class_='click')
                pages = []
                for page in clicks:
                    pages.append(int(page.get_text()))

                info['maxpage'] = max(pages)
            except:
                info['maxpage'] = info['pagenum']
                print traceback.format_exc()

        except:
            info['pagenum'] = 1
            info['maxpage'] = 1
            print traceback.format_exc()

        return info

    def get_movie_id(self, url):
        result = re.findall(r'\/([\d]+)\-', url)
        
        try:
            result = int(result[0])
        except:
            result = 0
            
        return result

class ResolveLink(xbmcup.app.Handler, HttpData):

    playerKeyParams = {
		'key' : '',
        'g'	  : 2,
        'p'	  : 293
    }

    def handle(self):
        item_dict = self.parent.to_dict()
        self.params = self.argv[0]
        movieInfo = self.get_movie_info(self.params['page_url'])
        item_dict['cover'] = movieInfo['cover']
        item_dict['title'] = self.params['file']
        folder = self.params['folder']
        resolution = self.params['resolution']
        if(len(movieInfo['movies']) > 0):
            for movies in movieInfo['movies']:
                for q in movies['movies']:
                    if(q == resolution):
                        if(movies['folder_title'] == folder or folder == ''):
                            for episode in movies['movies'][q]:
                                if episode[0].find( self.params['file'] ) != -1: 
                                    movie_id = self.get_movie_id( movieInfo['page_url'] )
                                    if movie_id != 0 and xbmcup.app.setting['watched_db'] == 'true' and xbmcup.app.setting['strm_url'] == 'true':
                                        Watched().set_watched( movie_id, season=episode[1], episode=episode[2] )
                                    return episode[0]
        return None

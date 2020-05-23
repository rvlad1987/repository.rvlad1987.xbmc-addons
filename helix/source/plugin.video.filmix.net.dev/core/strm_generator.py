# -*- coding: utf-8 -*-

import codecs
import json
import os
import re
import sys
import urllib
from collections import defaultdict
from urlparse import urlsplit, urlunsplit

import xbmc

import xbmcup
from core.defines import QUALITYS, SITE_URL, s_https, SITE_SCHEME, SITE_DOMAIN, PLUGIN_ID, IS_WIN_PLATFORM
from core.http import HttpData
from lib.counter import Counter
from xbmcup.app import compile_link
from xbmcup.log import notice

def encode_for_platform(file_name):
    if not IS_WIN_PLATFORM:
        return file_name.encode('utf8')
    else:
        return file_name


def int_quality(quality):
    if quality in ('1080p','1080 HD'):
        i_quality = 1080
    elif quality in ('1440','2K'):
        i_quality = 1440
    elif quality in ('2160p','4K UHD'):
        i_quality = 2160
    elif quality == '720p':
        i_quality = 720
    elif quality == '480p':
        i_quality = 480
    elif quality == '360p':
        i_quality = 360            
    else:
        i_quality = int(quality)
    return i_quality


class CancelSave(Exception):
    pass


class SaveMovieHandler(xbmcup.app.Handler, HttpData):
    def handle(self):
        params = self.argv[0] or {}

        self.lib_folder = xbmcup.app.setting['library_folder']
        if not self.lib_folder:
            xbmcup.gui.message(xbmcup.app.lang[30176].encode('utf-8'))
            return

        try:
            total = StreamGenerator(query_translate=True).from_url(params['url'])
            xbmcup.gui.message(xbmcup.app.lang[30181].format(total).encode('utf-8'))
        except CancelSave as exc:
            xbmcup.gui.message(exc.message or xbmcup.app.lang[30180].encode('utf-8'))


class WatchService(xbmcup.app.Service, HttpData):
    def handle(self):
        notice(PLUGIN_ID, 'Start filmix service')
        self.lib_folder = xbmcup.app.setting['library_folder']
        if not self.lib_folder:
            notice(PLUGIN_ID, xbmcup.app.lang[30176].encode('utf-8'))
            return

        for movie_type in ['Movies', 'Shows']:
            for folder in os.listdir(os.path.join(self.lib_folder, movie_type)):
                folder = os.path.join(self.lib_folder, movie_type, folder)
                if os.path.exists(os.path.join(folder, '_filmix_config.json')):
                    try:
                        total = StreamGenerator().from_folder(folder)
                        notice(PLUGIN_ID, '%s - %s' % (folder, total))
                    except CancelSave:
                        pass
        return 3600*6


class StreamGenerator(HttpData, object):
    config_file_name = '_filmix_config.json'

    is_serial = False

    def __init__(self, query_translate=False):
        self.config = {}
        self.query_translate = query_translate
        self.lib_folder = xbmcup.app.setting['library_folder']
        self.quality_settings = int(xbmcup.app.setting['quality'] or 4)
        self.default_quality = QUALITYS[self.quality_settings]

    def from_url(self, url):
        self.config['url'] = self.replace_host(url)
        return self.generate()

    def from_folder(self, folder):
        self.load_config(folder)
        self.config['url'] = self.replace_host(self.config['url'])
        return self.generate()

    @property
    def movieInfo(self):
        data = getattr(self, '_movieInfo', None)
        if not data:
            data = self.get_movie_info(self.config['url'])
            setattr(self, '_movieInfo', data)
            self.config['id'] = int(data['page_url'].rsplit('/', 1)[-1].split('-', 1)[0])
        return data

    def save_config(self):
        with codecs.open(os.path.join(self.content_folder, self.config_file_name), 'w', 'utf8') as fd:
            fd.write(json.dumps(self.config, ensure_ascii=False))

    def load_config(self, content_folder):
        with codecs.open(os.path.join(content_folder, self.config_file_name), 'r', 'utf8') as fd:
            data = fd.read()
        self.config = json.loads(data)

    def replace_host(self, url):
        url_split = urlsplit(url)
        return urlunsplit((SITE_SCHEME, SITE_DOMAIN, url_split[2], url_split[3], url_split[4]))

    def generate(self):
        self.is_serial = self.movieInfo.get('is_serial')
        if self.movieInfo['no_files']:
            raise CancelSave(self.movieInfo['no_files'])

        translate = self.choice_translation(self.movieInfo, self.query_translate)
        self.config['translate'] = translate
        seasons = self.prepare_episodes()[translate]
        total = 0
        for season, season_data in sorted(seasons.items(), key=lambda item: item[0]):
            for episode, qualities in sorted(season_data['episodes'].items(), key=lambda item: item[0]):
                quality, url = self.select_quality(qualities)
                file_name = self.generate_strm({'url': url,
                                                'season': season,
                                                'episode': episode,
                                                'quality': quality,
                                                'folder': season_data['folder']})
                total += 1
                if self.is_serial:
                    self.generate_episode_nfo(file_name)
                else:
                    self.generate_movie_nfo(file_name)
        if total:
            if self.is_serial:
                self.generate_tvshow_nfo()
            self.save_config()
            xbmc.executebuiltin('UpdateLibrary("video", "%s/")' % os.path.dirname(self.content_folder))
        return total

    def generate_strm(self, episode):
        external_file_name = os.path.splitext(os.path.basename(str(episode['url'])))[0]
        params = {}
        if self.is_serial:
            params = {'season': episode['season'], 'episode': episode['episode']}
        file_name = self.get_file_name(external_file_name, **params)

        file_url = compile_link('resolve', 'resolve', {
            'page_url': self.movieInfo['page_url'],
            'resolution': episode['quality'],
            'folder': episode['folder'],
            'file': external_file_name
        })
        url = sys.argv[0] + '?json' + urllib.quote_plus(json.dumps({
            'source': 'item',
            'folder': False,
            'parent': {},
            'url': file_url
        }))

        with open(os.path.join(self.content_folder, encode_for_platform(file_name)), 'w') as fd:
            fd.write(url)

        return file_name

    def generate_episode_nfo(self, episode_file_name):
        match = re.match(r'^.*? S(?P<season>.*?)E(?P<episode>.*?)\.strm$', episode_file_name)
        file_name = os.path.splitext(episode_file_name)[0] + '.nfo'
        params = self.movieInfo
        params.update(match.groupdict())
        content = u'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' \
                  u'<episodedetails>\n' \
                  u'<title>{title}</title>\n' \
                  u'<season>{season}</season>\n' \
                  u'<episode>{episode}</episode>\n' \
                  u'<thumb>{cover}</thumb>\n' \
                  u'</episodedetails>'.format(**params)

        with codecs.open(os.path.join(self.content_folder, encode_for_platform(file_name)), 'w', 'utf8') as fd:
            fd.write(content)

    def generate_tvshow_nfo(self):
        file_name = 'tvshow.nfo'
        content = u'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' \
                  u'<tvshow>\n' \
                  u'<title>{title}</title>\n' \
                  u'<originaltitle>{originaltitle}</originaltitle>\n' \
                  u'<tag>filmix</tag>\n' \
                  u'<thumb aspect="poster" preview="{cover}">{cover}</thumb>\n' \
                  u'<fanart url="">' \
                  u'<thumb preview="{fanart}">{fanart}</thumb>\n' \
                  u'</fanart>' \
                  u'</tvshow>'.format(**self.movieInfo)

        with codecs.open(os.path.join(self.content_folder, file_name), 'w', 'utf8') as fd:
            fd.write(content)

    def generate_movie_nfo(self, movie_file_name):
        file_name = os.path.splitext(movie_file_name)[0] + '.nfo'
        content = u'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' \
                  u'<movie>\n' \
                  u'<title>{title}</title>\n' \
                  u'<originaltitle>{originaltitle}</originaltitle>\n' \
                  u'<tag>filmix</tag>\n' \
                  u'<thumb aspect="poster" preview="{cover}">{cover}</thumb>\n' \
                  u'<fanart url="">' \
                  u'<thumb preview="{fanart}">{fanart}</thumb>\n' \
                  u'</fanart>' \
                  u'</movie>'.format(**self.movieInfo)

        with codecs.open(os.path.join(self.content_folder, encode_for_platform(file_name)), 'w', 'utf8') as fd:
            fd.write(content)

    def cleaned_name(self):
        return re.sub(r'[\\/:*?"<>|]', r'', self.movieInfo.get('originaltitle', '') or self.movieInfo['title'])

    def check_proplus_quality(self, quality):
        return int_quality(quality) < 1080 or self.movieInfo['is_proplus'] > 0

    @property
    def content_folder(self):
        result = getattr(self, '_content_folder', None)
        if not result:

            if self.is_serial:
                root_folder = 'Shows'
            else:
                root_folder = 'Movies'

            folder = os.path.join(self.lib_folder, root_folder)
            if not os.path.exists(folder):
                os.mkdir(folder)
            folder_name = self.cleaned_name()
            folder = os.path.join(folder, encode_for_platform(folder_name))
            if not os.path.exists(folder):
                os.mkdir(folder)
            result = folder
            setattr(self, '_content_folder', result)
        return result

    def get_file_name(self, file_name, **params):
        result = re.match(r'^(.*?)(?:s(?P<season>\d+))?(?:e(?P<episode>[\d-]+))?(?:_(?P<quality>\d+))?$', file_name)
        params['title'] = self.cleaned_name()
        if result:
            for key, value in result.groupdict().items():
                if value:
                    params[key] = value
        tmp_set = set(params.keys())
        if ('season' in tmp_set) or ('episode' in tmp_set):
            return u'{title} S{season}E{episode}.strm'.format(**params)
        return self.cleaned_name() + u'.strm'

    def select_quality(self, qualities):
        sorted_qualities = sorted(qualities.items(), key=lambda x: int_quality(x[0]), reverse=True)
        for quality, url in sorted_qualities:
            if int_quality(self.default_quality) >= int_quality(quality) and self.check_proplus_quality(quality):
                return quality, url
        return sorted_qualities[0]

    def choice_translation(self, movie_info, query=False):
        translations = Counter([f['translate'] for f in movie_info['movies']])
        translate = self.config.get('translate', translations.most_common()[0][0])
        if len(translations) > 1 and query:
            translations_select = []
            for trans, seasons in translations.most_common():
                if seasons > 1:
                    translations_select.append((trans, xbmcup.app.lang[30179].format(trans, seasons)))
                else:
                    translations_select.append((trans, trans))
            translate = xbmcup.gui.select(movie_info['title'], translations_select)
            if not translate:
                raise CancelSave()
        return translate

    def prepare_episodes(self):
        translations = defaultdict(lambda: defaultdict(lambda: dict(folder='', episodes=defaultdict(dict))))
        for folder in self.movieInfo['movies']:
            for quality, movies in folder['movies'].items():
                for movie in movies:
                    translations[folder['translate']][movie[1]]['folder'] = folder['folder_title']
                    translations[folder['translate']][movie[1]]['episodes'][movie[2]][quality] = movie[0]
        return translations

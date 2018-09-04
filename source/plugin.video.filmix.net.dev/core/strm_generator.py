# -*- coding: utf-8 -*-

import codecs
import json
import os
import re
import sys
import urllib
from collections import Counter

import xbmcup
from core.defines import QUALITYS
from core.http import HttpData


class CancelSave(Exception):
    pass


class STRMGenerator(xbmcup.app.Handler, HttpData):
    def handle(self):
        params = self.argv[0] or {}

        self.lib_folder = xbmcup.app.setting['library_folder']
        if not self.lib_folder:
            xbmcup.gui.message(xbmcup.app.lang[30176].encode('utf-8'))
            return

        self.movieInfo = self.get_movie_info(params['url'])
        # xbmc.log(json.dumps(self.movieInfo, indent=2), level=7)

        try:

            if self.movieInfo.get('is_serial'):
                episodes = self.get_episodes()

                self.folder = os.path.join(self.lib_folder, 'Shows',
                                           self.movieInfo.get('originaltitle', '') or self.movieInfo['title'])
                if not os.path.exists(self.folder):
                    os.mkdir(self.folder)

                self.generate_tvshow_nfo()

                for episode in episodes:
                    episode_file_name = self.generate_strm(episode)
                    self.generate_episode_nfo(episode_file_name)
                xbmcup.gui.message(xbmcup.app.lang[30181].format(len(episodes)).encode('utf-8'))
            else:
                episodes = self.get_episodes()
                if episodes:
                    self.folder = os.path.join(self.lib_folder, 'Movies',
                                               self.movieInfo.get('originaltitle', '') or self.movieInfo['title'])
                    if not os.path.exists(self.folder):
                        os.mkdir(self.folder)

                    movie_file_name = self.generate_strm(episodes[0])
                    self.generate_movie_nfo(movie_file_name)

        except CancelSave:
            xbmcup.gui.message(xbmcup.app.lang[30180].encode('utf-8'))

    def get_episodes(self):
        quality_settings = int(xbmcup.app.setting['quality'] or 4)
        default_quality = QUALITYS[quality_settings]

        result = []
        current_translation = self.choice_translation(self.movieInfo)
        if not current_translation:
            raise CancelSave()

        for folder in filter(lambda f: f['translate'] == current_translation, self.movieInfo['movies']):
            season_episodes = []
            max_episode = 1
            for quality, movies in folder['movies'].items():
                for movie in movies:
                    if max_episode < movie[2]:
                        max_episode = movie[2]

            for episode_num in xrange(1, max_episode + 1):
                for quality in sorted(folder['movies'].keys(),
                                      key=lambda x: self.int_quality(x),
                                      reverse=True):

                    if self.int_quality(default_quality) >= self.int_quality(quality) \
                            and self.check_proplus_quality(quality):
                        for movie in folder['movies'][quality]:

                            if episode_num == movie[2] and episode_num not in season_episodes:
                                season_episodes.append(movie[2])
                                result.append({
                                    'url': movie[0],
                                    'season': movie[1],
                                    'episode': movie[2],
                                    'quality': quality,
                                    'folder': folder['folder_title'],
                                })
        return result

    def generate_strm(self, episode):
        external_file_name = os.path.splitext(os.path.basename(str(episode['url'])))[0]
        file_name = self.get_name(external_file_name)
        file_url = self.resolve('resolve', {
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
        with open(os.path.join(self.folder, file_name), 'w') as fd:
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
                  u'<art><thumb>{cover}</thumb></art>\n' \
                  u'</episodedetails>'.format(**params)
        with codecs.open(os.path.join(self.folder, file_name), 'w', 'utf8') as fd:
            fd.write(content)

    def generate_tvshow_nfo(self):
        file_name = 'tvshow.nfo'
        content = u'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' \
                  u'<tvshow>\n' \
                  u'<title>{title}</title>\n' \
                  u'<originaltitle>{originaltitle}</originaltitle>\n' \
                  u'<thumb aspect="poster" preview="{cover}">{cover}</thumb>\n' \
                  u'<fanart url="">' \
                  u'<thumb preview="{fanart}">{fanart}</thumb>\n' \
                  u'</fanart>' \
                  u'</tvshow>'.format(**self.movieInfo)
        with codecs.open(os.path.join(self.folder, file_name), 'w', 'utf8') as fd:
            fd.write(content)

    def generate_movie_nfo(self, movie_file_name):
        file_name = os.path.splitext(movie_file_name)[0] + '.nfo'
        content = u'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' \
                  u'<movie>\n' \
                  u'<title>{title}</title>\n' \
                  u'<originaltitle>{originaltitle}</originaltitle>\n' \
                  u'<thumb aspect="poster" preview="{cover}">{cover}</thumb>\n' \
                  u'<fanart url="">' \
                  u'<thumb preview="{fanart}">{fanart}</thumb>\n' \
                  u'</fanart>' \
                  u'</movie>'.format(**self.movieInfo)
        with codecs.open(os.path.join(self.folder, file_name), 'w', 'utf8') as fd:
            fd.write(content)

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

    def check_proplus_quality(self, quality):
        return self.int_quality(quality) < 1080 or self.movieInfo['is_proplus'] > 0

    def get_name(self, file_name):
        result = re.match(r'^(.*?)(?:s(?P<s>\d+))?(?:e(?P<e>[\d-]+))?(?:_(?P<q>\d+))?$', file_name)
        if result and result.groupdict()['s'] and result.groupdict()['e']:
            title = self.movieInfo.get('originaltitle', '') or self.movieInfo['title']
            return u'{title} S{s}E{e}.strm'.format(title=title.encode('utf8'), **result.groupdict(''))
        return file_name

    @staticmethod
    def choice_translation(movieInfo):
        translations = Counter([f['translate'] for f in movieInfo['movies']])
        if len(translations) > 1:
            translations_select = []
            for trans, seasons in translations.most_common():
                if seasons > 1:
                    translations_select.append((trans, xbmcup.app.lang[30179].format(trans, seasons)))
                else:
                    translations_select.append((trans, trans))
            return xbmcup.gui.select(movieInfo['title'], translations_select)
        else:
            return translations.most_common()[0][0]

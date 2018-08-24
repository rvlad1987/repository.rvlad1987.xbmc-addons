# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import codecs
import json
import os
import re
import sys
import urllib

import xbmcup
from core.defines import QUALITYS
from core.http import HttpData


class STRMGenerator(xbmcup.app.Handler, HttpData):
    def handle(self):
        params = self.argv[0] or {}

        self.lib_folder = xbmcup.app.setting['library_folder']
        if not self.lib_folder:
            xbmcup.gui.message(xbmcup.app.lang[30176])
            return

        self.movieInfo = self.get_movie_info(params['url'])

        self.folder = os.path.join(self.lib_folder, 'Shows',
                                   self.movieInfo.get('originaltitle', '') or self.movieInfo['title'])
        if not os.path.exists(self.folder):
            os.mkdir(self.folder)

        self.generate_tvshow_nfo()
        episodes = self.get_episodes()
        for episode in episodes:
            episode_file_name = self.generate_strm(episode)
            self.generate_episode_nfo(episode_file_name)

    def get_episodes(self):
        quality_settings = int(xbmcup.app.setting['quality'] or 4)
        default_quality = QUALITYS[quality_settings]

        result = []
        for folder in self.movieInfo['movies']:
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
        content = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' \
                  '<episodedetails>\n' \
                  '<title>{title}</title>\n' \
                  '<season>{season}</season>\n' \
                  '<episode>{episode}</episode>\n' \
                  '<art><thumb>{cover}</thumb></art>\n' \
                  '</episodedetails>'.format(**params)
        with codecs.open(os.path.join(self.folder, file_name), 'w', 'utf8') as fd:
            fd.write(content)

    def generate_tvshow_nfo(self):
        file_name = 'tvshow.nfo'
        content = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' \
                  '<tvshow>\n' \
                  '<title>{title}</title>\n' \
                  '<originaltitle>{originaltitle}</originaltitle>\n' \
                  '<thumb aspect="poster" preview="{cover}">{cover}</thumb>\n' \
                  '<fanart url="">' \
                  '<thumb preview="{fanart}">{fanart}</thumb>\n' \
                  '</fanart>' \
                  '</tvshow>'.format(**self.movieInfo)
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
            return '{title} S{s}E{e}.strm'.format(title=title.encode('utf8'), **result.groupdict(''))
        return file_name

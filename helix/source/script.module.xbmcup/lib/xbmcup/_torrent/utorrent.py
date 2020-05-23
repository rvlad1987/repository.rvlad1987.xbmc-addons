# -*- coding: utf-8 -*-

__author__ = 'hal9000'
__all__ = ['UTorrent']

import re
import os
import urllib

from ..net import http


class UTorrent(object):
    def __init__(self, login, password, host, port=None, url=None):
        self._login, self._password, self._url = login, password, None
        self._url = 'http://' + host + ((':' + str(port)) if port else '') + '/gui/'
        self._auth, self._cache = None, dict(id=None, labels=None, torrents=None)
        self._str2obj = (lambda x: int(x) if x else 0, lambda x: True if x == 'true' else False, lambda x: x)

    # API

    def settings(self, settings=None):
        if isinstance(settings, dict):
            # set
            action = 'action=setsetting'
            for key, value in settings.iteritems():
                action += '&s=' + key + '&v='
                if isinstance(value, unicode):
                    # TODO: Make the normal codec (e.g. latin or utf8)
                    action += urllib.quote(value.encode('windows-1251'))
                elif isinstance(value, bool):
                    action += '1' if value else '0'
                else:
                    action += urllib.quote(str(value))
            return True if self._http(action) else False

        else:
            # get
            response = self._http('action=getsettings')
            if not response:
                return None
            res = {'build': response['build']}
            res.update(dict([(x[0], self._str2obj[x[1]](x[2])) for x in response['settings']]))
            return res

    def labels(self):
        return sorted(self._cache['labels']) if self._list() else None

    def torrents(self):
        return self._cache['torrents'].values() if self._list() else None

    def files(self, *hash):
        response = self._http('action=getfiles&hash=' + '&hash='.join(hash))
        if not response:
            return None
        r = dict([(x[0], [self._file(y, i) for i, y in enumerate(x[1])]) for x in zip(response['files'][::2], response['files'][1::2])])
        return r[hash[0]] if len(hash) == 1 else r

    def properties(self, hash, properties=None):
        if isinstance(properties, dict):
            # set
            if 'trackers' in properties:
                properties['trackers'] = ''.join([x + '\r\n\r\n' for x in properties['trackers']])
            for tag in ('superseed', 'dht', 'pex', 'seed_override'):
                if tag in properties:
                    properties[tag] = self._prop(properties[tag])
            action = 'action=setprops&hash=' + hash
            for key, value in properties.iteritems():
                action += '&s=' + key + '&v=' + urllib.quote(str(value))
            return True if self._http(action) else False

        else:
            # get
            response = self._http('action=getprops&hash=' + hash)
            if not response:
                return None

            props = response['props'][0]
            props['trackers'] = [y for y in [x.strip() for x in props['trackers'].split('\n')] if y]
            for tag in ('superseed', 'dht', 'pex', 'seed_override'):
                props[tag] = self._prop(props[tag])
            return props

    def start(self, *hash, **kwargs):
        action = 'forcestart' if kwargs.get('force') else 'start'
        return True if self._http('action=' + action + '&hash=' + '&hash='.join(hash)) else False

    def stop(self, *hash):
        return True if self._http('action=stop&hash=' + '&hash='.join(hash)) else False

    def pause(self, *hash):
        return True if self._http('action=pause&hash=' + '&hash='.join(hash)) else False

    def unpause(self, *hash):
        return True if self._http('action=unpause&hash=' + '&hash='.join(hash)) else False

    def recheck(self, *hash):
        return True if self._http('action=recheck&hash=' + '&hash='.join(hash)) else False

    def remove(self, *hash, **kwargs):
        action = 'removedata' if kwargs.get('data') else 'remove'
        return True if self._http('action=' + action + '&hash=' + '&hash='.join(hash)) else False

    def priority(self, hash, priority, *files):
        return True if self._http('action=priority&hash=' + hash + '&p=' + str(self.__priority(priority))
                                  + '&f=' + '&f='.join([str(x) for x in files])) else False

    def add_url(self, url, dirname=None):
        return self._add('action=add-url&s=' + url, None, dirname)

    def add_file(self, filename, dirname=None):
        return self.add_torrent(file(filename, 'rb').read(), dirname, os.path.basename(filename))

    def add_torrent(self, torrent, dirname=None, filename='default.torrent'):
        return self._add('action=add-file', {'torrent_file': (filename, torrent)}, dirname)


    # PRIVATE

    def _http(self, action, post=None):
        """
        Documentation:
        http://www.utorrent.com/intl/en/community/developers/webapi
        http://forum.utorrent.com/viewtopic.php?id=25661
        """
        if not self._token():
            return None
        kwargs = dict(
            cookies = {'GUID': self._auth[0]},
            auth = http.auth.HTTPBasicAuth(self._login, self._password)
        )
        try:
            if post:
                kwargs['files'] = post
                response = http.post(self._url + '?token=' + self._auth[1] + '&' + action, **kwargs)
            else:
                response = http.get(self._url + '?token=' + self._auth[1] + '&' + action, **kwargs)
            return response.json()
        except http.exceptions.RequestException:
            return None

    def _token(self):
        if self._auth:
            return True
        try:
            response = http.get(self._url + 'token.html', auth=http.auth.HTTPBasicAuth(self._login, self._password))
        except http.exceptions.RequestException:
            return False
        else:
            r = re.compile("<div[^>]+id='token'[^>]*>([^<]+)</div>").search(response.text)
            if not r:
                return False
            try:
                self._auth = response.cookies['GUID'], r.group(1).strip()
            except KeyError:
                return False
            return True

    def _add(self, action, post, dirname):
        old_flag = None
        if dirname:
            setting = self.settings()
            if not setting:
                return False
            old_flag, old_dirname = setting['dir_active_download_flag'], setting['dir_active_download']
            if isinstance(dirname, unicode):
                # TODO: Make the normal codec
                dirname = dirname.encode('windows-1251')
            if not self.settings({'dir_active_download_flag': True, 'dir_active_download': dirname}):
                return False

        r = self._http(action, post)

        if old_flag is not None:
            # TODO: Make the normal codec
            self.settings({'dir_active_download_flag': old_flag, 'dir_active_download': old_dirname.encode('windows-1251')})

        return True if r else False

    def _list(self):
        action = 'list=1'
        if self._cache['id']:
            action += '&cid=' + self._cache['id']

        response = self._http(action)
        if not response:
            return False

        self._cache['id'] = response['torrentc']
        self._cache['labels'] = response['label']

        if 'torrents' in response:
            self._cache['torrents'] = dict([(x[0], self._torrent(x)) for x in response['torrents']])
        else:
            for hash in [x for x in response['torrentm'] if x in self._cache['torrents']]:
                del self._cache['torrents'][hash]
            self._cache['torrents'].update(dict([(x[0], self._torrent(x)) for x in response['torrentp']]))

        return True

    def _status(self, status):
        res, code = [], 1
        for name in ('started', 'checking', 'start_after_check', 'checked', 'error', 'paused', 'queued', 'loaded'):
            if bool(status & code):
                res.append(name)
                code *= 2
        return res

    def _priority(self, priority):
        if priority == 'stop':
            return 0
        elif priority == 'low':
            return 1
        elif priority == 'normal':
            return 2
        elif priority == 'high':
            return 3
        elif priority == 0:
            return 'stop'
        elif priority == 1:
            return 'low'
        elif priority == 3:
            return 'high'
        else:
            return 'normal'

    def _prop(self, prop):
        if prop == -1:
            return None
        elif prop == 0:
            return False
        elif prop == 1:
            return True
        elif prop is None:
            return -1
        elif not prop:
            return 0
        else:
            return 1

    def _torrent(self, raw):
        return dict(
            hash = raw[0],
            status = self._status(raw[1]),
            name = raw[2],
            size = raw[3],
            progress = raw[4]/10.0,
            downloaded = raw[5],
            uploaded = raw[6],
            ratio = raw[7]/1000.0,
            ul_speed = raw[8],
            dl_speed = raw[9],
            eta = raw[10],
            label = raw[11],
            peers_connected = raw[12],
            peers_total = raw[13],
            seeds_connected = raw[14],
            seeds_total = raw[15],
            availability = raw[16]/65535.0,
            queue_order = raw[17],
            dl_remain = raw[18],
            url = raw[19],
            rss = raw[20],
            message = raw[21],
            unk_hash = raw[22],
            added = raw[23],
            finished = raw[24],
            unk_str = raw[25],
            dirname = raw[26]
        )

    def _file(self, raw, index):
        return dict(
            index = index,
            name = raw[0],
            size = raw[1],
            downloaded = raw[2],
            priority = self._priority(raw[3]),
            progress = 100 if not raw[1] else round(float(raw[2])/100*raw[1], 1)
        )

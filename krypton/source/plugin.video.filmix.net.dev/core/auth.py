# -*- coding: utf-8 -*-

import pickle, re
import xbmcup.app, xbmcup.system, xbmcup.net
from defines import *

class Auth:
    def __init__(self):
        self.success = 'AUTHORIZED'#'AUTH_OK'
        self.cookie_file = xbmcup.system.fs('sandbox://'+COOKIE_FILE).decode('utf-8')
        self.login = xbmcup.app.setting['username']
        self.password = xbmcup.app.setting['password']
        try:
            self.per_page_news = int(xbmcup.app.setting['per_page_news']) * 15 + 15
        except:
            self.per_page_news = 15
        #xbmcup.system.fs.delete('sandbox://'+COOKIE_FILE)

    def autorize(self):
        try:
            if(self.login == '' or  self.password == ''):
                self.reset_auth()
                return False
            url = '%s/engine/ajax/user_auth.php' % (SITE_URL)
            data = {'login' : 'submit', 'login_name' : self.login, 'login_password' : self.password, 'login_not_save' : '1'}
            response = xbmcup.net.http.post(url, data, verify=False)
            response.cookies.set('per_page_news', str(self.per_page_news), domain='.'+SITE_DOMAIN)
        except xbmcup.net.http.exceptions.RequestException:
            return False
        else:
            return self._check_response(response)

    def _check_response(self, response):
        is_logged = response.text == self.success
        if(is_logged):
            self.save_cookies(response.cookies)
            xbmcup.app.setting['is_logged'] = 'true'
        else:
            xbmcup.system.fs.delete('sandbox://'+COOKIE_FILE)
        return is_logged


    def save_cookies(self, cookiejar):
        with open(self.cookie_file, 'wb') as f:
            pickle.dump(cookiejar, f)
        f.close()


    def get_cookies(self):
        if(xbmcup.system.fs.exists('sandbox://'+COOKIE_FILE)):
            with open(self.cookie_file, 'rb') as f:
                cook = pickle.load(f)
                f.close()
                return cook
        return None


    def reset_auth(self, reset_settings=False):
        xbmcup.app.setting['is_logged'] = 'false'
        if reset_settings == True:
            xbmcup.app.setting['username'] = ''
            xbmcup.app.setting['password'] = ''
        xbmcup.system.fs.delete('sandbox://'+COOKIE_FILE)


    def check_auth(self, page):
        reg = re.compile('/users/index/logout', re.S).findall(page)
        return len(reg) > 0
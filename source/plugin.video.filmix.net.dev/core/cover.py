# -*- coding: utf-8 -*-

import xbmcup.system
from xbmc import skinHasImage
from defines import *

icons_path = 'home://addons/'+PLUGIN_ID+'/resources/media/icons/'

treetv = xbmcup.system.fs(icons_path+'/icon.png')

def get_image(image, alt_image = None):
    if not alt_image:
        alt_image = treetv
    return image if skinHasImage(image) else alt_image

search  = get_image( 'DefaultAddonsSearch.png',     xbmcup.system.fs(icons_path+'/search.png') )
info    = get_image( 'DefaultIconWarning.png',   xbmcup.system.fs(icons_path+'/info.png') )
next    = None #get_image('osd/fullscreen/buttons/forward.png', xbmcup.system.fs(icons_path+'/next.png'))
prev    = None #xbmcup.system.fs(icons_path+'/prev.png')

res_icon = {}
res_icon['360']     = xbmcup.system.fs(icons_path+'/360.png')
res_icon['480']     = xbmcup.system.fs(icons_path+'/480.png')
res_icon['720']     = xbmcup.system.fs(icons_path+'/720.png')
res_icon['1080']    = xbmcup.system.fs(icons_path+'/1080.png')
res_icon['default'] = xbmcup.system.fs(icons_path+'/default.png')


bookmarks = get_image('DefaultFavourites.png')
collections = get_image('DefaultSets.png')
news = get_image('DefaultTags.png')
empty = get_image('OverlayUnwatched.png')

films = get_image('DefaultMovies.png')
serialy = get_image('DefaultTVShows.png')
watchlater = get_image('DefaultRecentlyAddedMovies.png')

rubrics = get_image('DefaultStudios.png')
genre = get_image('DefaultGenre.png')
years = get_image('DefaultYear.png') # DefaultMusicYears.png
qualitys = get_image('DefaultPicture.png')
awards = get_image('DefaultAddonLyrics.png')
productions = get_image('DefaultCountry.png')

  
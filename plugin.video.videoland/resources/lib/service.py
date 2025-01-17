import glob, hashlib, io, json, os, re, requests, shutil, time, xbmc, xbmcgui, xbmcvfs

from resources.lib.api import api_get_series_nfo, api_list_watchlist, api_vod_season, api_vod_seasons
from resources.lib.base.l1.constants import ADDON_ID, ADDON_PROFILE, PROVIDER_NAME
from resources.lib.base.l2 import settings
from resources.lib.base.l2.log import log
from resources.lib.base.l3.util import check_addon, check_loggedin, check_key, clean_library, encode_obj, json_rpc, load_file, md5sum, scan_library, txt2filename, write_file
from resources.lib.base.l5.api import api_get_vod_by_type
from resources.lib.constants import CONST_IMAGES, CONST_LIBRARY
from resources.lib.util import plugin_process_watchlist, plugin_vod_subscription_filter
from urllib.parse import urlencode
from xml.dom.minidom import *

def main():
    log('Start Dut-IPTV Library Updater service for {}'.format(PROVIDER_NAME))
    loop = True

    if not os.path.isdir(os.path.join(ADDON_PROFILE, "movies")):
        os.makedirs(os.path.join(ADDON_PROFILE, "movies"))

    if not os.path.isdir(os.path.join(ADDON_PROFILE, "shows")):
        os.makedirs(os.path.join(ADDON_PROFILE, "shows"))

    while loop == True:
        start = int(time.time())

        update_library()

        end = int(time.time())

        if xbmc.Monitor().waitForAbort((start - end) + 3600):
            loop = False

def update_library():
    #if check_loggedin(ADDON_ID):
    librarysettings = {}
    librarysettings['library_movies'] = settings.getInt(key='library_movies')
    librarysettings['library_shows'] = settings.getInt(key='library_shows')
    movies_added = False
    shows_added = False
    movies_removed = False
    shows_removed = False

    if librarysettings['library_movies'] == 0:
        for file in glob.glob(os.path.join(ADDON_PROFILE, "movies", "*.*")):
            movies_removed = True
            os.remove(file)

    if librarysettings['library_shows'] == 0:
        for file in glob.glob(os.path.join(ADDON_PROFILE, "shows", "*.*")):
            shows_removed = True
            os.remove(file)

    if librarysettings['library_movies'] > 0 or librarysettings['library_shows'] > 0:
        log('Update Dut-IPTV Library for {}'.format(PROVIDER_NAME))

        skiplist = []
        skiplist2 = []

        if librarysettings['library_movies'] == 1 or librarysettings['library_shows'] == 1:
            data = api_list_watchlist(continuewatch=0)

            if data:
                processed = plugin_process_watchlist(data=data, continuewatch=0)

                if processed:
                    for ref in processed:
                        currow = processed[ref]

                        if currow['type'] == 'movie':
                            skiplist.append(ref)
                        elif currow['type'] == 'series':
                            skiplist2.append(ref)

        movie_list = []

        if librarysettings['library_movies'] > 0:
            for type in CONST_LIBRARY['movies']:
                if settings.getBool(key='library_movies_' + str(type), default=False):
                    result = create_stream(type, 'movies', librarysettings['library_movies'], skiplist)
                    movie_list.extend(result['list'])

                    if result['add'] == True:
                        movies_added = True

        for file in glob.glob(os.path.join(ADDON_PROFILE, "movies", "*.*")):
            filename = os.path.basename(file)

            if not filename in movie_list:
                movies_removed = True

                try:
                    os.remove(file)
                except:
                    pass

        shows_list = []
        remove_shows = []
        remove_shows2 = []

        if librarysettings['library_shows'] > 0:
            if librarysettings['library_shows'] == 2:
                api_get_series_nfo()

            for type in CONST_LIBRARY['shows']:
                if settings.getBool(key='library_shows_' + str(type), default=False):
                    result = create_stream(type, 'shows', librarysettings['library_shows'], skiplist2)
                    shows_list.extend(result['list'])

                    if result['add'] == True:
                        shows_added = True

        for file in glob.glob(os.path.join(ADDON_PROFILE, "shows", "*"), recursive=False):
            filename = os.path.basename(os.path.normpath(file))

            if not filename in shows_list:
                shows_removed = True

                try:
                    os.remove(os.path.join(ADDON_PROFILE, "shows", filename, 'tvshow.nfo'))
                    remove_shows.append(os.path.join(ADDON_PROFILE, "shows", filename, ""))
                except:
                    pass

        for file in glob.glob(os.path.join(ADDON_PROFILE, "shows", "*", "*", "*.*"), recursive=False):
            filename = os.path.basename(file)

            if not filename in shows_list:
                shows_removed = True

                try:
                    os.remove(file)
                except:
                    pass

        index = 0

        for root, dirs, files in os.walk(os.path.join(ADDON_PROFILE, "shows")):
            for dir in dirs:
                newDir = os.path.join(root, dir)
                index += 1

                try:
                    os.removedirs(newDir)
                    remove_shows2.append(os.path.join(newDir, ""))
                    shows_removed = True
                except:
                    pass

        for removal in remove_shows:
            clean_library(show_dialog=False, path=removal)
            #Manual DB removal?

        for removal2 in remove_shows2:
            clean_library(show_dialog=False, path=removal2)
            #Manual DB removal?

        if movies_added == True or shows_added == True:
            if movies_added == True:
                scan_library(show_dialog=False, path=os.path.join(ADDON_PROFILE, "movies", ""))

            if shows_added == True:
                scan_library(show_dialog=False, path=os.path.join(ADDON_PROFILE, "shows", ""))

    if movies_removed == True or shows_removed == True:
        clean_library(show_dialog=False)
        #clean_library(show_dialog=False, path=os.path.join(ADDON_PROFILE, "movies", ""))
        #clean_library(show_dialog=False, path=os.path.join(ADDON_PROFILE, "shows", ""))

def create_stream(type, type2, skip, skiplist):
    return_list = []
    subscription_filter = plugin_vod_subscription_filter()
    data = api_get_vod_by_type(type=type, character=None, genre=None, subscription_filter=subscription_filter, menu=0)
    count = 0
    progress_abs = 0
    progress_rel = 0
    total = 0
    add = False

    if data:
        #pDialog = xbmcgui.DialogProgressBG()
        #pDialog.create(str(PROVIDER_NAME).capitalize(), 'Update {}...'.format(type))
        total = len(data)

        if skip == 1 and skiplist:
            total = len(skiplist)

        for currow in data:
            row = data[currow]

            if skip == 1 and not row['id'] in skiplist:
                continue

            id = str(row['id'])
            label = str(row['title'])
            year = 0

            filename = txt2filename(txt=str(label), chr_set='printable', no_ext=True)

            if check_key(row, 'datum'):
                if len(str(row['datum'])) > 0:
                    year = int(str(row['datum'])[:4])

            if year > 0:
                if not str(year) in filename:
                    filename += ' ({})'.format(year)

            if type2 == 'shows':
                if row['id'] in skiplist:
                    data2 = api_vod_seasons(type=type, id=id, raw=True, github=False, use_cache=False)
                    no_cache = True
                else:
                    data2 = api_vod_seasons(type=type, id=id, raw=True, github=True)
                    no_cache = False

                if data2:
                    if not os.path.isdir(os.path.join(ADDON_PROFILE, "shows", filename)):
                        os.makedirs(os.path.join(ADDON_PROFILE, "shows", filename))

                    return_list.append(filename)

                    episodes = {}
                    seasons = {}

                    seriesid = id[1:]

                    seriesinfo = {}
                    seriesinfo['title'] = data2['data']['title']
                    seriesinfo['id'] = data2['data']['ref']
                    seriesinfo['duration'] = ''
                    seriesinfo['description'] = ''
                    seriesinfo['category'] = ''
                    seriesinfo['datum'] = ''
                    seriesinfo['icon_poster'] = ''
                    seriesinfo['icon_still'] = ''
                    seriesinfo['allnumeric'] = 1

                    if check_key(data2['data'], 'description'):
                        seriesinfo['description'] = data2['data']['description']

                    if check_key(data2['data'], 'genres'):
                        seriesinfo['category'] = data2['data']['genres']

                    if check_key(data2['data'], 'year'):
                        seriesinfo['datum'] = str(data2['data']['year']) + '0101'

                    if check_key(data2['data'], 'poster'):
                        seriesinfo['icon_poster'] = data2['data']['poster']

                    if check_key(data2['data'], 'still'):
                        seriesinfo['icon_still'] = data2['data']['still']

                    for item in data2['data']['details']:
                        row = data2['data']['details'][item]

                        if row['type'] == 'episode':
                            episodes[row['ref']] = {}
                            episodes[row['ref']]['title'] = row['title']
                            episodes[row['ref']]['id'] = row['id']

                            episodes[row['ref']]['position'] = ''
                            episodes[row['ref']]['description'] = ''
                            episodes[row['ref']]['duration'] = ''
                            episodes[row['ref']]['icon_poster'] = ''
                            episodes[row['ref']]['icon_still'] = ''
                            episodes[row['ref']]['datum'] = ''

                            if check_key(row, 'position'):
                                episodes[row['ref']]['position'] = re.sub("[^0-9]", "", str(row['position']))

                            if len(str(episodes[row['ref']]['position'])) == 0:
                                episodes[row['ref']]['position'] = 1

                            if check_key(row, 'description'):
                                episodes[row['ref']]['description'] = row['description']

                            if check_key(row, 'runtime'):
                                episodes[row['ref']]['duration'] = row['runtime']

                            if check_key(row, 'poster'):
                                episodes[row['ref']]['icon_poster'] = row['poster']

                            if check_key(row, 'still'):
                                episodes[row['ref']]['icon_still'] = row['still']

                        elif row['type'] == 'season':
                            if not check_key(row, 'refs'):
                                if no_cache == True:
                                    data3 = api_vod_season(series=id, id=str(seriesid) + '###' + str(row['id']), raw=True, use_cache=False)
                                else:
                                    data3 = api_vod_season(series=id, id=str(seriesid) + '###' + str(row['id']), raw=True)

                                for item in data3['data']['details']:
                                    row2 = data3['data']['details'][item]

                                    if row2['type'] == 'episode':
                                        episodes[row2['ref']] = {}
                                        episodes[row2['ref']]['title'] = row2['title']
                                        episodes[row2['ref']]['id'] = row2['id']

                                        episodes[row2['ref']]['position'] = ''
                                        episodes[row2['ref']]['description'] = ''
                                        episodes[row2['ref']]['duration'] = ''
                                        episodes[row2['ref']]['icon_poster'] = ''
                                        episodes[row2['ref']]['icon_still'] = ''
                                        episodes[row2['ref']]['datum'] = ''

                                        if check_key(row2, 'position'):
                                            episodes[row2['ref']]['position'] = re.sub("[^0-9]", "", str(row2['position']))

                                        if len(str(episodes[row2['ref']]['position'])) == 0:
                                            episodes[row2['ref']]['position'] = 1

                                        if check_key(row2, 'description'):
                                            episodes[row2['ref']]['description'] = row2['description']

                                        if check_key(row2, 'runtime'):
                                            episodes[row2['ref']]['duration'] = row2['runtime']

                                        if check_key(row2, 'poster'):
                                            episodes[row2['ref']]['icon_poster'] = row2['poster']

                                        if check_key(row2, 'still'):
                                            episodes[row2['ref']]['icon_still'] = row2['still']

                                    elif row['type'] == 'season':
                                        if check_key(row2, 'refs') and row['id'] == row2['id']:
                                            row['refs'] = row2['refs']

                            if check_key(row, 'refs'):
                                seasons[row['ref']] = {}
                                seasons[row['ref']]['title'] = re.sub("[^0-9]", "", str(row['title']).strip())
                                seasons[row['ref']]['origtitle'] = str(row['title']).strip()

                                if not str(row['title']).strip() == str(seasons[row['ref']]['title']).strip():
                                    seriesinfo['allnumeric'] = 0

                                if len(str(seasons[row['ref']]['title'])) == 0:
                                    seasons[row['ref']]['title'] = 1

                                if len(str(seasons[row['ref']]['origtitle'])) == 0:
                                    seasons[row['ref']]['origtitle'] = 1

                                seasons[row['ref']]['refs'] = row['refs']
                                seasons[row['ref']]['id'] = row['id']
                                seasons[row['ref']]['position'] = row['position']

                    if len(seasons) == 0:
                        shutil.rmtree(os.path.join(ADDON_PROFILE, "shows", filename))
                    else:
                        seriesinfo['seasons'] = {}

                        for season in seasons:
                            row = seasons[season]

                            if seriesinfo['allnumeric'] == 1:
                                season_path = os.path.join(ADDON_PROFILE, "shows", filename, 'Season ' + str(row['origtitle']))
                            else:
                                season_path = os.path.join(ADDON_PROFILE, "shows", filename, 'Season ' + str(row['position']))

                            if not os.path.isdir(season_path):
                                os.makedirs(season_path)

                            for ref in row['refs']:
                                season_ep = '.'
                                filename_ep = filename

                                if len(str(row['title'])) > 0:
                                    if seriesinfo['allnumeric'] == 1:
                                        season_title = str(row['origtitle'])
                                    else:
                                        season_title = str(row['position'])

                                    if season_title.isnumeric():
                                        season_ep += 'S{:02d}'.format(int(season_title))
                                    else:
                                        season_ep += 'S{}'.format(season_title)

                                if len(str(episodes[ref]['position'])) > 0:
                                    season_ep += 'E{:02d}'.format(int(episodes[ref]['position']))

                                if len(str(season_ep)) > 1:
                                    filename_ep += str(season_ep)

                                return_list.append(filename_ep + '.strm')
                                return_list.append(filename_ep + '.nfo')
                                filename_ep = os.path.join(season_path, filename_ep)
                                seriesinfo['seasons'][str(row['position'])] = str(row['origtitle'])

                                if create_strm_file(filename_ep, 'E' + str(seriesid) + '###' + str(row['id']) + '###' + str(episodes[ref]['id']), episodes[ref]['title']) == True:
                                    add = True

                                episodes[ref]['season'] = row['title']
                                if create_nfo_file(filename_ep, episodes[ref], 'episode') == True:
                                    add = True

                        if not data2['cache'] == 1:
                            xbmc.Monitor().waitForAbort(3)
                            count += 1

                        if create_nfo_file(os.path.join(ADDON_PROFILE, "shows", filename, 'tvshow'), seriesinfo, 'show') == True:
                            add = True
            else:
                return_list.append(filename + '.strm')
                return_list.append(filename + '.nfo')
                filename = os.path.join(ADDON_PROFILE, "movies", filename)

                if create_strm_file(filename, id, label) == True:
                    add = True

                if not check_key(row, 'icon_poster'):
                    row['icon_poster'] = row['icon']

                if not check_key(row, 'icon_still'):
                    row['icon_still'] = row['icon']

                if create_nfo_file(filename, row, 'movie') == True:
                    add = True

            progress_abs += 1
            progress_rel = int((progress_abs / total) * 100)
            #pDialog.update(progress_rel)

    #pDialog.close()

    return {'add': add, 'list': return_list }

def create_nfo_file(filename, data, type):
    doc = Document()

    if type == 'movie':
        root = doc.createElement("movie")
    elif type == 'show':
        root = doc.createElement("tvshow")
    else:
        root = doc.createElement("episodedetails")

        if len(str(data['title'])) == 0:
            data['title'] = 'Aflevering {episode}'.format(episode=data['position'])

    doc.appendChild(root)

    XMLvalues = {}
    XMLvalues['title'] = str(data['title'])

    if len(str(data['description'])) > 0:
        XMLvalues['plot'] = str(data['description'])

    if not type == 'show' and len(str(data['duration'])) > 0 and int(data['duration']) > 0:
        XMLvalues['runtime'] = str(int(int(data['duration']) / 60))

    if len(str(data['datum'])) > 3:
        XMLvalues['year'] = str(data['datum'])[:4]

    for value in XMLvalues:
        tempChild = doc.createElement(value)
        root.appendChild(tempChild)
        nodeText = doc.createTextNode(XMLvalues[value].strip())
        tempChild.appendChild(nodeText)

    tempChild = doc.createElement('uniqueid')
    tempChild.setAttribute("type", str(PROVIDER_NAME))
    tempChild.setAttribute("default", 'true')
    root.appendChild(tempChild)
    nodeText = doc.createTextNode(str(data['id']).strip())
    tempChild.appendChild(nodeText)

    if not type == 'episode':
        if type == 'show':
            genres = data['category']
        else:
            genres = data['category'].split(', ')

        if len(genres) > 0:
            for genre in genres:
                tempChild = doc.createElement('genre')
                root.appendChild(tempChild)
                nodeText = doc.createTextNode(str(genre).strip())
                tempChild.appendChild(nodeText)

    if check_key(data, 'seasons'):
        for season in data['seasons']:
            origtitle = data['seasons'][season]
            tempChild = doc.createElement('namedseason')

            if str(origtitle).strip().isnumeric():
                nodeText = doc.createTextNode('Seizoen ' + str(origtitle).strip())
            else:
                nodeText = doc.createTextNode(str(origtitle).strip())

            tempChild.appendChild(nodeText)
            tempChild.setAttribute("number", season)
            root.appendChild(tempChild)

    tempChild = doc.createElement('thumb')

    if type == 'movie' or type == 'show':
        tempChild.setAttribute("aspect", 'poster')
    else:
        tempChild.setAttribute("aspect", 'thumb')

    root.appendChild(tempChild)

    if len(str(data['icon_poster'])) > 0:
        if settings.getBool('use_small_images', default=False) == True:
            nodeText = doc.createTextNode(str(data['icon_poster'].replace(CONST_IMAGES['poster']['replace'], CONST_IMAGES['poster']['small'])).strip())
        else:
            nodeText = doc.createTextNode(str(data['icon_poster'].replace(CONST_IMAGES['poster']['replace'], CONST_IMAGES['poster']['large'])).strip())
    elif len(str(data['icon_still'])) > 0:
        if settings.getBool('use_small_images', default=False) == True:
            nodeText = doc.createTextNode(str(data['icon_still'].replace(CONST_IMAGES['still']['replace'], CONST_IMAGES['still']['small'])).strip())
        else:
            nodeText = doc.createTextNode(str(data['icon_still'].replace(CONST_IMAGES['still']['replace'], CONST_IMAGES['still']['large'])).strip())

    tempChild.appendChild(nodeText)

    if not os.path.isfile(filename + '.nfo'):
        write_file(file=filename + '.nfo', data=doc.toprettyxml(), ext=True, isJSON=False)
        return True
    else:
        if not load_file(filename + '.nfo', ext=True, isJSON=False) == doc.toprettyxml():
            write_file(file=filename + '.nfo', data=doc.toprettyxml(), ext=True, isJSON=False)

            if type == 'movie':
                method = 'VideoLibrary.GetMovies'
                basefilename = os.path.basename(os.path.normpath(filename))
                path = os.path.dirname(filename)
                params = {"filter": {"and": [{"operator": "contains", "field": "path", "value": path}, {"operator": "is", "field": "filename", "value": str(basefilename) + '.strm'}]}}
                result = json_rpc(method, params)

                if result and check_key(result, 'movies') and len(result['movies']) > 0:
                    libraryid = result['movies'][0]['movieid']

                    method = 'VideoLibrary.RefreshMovie'
                    params = {"movieid": libraryid}
                    result = json_rpc(method, params)

            elif type == 'show':
                method = 'VideoLibrary.GetTVShows'
                path = os.path.dirname(filename)
                params = {"filter": {"operator": "contains", "field": "path", "value": path}}
                result = json_rpc(method, params)

                if result and check_key(result, 'tvshows') and len(result['tvshows']) > 0:
                    libraryid = result['tvshows'][0]['tvshowid']

                    method = 'VideoLibrary.RefreshTVShow'
                    params = {"tvshowid": libraryid}
                    result = json_rpc(method, params)

            else:
                method = 'VideoLibrary.GetEpisodes'
                params = {"filter": {"operator": "contains", "field": "filename", "value": filename}}
                result = json_rpc(method, params)

                if result and check_key(result, 'episodes') and len(result['episodes']) > 0:
                    libraryid = result['episodes'][0]['episodeid']

                    method = 'VideoLibrary.RefreshEpisode'
                    params = {"episodeid": libraryid}
                    result = json_rpc(method, params)

            return True
        else:
            return False

def create_strm_file(filename, id, label):
    if not os.path.isfile(filename + '.strm'):
        params = []
        params.append(('_', 'play_video'))
        params.append(('type', 'vod'))
        params.append(('channel', None))

        params.append(('id', id))
        params.append(('title', label))
        path = 'plugin://{0}/?{1}'.format(ADDON_ID, urlencode(encode_obj(params)))
        write_file(file=filename + '.strm', data=path, ext=True, isJSON=False)
        return True
    else:
        return False
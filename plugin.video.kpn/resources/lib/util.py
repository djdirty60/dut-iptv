import _strptime
import datetime, os, sys, time, xbmc

from resources.lib.api import api_vod_subscription
from resources.lib.base.l1.constants import ADDON_ID, DEFAULT_USER_AGENT
from resources.lib.base.l2 import settings
from resources.lib.base.l2.log import log
from resources.lib.base.l3.language import _
from resources.lib.base.l3.util import check_key, convert_datetime_timezone, date_to_nl_dag, date_to_nl_maand, encode_obj, load_file, write_file
from resources.lib.base.l4 import gui
from resources.lib.base.l6 import inputstream
from resources.lib.constants import CONST_BASE_HEADERS, CONST_IMAGE_URL, CONST_IMAGES
from urllib.parse import urlencode

def check_devices():
    pass

def check_entitlements():
    return

def get_image(prefix, content):
    return ''

def get_play_url(content):
    return {'play_url': '', 'locator': ''}

def plugin_ask_for_creds(creds):
    email_or_pin = settings.getBool(key='email_instead_of_customer')

    if email_or_pin:
        if str(creds['username']).isnumeric():
            creds['username'] = ''

        username = str(gui.input(message=_.ASK_USERNAME2, default=creds['username'])).strip()
    else:
        if not str(creds['username']).isnumeric():
            creds['username'] = ''

        username = str(gui.input(message=_.ASK_USERNAME, default=creds['username'])).strip()

    if not len(str(username)) > 0:
        if email_or_pin:
            gui.ok(message=_.EMPTY_USER2, heading=_.LOGIN_ERROR_TITLE)
        else:
            gui.ok(message=_.EMPTY_USER, heading=_.LOGIN_ERROR_TITLE)

        return {'result': False, 'username': '', 'password': ''}

    if email_or_pin:
        password = str(gui.input(message=_.ASK_PASSWORD2, hide_input=True)).strip()
    else:
        password = str(gui.input(message=_.ASK_PASSWORD, hide_input=True)).strip()

    if not len(str(password)) > 0:
        if email_or_pin:
            gui.ok(message=_.EMPTY_PASS2, heading=_.LOGIN_ERROR_TITLE)
        else:
            gui.ok(message=_.EMPTY_PASS, heading=_.LOGIN_ERROR_TITLE)

        return {'result': False, 'username': '', 'password': ''}

    return {'result': True, 'username': username, 'password': password}

def plugin_login_error(login_result):
    email_or_pin = settings.getBool(key='email_instead_of_customer')

    if email_or_pin:
        gui.ok(message=_.LOGIN_ERROR2, heading=_.LOGIN_ERROR_TITLE)
    else:
        gui.ok(message=_.LOGIN_ERROR, heading=_.LOGIN_ERROR_TITLE)

def plugin_post_login():
    pass

def plugin_process_info(playdata):
    info = {
        'label1': '',
        'label2': '',
        'description': '',
        'image': '',
        'image_large': '',
        'duration': 0,
        'credits': [],
        'cast': [],
        'director': [],
        'writer': [],
        'genres': [],
        'year': '',
    }

    if playdata['info'] and check_key(playdata['info'], 'resultObj'):
        for row in playdata['info']['resultObj']['containers']:
            if check_key(row, 'metadata'):
                if check_key(row['metadata'], 'airingStartTime') and check_key(row['metadata'], 'airingEndTime'):
                    startT = datetime.datetime.fromtimestamp(int(int(row['metadata']['airingStartTime']) // 1000))
                    startT = convert_datetime_timezone(startT, "UTC", "UTC")
                    endT = datetime.datetime.fromtimestamp(int(int(row['metadata']['airingEndTime']) // 1000))
                    endT = convert_datetime_timezone(endT, "UTC", "UTC")

                    info['duration'] = int((endT - startT).total_seconds())

                    if xbmc.getLanguage(xbmc.ISO_639_1) == 'nl':
                        info['label1'] = '{weekday} {day} {month} {yearhourminute} '.format(weekday=date_to_nl_dag(startT), day=startT.strftime("%d"), month=date_to_nl_maand(startT), yearhourminute=startT.strftime("%Y %H:%M"))
                    else:
                        info['label1'] = startT.strftime("%A %d %B %Y %H:%M ").capitalize()

                    info['label1'] += " - "

                    write_file(file='stream_start', data=int(int(row['metadata']['airingStartTime']) // 1000), isJSON=False)
                    write_file(file='stream_end', data=int(int(row['metadata']['airingEndTime']) // 1000), isJSON=False)

                if check_key(playdata, 'title') and len(str(playdata['title'])) > 0:
                    info['label1'] += playdata['title']

                    if len(str(info['label2'])) > 0:
                        info['label2'] += " - "

                    info['label2'] += playdata['title']

                if check_key(row['metadata'], 'title') and len(str(row['metadata']['title'])) > 0:
                    info['label1'] += row['metadata']['title']

                    if len(str(info['label2'])) > 0:
                        info['label2'] += " - "

                    info['label2'] += row['metadata']['title']

                if check_key(row['metadata'], 'longDescription'):
                    info['description'] = row['metadata']['longDescription']

                if playdata['type'] == 'VOD':
                    imgtype = 'vod'
                else:
                    imgtype = 'epg'

                if check_key(row['metadata'], 'pictureUrl'):
                    info['image'] = "{image_url}/{imgtype}/{image}/1920x1080.jpg?blurred=false".format(image_url=CONST_IMAGE_URL, imgtype=imgtype, image=row['metadata']['pictureUrl'])
                    info['image_large'] = "{image_url}/{imgtype}/{image}/1920x1080.jpg?blurred=false".format(image_url=CONST_IMAGE_URL, imgtype=imgtype, image=row['metadata']['pictureUrl'])

                if check_key(row['metadata'], 'actors'):
                    for castmember in row['metadata']['actors']:
                        info['cast'].append(castmember)

                if check_key(row['metadata'], 'directors'):
                    for directormember in row['metadata']['directors']:
                        info['director'].append(directormember)

                if check_key(row['metadata'], 'authors'):
                    for writermember in row['metadata']['authors']:
                        info['writer'].append(writermember)

                if check_key(row['metadata'], 'genres'):
                    for genre in row['metadata']['genres']:
                        info['genres'].append(genre)

                if check_key(row['metadata'], 'duration'):
                    info['duration'] = row['metadata']['duration']

                epcode = ''

                if check_key(row['metadata'], 'season'):
                    epcode += 'S' + str(row['metadata']['season'])

                if check_key(row['metadata'], 'episodeNumber'):
                    epcode += 'E' + str(row['metadata']['episodeNumber'])

                if check_key(row['metadata'], 'episodeTitle'):
                    if len(str(info['label2'])) > 0:
                        info['label2'] += " - "

                    info['label2'] += str(row['metadata']['episodeTitle'])

                    if len(epcode) > 0:
                        info['label2'] += " (" + epcode + ")"

                if check_key(row, 'channel'):
                    if check_key(row['channel'], 'channelName'):
                        if len(str(info['label2'])) > 0:
                            info['label2'] += " - "

                        info['label2'] += str(row['channel']['channelName'])

    return info

def plugin_process_playdata(playdata):
    CDMHEADERS = CONST_BASE_HEADERS
    CDMHEADERS['User-Agent'] = DEFAULT_USER_AGENT

    if check_key(playdata, 'license'):
        item_inputstream = inputstream.Widevine(
            license_key = playdata['license'],
        )
    else:
        item_inputstream = inputstream.MPD()

    return item_inputstream, CDMHEADERS

def plugin_renew_token(data):
    return None

def plugin_process_watchlist(data, continuewatch=0):
    items = []

    return items

def plugin_process_watchlist_listing(data, id=None, continuewatch=0):
    items = []

    return items
    
def plugin_vod_subscription_filter():
    api_vod_subscription()

    subscription_filter = load_file(file=os.path.join('cache', 'vod_subscription.json'), isJSON=True)

    if subscription_filter:
        subscription_filter = list(subscription_filter)

    return subscription_filter
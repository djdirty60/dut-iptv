from resources.lib.base.l3.language import _

CONST_BASE_DOMAIN = ''
CONST_BASE_DOMAIN_MOD = False
CONST_BASE_IP = ''

CONST_API_URL = 'https://api.nlziet.nl'
CONST_APP_URL = 'https://app.nlziet.nl'

CONST_BASE_HEADERS = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,nl;q=0.8',
    'Cache-Control': 'no-cache',
    'DNT': '1',
    'Origin': CONST_APP_URL,
    'Pragma': 'no-cache',
    'Referer': CONST_APP_URL,
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
}

CONST_BASE_URL = 'https://www.nlziet.nl'

CONST_CONTINUE_WATCH = False

CONST_FIRST_BOOT = True

CONST_HAS_DUTIPTV = True

CONST_HAS_LIBRARY = False

CONST_HAS_LIVE = True

CONST_HAS_REPLAY = True

CONST_HAS_SEARCH = True

CONST_ID_URL = 'https://id.nlziet.nl'

CONST_IMAGES = {
    'replay': {
        'large': '',
        'small': '',
        'replace': '[format]'
    },
    'vod': {
        'large': '',
        'small': '',
        'replace': '[format]'
    },
}

CONST_IMAGE_URL = 'https://nlzietprodstorage.blob.core.windows.net'

CONST_LIBRARY = {}

CONST_MOD_CACHE = {}

CONST_ONLINE_SEARCH = False

CONST_START_FROM_BEGINNING = True

CONST_USE_PROXY = True

CONST_USE_PROFILES = False

CONST_VOD_CAPABILITY = [
    { 'file': 'tipfeednpo', 'label': _.RECOMMENDED + ' NPO', 'start': 0, 'menu': 0, 'online': 1, 'search': 1, 'az': 0 },
    { 'file': 'tipfeed', 'label': _.RECOMMENDED, 'start': 0, 'menu': 0, 'online': 1, 'search': 1, 'az': 0 },
    { 'file': 'watchaheadnpo', 'label': _.WATCHAHEAD + ' NPO', 'start': 0, 'menu': 0, 'online': 1, 'search': 1, 'az': 0 },
    { 'file': 'watchahead', 'label': _.WATCHAHEAD, 'start': 0, 'menu': 0, 'online': 1, 'search': 1, 'az': 0 },
    { 'file': 'moviesnpo', 'label': _.MOVIES + ' NPO', 'start': 0, 'menu': 0, 'online': 1, 'search': 1, 'az': 0 },
    { 'file': 'movies', 'label': _.MOVIES, 'start': 0, 'menu': 0, 'online': 1, 'search': 1, 'az': 0 },
    { 'file': 'seriesbingenpo', 'label': _.SERIESBINGE + ' NPO', 'start': 0, 'menu': 0, 'online': 1, 'search': 1, 'az': 0 },
    { 'file': 'seriesbinge', 'label': _.SERIESBINGE, 'start': 0, 'menu': 0, 'online': 1, 'search': 1, 'az': 0 },
    { 'file': 'mostviewed', 'label': _.MOSTVIEWED, 'start': 0, 'menu': 0, 'online': 1, 'search': 1, 'az': 0 },
]

CONST_WATCHLIST = False
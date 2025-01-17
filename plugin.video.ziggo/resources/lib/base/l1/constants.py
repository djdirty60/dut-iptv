import os, xbmcaddon, xbmcvfs

##### ADDON ####
ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_NAME = ADDON.getAddonInfo('name')

PROVIDER_NAME = ADDON_ID.replace('plugin.video.', '')

ADDON_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('path'))
ADDON_PROFILE = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))

ADDONS_PATH = os.path.join(xbmcvfs.translatePath('special://home'), 'addons', '')

USERDATA_PATH = os.path.join(xbmcvfs.translatePath('special://userdata'), '')

ADDON_ICON = ADDON.getAddonInfo('icon')
ADDON_FANART = ADDON.getAddonInfo('fanart')
ADDON_VERSION = ADDON.getAddonInfo('version')

#################

CONST_DUT_EPG_BASE = 'https://dut-epg.github.io'
CONST_DUT_EPG = '{base_epg}/{provider}'.format(base_epg=CONST_DUT_EPG_BASE, provider=PROVIDER_NAME)

try:
    CONST_DUT_EPG_SETTINGS = '{base_epg}/{letter}.settings.json'.format(base_epg=CONST_DUT_EPG_BASE, letter=PROVIDER_NAME[0])
except:
    CONST_DUT_EPG_SETTINGS = '{base_epg}/a.settings.json'.format(base_epg=CONST_DUT_EPG_BASE)

DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'
DEFAULT_BROWSER_NAME = 'Chrome'
DEFAULT_BROWSER_VERSION = '96.0.4664.45'
DEFAULT_OS_NAME = 'Windows'
DEFAULT_OS_VERSION = '10'

SESSION_CHUNKSIZE = 4096

AUDIO_LANGUAGES = {
    'nl': 'Nederlands/Dutch',
    'en': 'Engels/English',
    'gos': 'Gesproken ondertiteling/Spoken subtitles',
    'unk': 'Onbekend/Unknown'
}
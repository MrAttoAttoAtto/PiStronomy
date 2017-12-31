from astronomy_gui import lockedScreen
from astronomy_gui import wifiScreen
from astronomy_gui import astroScreen

__all__ = [
    'lockedScreen',
    'astroScreen',
    'wifiScreen'
]

pages = [
    lockedScreen.LockedScreen,
    wifiScreen.WifiScreen,
    astroScreen.AstroScreen
]

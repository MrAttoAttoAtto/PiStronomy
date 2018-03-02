from astronomy_gui import wifiScreen
from astronomy_gui import astroScreen

# Sets the names of both the screens to be imported with *
__all__ = [
    'astroScreen',
    'wifiScreen'
]

# Gets the classes of the screens into a list to be imported
pages = [
    wifiScreen.WifiScreen,
    astroScreen.AstroScreen
]

import tkinter as tk

from astronomy_gui.lockedScreen import LockedScreen
from astronomy_gui.wifiScreen import WifiScreen
from astronomy_gui.controller import CONTROLLER

CONTROLLER.add_page(WifiScreen)

CONTROLLER.show_page('WifiScreen')

tk.mainloop()

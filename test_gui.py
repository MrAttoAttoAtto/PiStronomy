import tkinter as tk

from astronomy_gui.lockedScreen import LockedScreen
from astronomy_gui.controller import CONTROLLER

CONTROLLER.add_page(LockedScreen)

CONTROLLER.show_page('LockedScreen')

tk.mainloop()
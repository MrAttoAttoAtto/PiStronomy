import tkinter as tk

from astronomy_gui import *
from astronomy_gui import pages
from astronomy_gui.controller import CONTROLLER

for clas in pages:
    CONTROLLER.add_page(clas)

CONTROLLER.show_page('WifiScreen')

tk.mainloop()

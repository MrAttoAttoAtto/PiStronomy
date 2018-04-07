"""
Opens the gui
"""

import tkinter as tk

from astronomy_gui import pages
from astronomy_gui.controller import CONTROLLER
from tools import setup_gpio

setup_gpio()

for clas in pages:
    CONTROLLER.add_page(clas)

CONTROLLER.show_page('AstroScreen')

tk.mainloop()

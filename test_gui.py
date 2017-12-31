import tkinter as tk

from astronomy_gui import *
from astronomy_gui import pages
from astronomy_gui.controller import CONTROLLER
from planets import start_planet_update

start_planet_update()

for clas in pages:
    CONTROLLER.add_page(clas)

CONTROLLER.show_page('AstroScreen')

tk.mainloop()

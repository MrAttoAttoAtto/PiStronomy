import tkinter as tk

from rational_gui.controller import CONTROLLER
from rational_gui.images import get_imagepath
from rational_gui.page import Page

#locked screen class
class LockedScreen(Page):
    def __init__(self, parent):
        #setup things
        super().__init__(parent)

        lockedBg = tk.PhotoImage(file=get_imagepath("lockedBg"))
        lockedButton = tk.PhotoImage(file=get_imagepath("unlockTest"))

        self.width = 800
        self.height = 480
        self.grid()

        #background things
        bg_lbl = tk.Label(self, image=lockedBg)
        bg_lbl.image = lockedBg
        bg_lbl.place(x=-2, y=-2)

        #submit button things
        submit_button = tk.Button(self, image=lockedButton, command=lambda: CONTROLLER.show_page("VerificationScreen"), bg="black", activebackground="black", bd=0, highlightthickness=0)
        submit_button.image = lockedButton
        submit_button.grid(row=1, column=1, padx=326, pady=151)
        
        print("Locked Screen Initialised")

import tkinter as tk

from rational_gui.images import get_imagepath
from rational_gui.page import Page
from rational_gui.controller import CONTROLLER

#refill class
class RefillScreen(Page):
    def __init__(self, parent):
        #setup thingss
        super().__init__(parent)
        self.width = 800
        self.height = 480
        self.grid()
        
        refillBg = tk.PhotoImage(file=get_imagepath("addCrackerBg"))
        backIcon = tk.PhotoImage( file=get_imagepath("backIcon"))

        bg_lbl = tk.Label(self, image=refillBg)
        bg_lbl.image = refillBg
        bg_lbl.place(x=-2, y=-2)

        #back button
        backIcon = backIcon.subsample(3, 3)
        back_button = tk.Button(self, image=backIcon, bg="black", activebackground="black", fg="white", command=lambda:CONTROLLER.show_page("HudScreen"))
        back_button.image = backIcon
        back_button.place(x=20, y=20)

        #cracker adding tracker lbl
        crackers_to_add_text = 0
        crackers_to_add = tk.Label(self, text = str(crackers_to_add_text), font=("Helvetica", 50))
        crackers_to_add.place(x=350, y=200)

        """ dodgy things that don't work yet
        def upCrackers():
            global crackers_to_add_text
            crackers_to_add_text += 1
            print(crackers_to_add_text)
        
        def downCrackers():
            global crackers_to_add_text
            crackers_to_add_text -= 1
            print(crackers_to_add_text)

        up_crackers = tk.Button(self, text="^", bg="black", activebackground="black", font=("Helvetica", 50), command=lambda: upCrackers() )
        up_crackers.place(x=400, y=100)
        down_crackers = tk.Button(self, text="⌄", bg="black", activebackground="black", font=("Helvetica", 50), command=lambda: downCrackers() )
        down_crackers.place(x=400, y=300)
        """
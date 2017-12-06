import tkinter as tk

from rational_gui.images import get_imagepath
from rational_gui.page import Page
from rational_gui.controller import CONTROLLER
from settings import SYSTEM_DATA
import cracker_tracker
import datetime


#hud class
class HudScreen(Page):
    def __init__(self, parent):
        #setup thingss
        super().__init__(parent)
        self.width = 800
        self.height = 480
        self.grid()
        crackers = {}
        self.user = None
        hudBg = tk.PhotoImage(file=get_imagepath("hudBg"))
        cracker_holder = tk.PhotoImage(file=get_imagepath("crackerHolder"))
        self.crackerimg = tk.PhotoImage(file=get_imagepath("cracker2"))
        realCracker = tk.PhotoImage(file=get_imagepath("crackerImg"))
        refillIcon = tk.PhotoImage(file=get_imagepath("refill"))
        lockIco = tk.PhotoImage(file=get_imagepath("lockIco"))

        # This is going to have to be changed...
        person_pic = tk.PhotoImage(file=get_imagepath("personpic"))

        #background things
        bg_lbl = tk.Label(self, image=hudBg)
        bg_lbl.image = hudBg
        bg_lbl.place(x=-2, y=-2)


        #picture of respective person logged in
        person_pic = person_pic.subsample(2, 2)
        person_lbl = tk.Label(self, image=person_pic)
        person_lbl.image = person_pic
        person_lbl.place(x=360, y=30)

        #info label
        self.info_var = tk.StringVar()
        info = tk.Label(self, textvariable=self.info_var, bg="black", foreground="white")
        info.place(x=320, y=420)

        #lock button stuff
        lockIco = lockIco.subsample(4, 4)
        lock_button = tk.Button(self, image=lockIco, bg="black", activebackground="black", fg="white", command=lambda: CONTROLLER.show_page("LockedScreen"))
        lock_button.image = lockIco
        lock_button.place(x=720, y=30)

        #dispense button stuff
        realCracker = realCracker.subsample(4, 4)
        self.dispense_button = tk.Button(self, image=realCracker, bg="black", command=lambda: CONTROLLER.show_page("DispenseScreen"), activebackground="black", fg="white")
        self.dispense_button.image = realCracker
        self.dispense_button.place(x=370, y=245)

        #refill button things
        refillIcon = refillIcon.subsample(6, 6)
        refill_button = tk.Button(self, image=refillIcon, bg="black", activebackground="black", fg="white", command=lambda: CONTROLLER.show_page("RefillScreen"))
        refill_button.image = refillIcon
        refill_button.place(x=50, y=400)

        #crackers image things
        person_lbl = tk.Label(self, image=cracker_holder, bd=0)
        person_lbl.image = cracker_holder
        person_lbl.place(x=20, y=30)

    def render_message(self, user):
        msg = "Welcome, {}.\n".format(SYSTEM_DATA['userDict'][user]["name"])
        if cracker_tracker.can_dispense_cracker(user):
            msg+="You can take a cracker."
        else:
            msg+="You cannot take a cracker right now.\n"
            lastCracker = datetime.datetime.strptime(SYSTEM_DATA['userDict'][user]["lastCracker"], "%Y-%m-%dT%H:%M:%S")
            s = (datetime.datetime.today() - lastCracker + datetime.timedelta(hours=12)).total_seconds()
            msg += '{:02}:{:02}:{:02}'.format(s // 3600, s % 3600 // 60, s % 60)

        self.info_var.set(msg)
        self.after(1000, self.render_message, user)

    def render(self, user):
        self.user = user
        self.dispense_button.configure(command=lambda: CONTROLLER.show_page("DispenseScreen", user))
        self.render_message(user)
        #temporary variable so you can see that it still works with less crackers (try changing it)
        cry = 348
        for i in range(SYSTEM_DATA['crackersLeft']):
            crackers = tk.Label(self, image=self.crackerimg, bd=0)
            crackers.place(x=35, y=cry)
            cry -= 23

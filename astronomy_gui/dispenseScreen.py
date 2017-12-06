import tkinter as tk
import threading

from rational_gui.controller import CONTROLLER
from rational_gui.images import get_imagepath
from rational_gui.page import Page
from cracker_controller import CHOREOGRAPHER
from rational_utils.thread_tools import wait_for_thread

#dispense screen class
class DispenseScreen(Page):
    def __init__(self, parent):
        #setup things
        super().__init__(parent)

        dispenseBg = tk.PhotoImage(file=get_imagepath("dispenseScreen"))
        #lockedButton = tk.PhotoImage(file=get_imagepath("unlockTest"))

        self.width = 800
        self.height = 480
        self.grid()

        #background things
        bg_lbl = tk.Label(self, image=dispenseBg)
        bg_lbl.image = dispenseBg
        bg_lbl.place(x=-2, y=-2)

       
        
        print("Dispense Screen Initialised")

    def on_auth_end(self):
        CONTROLLER.show_page('HudScreen', self.user)

    def verithread(self):
        CHOREOGRAPHER.prepare_cracker()
        time.sleep(10)


    def render(self, data=False):
        self.user = data
        thread = threading.Thread(target=self.verithread)
        thread.start()
        wait_for_thread(thread, self.on_auth_end)
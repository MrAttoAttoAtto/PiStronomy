import queue
import threading
import time
import tkinter as tk
from PIL import ImageTk

from astronomy_gui.controller import CONTROLLER
from astronomy_gui.images import get_imagepath
from astronomy_gui.page import Page
from get_picture import get_sky_picture
from tools import from_hour_rep, from_deg_rep

#astronomy main screen class
class AstroScreen(Page):
    def __init__(self, parent):
        #setup things
        super().__init__(parent)

        load_image = tk.PhotoImage(file=self.loading_gif_path, format='gif -index 0')

        self.width = 800
        self.height = 480
        self.grid()

        #instruction label
        #instr_label = tk.Label(self, text="Please select a network to connect to:", font=("Helvetica", 34))
        #instr_label.grid(row=0, column=1, columnspan=3)

        #loading things
        self.load_label = tk.Label(self, image=load_image)
        self.load_label.image = load_image

        self.load_label.pack()

        wifi_button = tk.Button(self, text="Go To Wifi", command=lambda: CONTROLLER.show_page('WifiScreen'), font=("Helvetica", 20), fg='green', activeforeground='green')
        wifi_button.pack()

        CONTROLLER.after(self.LOADING_GIF_FREQUENCY, lambda: self.update_loading_gif(1, self.load_label, time.time()))

        self.image_queue = queue.Queue(1)

        image_process = threading.Thread(None, lambda: self.image_queue.put(get_sky_picture(ra=from_hour_rep(3, 47, 24), de=from_deg_rep(24, 7, 0))))
        image_process.start()

        CONTROLLER.after(self.CHECK_FREQUENCY,
                         lambda: self.check_thread(image_process,
                                                   self.display_image))
    
    def display_image(self):
        self.load_label.pack_forget()

        image = self.image_queue.get()

        tk_image = ImageTk.PhotoImage(image)

        image_label = tk.Label(self, image=tk_image)
        image_label.image = tk_image

        image_label.pack()
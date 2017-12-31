import queue
import threading
import time
import tkinter as tk

from PIL import ImageTk

from astronomy_gui.controller import CONTROLLER
from astronomy_gui.images import get_imagepath
from astronomy_gui.page import Page
from get_picture import get_sky_picture
from planets import MAPPING_DICT, PLANET_COORDINATES
from tools import from_deg_rep, from_hour_rep, get_constellation


#astronomy main screen class
class AstroScreen(Page):
    def __init__(self, parent):
        #setup things
        super().__init__(parent)

        self.base_ra = 0
        self.base_de = 0
        self.shiftx = 0
        self.shifty = 0

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

        self.image_label = tk.Label(self, image=None)
        self.image_label.image = None

        wifi_button = tk.Button(self, text="Go To Wifi", command=self.wifi_button_func, font=("Helvetica", 20), fg='green', activeforeground='green')
        wifi_button.pack()

        self.planet_menu = tk.Menu(self, tearoff=0)
        for planet in MAPPING_DICT:
            self.planet_menu.add_command(label=planet, command=lambda planet=planet: self.show_planet(MAPPING_DICT[planet]))

        planet_button = tk.Button(self, text="Go To Object", font=("Helvetica", 20), fg='green', activeforeground='green')
        planet_button.bind('<Button-1>', lambda e: CONTROLLER.after(5, lambda e=e: self.planet_menu_popup(e)))
        planet_button.pack()

        self.do_bindings()

        CONTROLLER.after(self.LOADING_GIF_FREQUENCY, lambda: self.update_loading_gif(1, self.load_label, time.time()))

        self.image_queue = queue.Queue(1)

        self.base_ra = from_hour_rep(3, 47, 24)
        self.base_de = from_deg_rep(24, 7, 0)

        image_process = threading.Thread(None, lambda: self.image_queue.put(get_sky_picture(self.base_ra, self.base_de)))
        image_process.start()

        CONTROLLER.after(self.CHECK_FREQUENCY,
                         lambda: self.check_thread(image_process,
                                                   self.display_image))

    def display_image(self):
        self.load_label.pack_forget()

        self.image_label.pack_forget()

        image = self.image_queue.get()

        tk_image = ImageTk.PhotoImage(image)

        self.image_label.configure(image=tk_image)
        self.image_label.image = tk_image

        self.image_label.pack()
    
    def generate_image(self, shiftx, shifty, new_base_ra=None, new_base_de=None):
        self.shiftx += shiftx
        self.shifty += shifty

        if new_base_ra is not None:
            self.base_ra = new_base_ra

        if new_base_ra is not None:
            self.base_ra = new_base_ra

        image_process = threading.Thread(None, lambda: self.image_queue.put(get_sky_picture(self.base_ra, self.base_de, self.shiftx, self.shifty)))
        image_process.start()

        CONTROLLER.after(self.CHECK_FREQUENCY,
                         lambda: self.check_thread(image_process,
                                                   self.display_image))
    
    def wifi_button_func(self):
        CONTROLLER.unbind("<Left>")
        CONTROLLER.unbind("<Right>")
        CONTROLLER.unbind("<Up>")
        CONTROLLER.unbind("<Down>")

        CONTROLLER.show_page('WifiScreen')
    
    def do_bindings(self):
        CONTROLLER.bind("<Left>", lambda e: self.generate_image(128, 0))
        CONTROLLER.bind("<Right>", lambda e: self.generate_image(-128, 0))
        CONTROLLER.bind("<Up>", lambda e: self.generate_image(0, 128))
        CONTROLLER.bind("<Down>", lambda e: self.generate_image(0, -128))
    
    def planet_menu_popup(self, event):
        x_root = event.x_root
        y_root = event.y_root

        self.planet_menu.post(x_root, y_root)
    
    def show_planet(self, index):
        try:
            self.all_coords = PLANET_COORDINATES.get(block=False)
        except queue.Empty:
            pass
        
        try:
            planet_ra, planet_de = self.all_coords[index]
        except IndexError:
            #TODO: Error message
            return

        self.generate_image(0, 0, planet_ra, planet_de)

    def render(self, referral=False):
        if referral:
            self.do_bindings()

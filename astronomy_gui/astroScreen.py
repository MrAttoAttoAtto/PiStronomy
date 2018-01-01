import queue
import threading
import time
import tkinter as tk
import uuid
from tkinter import messagebox
from tkinter import simpledialog

from PIL import ImageTk

from astronomy_gui.controller import CONTROLLER
from astronomy_gui.images import get_imagepath
from astronomy_gui.page import Page
from get_picture import get_sky_picture
from planets import MAPPING_DICT, PLANET_COORDINATES, constant_planet_update
from tools import from_deg_rep, from_hour_rep, get_constellation, coordinates_from_observer, get_earth_location_coordinates

from astropy.coordinates.errors import UnknownSiteException

UNSEEABLE_START_ALTITUDE = 20

#astronomy main screen class
class AstroScreen(Page):
    def __init__(self, parent):
        #setup things
        super().__init__(parent)

        self.base_ra = 0
        self.base_de = 0
        self.shiftx = 0
        self.shifty = 0
        self.magnification = 0

        self.location = 'Greenwich'
        self.lat, self.long = get_earth_location_coordinates(self.location.lower())
        self.time = time.strftime("%Y-%m-%d %H:%M:%S")
        self.time_manual = False

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

        self._setup_menus()

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
    
    def _setup_menus(self):
        self.menubar = tk.Menu(self, font=("Helvetica", 10))

        # setting up the planet submenu
        planet_menu = tk.Menu(self.menubar, tearoff=0, font=("Helvetica", 10))

        planet_goto_menu = tk.Menu(planet_menu, tearoff=0, font=("Helvetica", 10))
        planet_info_menu = tk.Menu(planet_menu, tearoff=0, font=("Helvetica", 10))
        for planet in MAPPING_DICT:
            planet_goto_menu.add_command(label=planet, command=lambda planet=planet: self.show_planet(MAPPING_DICT[planet]))
            planet_info_menu.add_command(label=planet, command=lambda planet=planet: self.show_planet_info(MAPPING_DICT[planet]))

        planet_menu.add_cascade(label='Goto', menu=planet_goto_menu)
        planet_menu.add_cascade(label="Info", menu=planet_info_menu)
        planet_menu.add_separator()
        planet_menu.add_command(label="Refresh planet positions", command=self.refresh_planets)

        # setting up the wifi submenu
        wifi_menu = tk.Menu(self.menubar, tearoff=0, font=("Helvetica", 10))
        wifi_menu.add_command(label='Open Wifi Screen', command=self.wifi_button_func)
        wifi_menu.add_command(label="Check IP", command=self.display_current_ip)
        wifi_menu.add_command(label="Check SSID", command=self.display_current_ssid)

        # setting up the settings submenu
        settings_menu = tk.Menu(self.menubar, tearoff=0, font=("Helvetica", 10))
        settings_menu.add_command(label="Change magnification", command=self.set_magnification)
        settings_menu.add_command(label="Change coordinates", command=self.set_coordinates)

        self.menubar.add_cascade(label='Planets', menu=planet_menu)
        self.menubar.add_cascade(label="Wifi", menu=wifi_menu)
        self.menubar.add_cascade(label="Settings", menu=settings_menu)

        CONTROLLER.config(menu=self.menubar)
    
    def set_magnification(self):
        new_mag = simpledialog.askfloat("Enter new magnification", "Please enter a new magnification (0 is the default, -1 is smaller and 1 is bigger.\nIt is currently {}".format(self.magnification), parent=self)

        self.generate_image(0, 0, None, None, new_mag)
    
    def refresh_planets(self):
        planet_process = threading.Thread(None, lambda: constant_planet_update(True))
        planet_process.start()

        CONTROLLER.after(self.CHECK_FREQUENCY,
                         lambda: self.check_thread(planet_process,
                                                   lambda: self.display_info("Planets successfully updated", "Planets updated")))
    
    def set_coordinates(self):
        coordinate_string = simpledialog.askstring("Enter new coordinates", "Please enter new coordinates.\nThe formats \"(hours, minutes, seconds), (degrees, arcmins, arcsecs)\"\n" +
                                                   "and \"hours, degrees\" (where the latter takes values with decimal points) are both acceptable", parent=self)
        
        coordinate_string = coordinate_string.replace("(", "")
        coordinate_string = coordinate_string.replace(")", "")
        coordinate_string = coordinate_string.replace(" ", "")

        split_string = coordinate_string.split(",")

        if len(split_string) == 2:
            try:
                righta = int(split_string[0])
                dec = int(split_string[1])
            except ValueError:
                self.display_error("That was not a valid input!", "Invalid input")
                return
        elif len(split_string) == 6:
            try:
                hours = int(split_string[0])
                mins = int(split_string[1])
                secs = int(split_string[2])
                degs = int(split_string[3])
                arcmins = int(split_string[4])
                arcsecs = int(split_string[5])
            except ValueError:
                self.display_error("That was not a valid input!", "Invalid input")
                return

            righta = from_hour_rep(hours, mins, secs)
            dec = from_deg_rep(degs, arcmins, arcsecs)
        else:
            self.display_error("That was not a valid input!", "Invalid input")
            return

        if righta > 24 or righta < 0 or dec > 90 or dec < -90:
            self.display_error("That was not a valid input!\nRight ascension is in the range 0 - 24 " +
                               "and declination in the range -90 - 90", "Invalid input")
            return

        self.generate_image(0, 0, righta, dec)

    def display_image(self):
        self.load_label.pack_forget()

        self.image_label.pack_forget()

        image = self.image_queue.get()

        tk_image = ImageTk.PhotoImage(image)

        self.image_label.configure(image=tk_image)
        self.image_label.image = tk_image

        self.image_label.pack()

    def generate_image(self, shiftx, shifty, new_base_ra=None, new_base_de=None, new_base_magnification=None):
        self.shiftx += shiftx
        self.shifty += shifty

        if new_base_ra is not None:
            self.base_ra = new_base_ra

        if new_base_de is not None:
            self.base_de = new_base_de
        
        if new_base_magnification is not None:
            self.magnification = new_base_magnification

        image_process = threading.Thread(None, lambda: self.image_queue.put(get_sky_picture(self.base_ra, self.base_de, self.shiftx, self.shifty, self.magnification)))
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

    def show_planet(self, index):
        try:
            self.all_coords = PLANET_COORDINATES.get(block=False)
        except queue.Empty:
            pass
        
        try:
            planet_ra, planet_de = self.all_coords[index]
        except IndexError:
            self.display_error("The planet data has not been generated yet, please wait a few seconds then try again", "Data not available")
            return

        self.generate_image(0, 0, planet_ra, planet_de)
    
    def show_planet_info(self, index):
        try:
            self.all_coords = PLANET_COORDINATES.get(block=False)
        except queue.Empty:
            pass
        
        try:
            planet_ra, planet_de = self.all_coords[index]
        except IndexError:
            self.display_error("The planet data has not been generated yet, please wait a few seconds then try again", "Data not available")
            return

        if not self.time_manual:
            self.time = time.strftime("%Y-%m-%d %H:%M:%S")

        planet_az, planet_alt = coordinates_from_observer(planet_ra, planet_de, self.location, self.time)

        visible = "Yes" if planet_alt > UNSEEABLE_START_ALTITUDE else "No" 

        info_string = '''Name — {}
Right Ascension — {} hours
Declination — {} degrees
Azimuth — {} degrees
Altitude — {} degrees
Visible from {}? (latitude {} degrees) — {}
Within {} (Constellation)
(Information generated for {} at location {})'''.format(next((name for name, map_index in MAPPING_DICT.items() if map_index == index)),
                                                                round(planet_ra, 2), round(planet_de, 2), round(planet_az, 2), round(planet_alt, 2),
                                                                self.location, round(self.lat, 2), visible, get_constellation(planet_ra, planet_de),
                                                                self.time, self.location)

        self.display_info(info_string, "Planet info")

    def update_location(self, location):
        try:
            self.lat, self.long = get_earth_location_coordinates(location.lower())
        except UnknownSiteException:
            self.display_error("This site is not recognised, please choose another telescope/site", "Site not recognised")
            return

        self.location = location

    def render(self, referral=False):
        if referral:
            self.do_bindings()

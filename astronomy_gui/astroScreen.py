import queue
import threading
import time
import tkinter as tk
import uuid
from tkinter import messagebox, simpledialog

from astropy.coordinates.errors import UnknownSiteException
from astropy.coordinates import EarthLocation
from astropy.coordinates.name_resolve import NameResolveError
from astropy.time import Time
from PIL import ImageTk

from astronomy_gui.controller import CONTROLLER
from astronomy_gui.images import get_imagepath
from astronomy_gui.page import Page
from get_picture import get_sky_picture
from planets import MAPPING_DICT, PLANET_COORDINATES, constant_planet_update
from tools import (coordinates_from_observer, from_deg_rep, from_hour_rep,
                   get_constellation, get_earth_location_coordinates,
                   get_object_coordinates)

# the altitude at which it is considered impossible to see a star (i.e. too close to the horizon)
UNSEEABLE_START_ALTITUDE = 20

# astronomy main screen class
class AstroScreen(Page):
    def __init__(self, parent):
        #setup things
        super().__init__(parent)

        self.all_coords = []

        self.base_ra = 0
        self.base_de = 0
        self.shiftx = 0
        self.shifty = 0
        self.magnification = 0.0

        self.location = 'Greenwich'
        self.lat, self.long = get_earth_location_coordinates(self.location.lower())
        self.time = time.strftime("%Y-%m-%d %H:%M:%S")
        self.time_manual = False

        load_image = tk.PhotoImage(file=self.loading_gif_path, format='gif -index 0')

        self.width = 800
        self.height = 480
        self.grid()

        planet_update_process = threading.Thread(None, lambda: constant_planet_update(skip=True))
        planet_update_process.setDaemon(True)
        planet_update_process.start()

        CONTROLLER.after(self.CHECK_FREQUENCY,
                         lambda: self.check_thread(planet_update_process,
                                                   lambda: self.display_info("Initial planet locations have been calculated", "Planet locations calculated")))

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

        self._do_bindings()

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
        self.menubar = tk.Menu(self, font=("Helvetica", self.MENU_FONT_SIZE))

        # setting up the astronomy submenu
        astronomy_menu = tk.Menu(self.menubar, tearoff=0, font=("Helvetica", self.MENU_FONT_SIZE))

        planet_goto_menu = tk.Menu(astronomy_menu, tearoff=0, font=("Helvetica", self.MENU_FONT_SIZE))
        planet_info_menu = tk.Menu(astronomy_menu, tearoff=0, font=("Helvetica", self.MENU_FONT_SIZE))
        for planet in MAPPING_DICT:
            planet_goto_menu.add_command(label=planet, command=lambda planet=planet: self.show_planet(MAPPING_DICT[planet]))
            planet_info_menu.add_command(label=planet, command=lambda planet=planet: self.show_planet_info(MAPPING_DICT[planet]))

        astronomy_menu.add_cascade(label='Goto planet', menu=planet_goto_menu)
        astronomy_menu.add_cascade(label="Planet info", menu=planet_info_menu)
        astronomy_menu.add_command(label="Refresh planet positions", command=self.refresh_planets)
        astronomy_menu.add_separator()
        astronomy_menu.add_command(label="Goto object (By name)", command=self.show_object)
        astronomy_menu.add_command(label="Object info (By name)", command=self.show_object_info)

        # setting up the wifi submenu
        wifi_menu = tk.Menu(self.menubar, tearoff=0, font=("Helvetica", self.MENU_FONT_SIZE))
        wifi_menu.add_command(label='Open Wifi Screen', command=self.wifi_button_func)
        wifi_menu.add_command(label="Check IP", command=self.display_current_ip)
        wifi_menu.add_command(label="Check SSID", command=self.display_current_ssid)

        # setting up the settings submenu
        settings_menu = tk.Menu(self.menubar, tearoff=0, font=("Helvetica", self.MENU_FONT_SIZE))
        settings_menu.add_command(label="Change magnification", command=self.set_magnification)
        settings_menu.add_command(label="Change coordinates", command=self.set_coordinates)
        settings_menu.add_command(label="Change location", command=self.set_location)
        settings_menu.add_command(label="Change time", command=self.set_time)

        # setting up the help submenu
        help_menu = tk.Menu(self.menubar, tearoff=0, font=("Helvetica", self.MENU_FONT_SIZE))
        help_menu.add_command(label="List of sites", command=self.show_sites)

        self.menubar.add_cascade(label='Astronomy', menu=astronomy_menu)
        self.menubar.add_cascade(label="Wifi", menu=wifi_menu)
        self.menubar.add_cascade(label="Settings", menu=settings_menu)
        self.menubar.add_cascade(label="Help", menu=help_menu)

        CONTROLLER.config(menu=self.menubar)

    def set_location(self):
        location = simpledialog.askstring("Enter new location", "Please enter a new location (astronomical site on Earth)\nThe location is currently \"{}\"".format(self.location), parent=self)

        if location is not None:
            self.update_location(location)
    
    def set_time(self):
        if not self.time_manual:
            self.time = time.strftime("%Y-%m-%d %H:%M:%S")

        obstime = simpledialog.askstring("Enter new time", "Please enter a new time (In this EXACT format: \"YYYY-MM-DD HH:MM:SS\")" +
                                         "\nYou can set it to the current time by typing \"current\"" +
                                         "\nNote: the dashes and spaces are important, so don't miss them out!\n" +
                                         "The time is currently \"{}\"".format(self.time), parent=self)

        if obstime is not None:
            if obstime.lower() == 'current':
                self.update_time(time.strftime("%Y-%m-%d %H:%M:%S"))
                self.time_manual = False
            else:
                self.update_time(obstime)
    
    def set_magnification(self):
        new_mag = simpledialog.askfloat("Enter new magnification", "Please enter a new magnification (0 is the default, -1 is smaller and 1 is bigger.)\nThe magnification is currently {}".format(self.magnification), parent=self)

        if new_mag is not None:
            self.generate_image(0, 0, None, None, new_mag)

    def show_sites(self):
        locations = EarthLocation.get_site_names()

        locations = [location for location in locations if location != '']

        location_string = ', '.join(locations)

        self.display_info("List of astronomical sites:\n{}".format(location_string), "List of sites")
    
    def refresh_planets(self):
        planet_process = threading.Thread(None, lambda: constant_planet_update(True))
        planet_process.start()

        CONTROLLER.after(self.CHECK_FREQUENCY,
                         lambda: self.check_thread(planet_process,
                                                   lambda: self.display_info("Planet positions successfully updated", "Planets updated")))
    
    def set_coordinates(self):
        coordinate_string = simpledialog.askstring("Enter new coordinates", "Please enter new coordinates.\nThe formats \"(hours, minutes, seconds), (degrees, arcmins, arcsecs)\"\n" +
                                                   "and \"hours, degrees\" (where the latter takes values with decimal points) are both acceptable." +
                                                   "\nThe current values are: {} hours, {} degrees".format(round(self.base_ra, 2), round(self.base_de, 2)), parent=self)
        
        if coordinate_string is None:
            return

        coordinate_string = coordinate_string.replace("(", "")
        coordinate_string = coordinate_string.replace(")", "")
        coordinate_string = coordinate_string.replace(" ", "")

        split_string = coordinate_string.split(",")

        if len(split_string) == 2:
            try:
                righta = float(split_string[0])
                dec = float(split_string[1])
            except ValueError:
                self.display_error("That was not a valid input!", "Invalid input")
                return
        elif len(split_string) == 6:
            try:
                hours = float(split_string[0])
                mins = float(split_string[1])
                secs = float(split_string[2])
                degs = float(split_string[3])
                arcmins = float(split_string[4])
                arcsecs = float(split_string[5])
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
        CONTROLLER.config(menu=tk.Menu(self))
    
    def _do_bindings(self):
        CONTROLLER.bind("<Left>", lambda e: self.generate_image(128, 0))
        CONTROLLER.bind("<Right>", lambda e: self.generate_image(-128, 0))
        CONTROLLER.bind("<Up>", lambda e: self.generate_image(0, 128))
        CONTROLLER.bind("<Down>", lambda e: self.generate_image(0, -128))

        CONTROLLER.bind("<Control-a>", lambda e: self.generate_image(128, 0))
        CONTROLLER.bind("<Control-d>", lambda e: self.generate_image(-128, 0))
        CONTROLLER.bind("<Control-w>", lambda e: self.generate_image(0, 128))
        CONTROLLER.bind("<Control-s>", lambda e: self.generate_image(0, -128))

    def show_planet(self, index):
        try:
            self.all_coords = PLANET_COORDINATES.get(block=False)
        except queue.Empty:
            pass
        
        try:
            planet_ra, planet_de = self.all_coords[index]
        except IndexError:
            self.display_error("The planet data has not been generated yet, please wait for the prompt then try again", "Data not available")
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
            self.display_error("The planet data has not been generated yet, please wait for the prompt then try again", "Data not available")
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
    
    def show_object(self):
        obj = simpledialog.askstring("Enter object name", 'Enter the name of the celestial object you would like to find\n(Examples: , "Polaris", M1", "Pleiades", "Andromeda", "Ursa Minor")', parent=self)

        if obj is None:
            return
        
        try:
            righta, dec = get_object_coordinates(obj)
        except NameResolveError:
            self.display_error("This object \"{}\" is not recognised, please choose another object\nNote: Solar system objects must be selected from their menu".format(obj), "Object not recognised")
            return

        self.generate_image(0, 0, righta, dec)
    
    def show_object_info(self):
        obj = simpledialog.askstring("Enter object name", 'Enter the name of the celestial object you would like to find\n(Examples: "Polaris", M1", "Pleiades", "Andromeda", "Ursa Minor")', parent=self)

        if obj is None:
            return
        
        try:
            righta, dec = get_object_coordinates(obj)
        except NameResolveError:
            self.display_error("This object \"{}\" is not recognised, please choose another object\nNote: Solar system objects must be selected from their menu".format(obj), "Object not recognised")
            return

        if not self.time_manual:
            self.time = time.strftime("%Y-%m-%d %H:%M:%S")

        azim, alt = coordinates_from_observer(righta, dec, self.location, self.time)

        visible = "Yes" if alt > UNSEEABLE_START_ALTITUDE else "No" 

        info_string = '''Name — {}
Right Ascension — {} hours
Declination — {} degrees
Azimuth — {} degrees
Altitude — {} degrees
Visible from {}? (latitude {} degrees) — {}
Within {} (Constellation)
(Information generated for {} at location {})'''.format(obj, round(righta, 2), round(dec, 2), round(azim, 2),
                                                        round(alt, 2), self.location, round(self.lat, 2), visible,
                                                        get_constellation(righta, dec), self.time, self.location)
        
        self.display_info(info_string, "Object info")

    def update_location(self, location):
        try:
            self.lat, self.long = get_earth_location_coordinates(location.lower())
        except UnknownSiteException:
            self.display_error("This site is not recognised, please choose another telescope/site\nFor a complete list, check the help section.", "Site not recognised")
            return

        self.location = location
        self.display_info("Location successfully changed to \"{}\"".format(location), "Location change successful")

    def update_time(self, obstime):
        try:
            Time(obstime)
        except ValueError:
            self.display_error("That was not a valid input!", "Invalid input")
            return

        self.time = obstime
        self.time_manual = True

        self.display_info("Time successfully changed to \"{}\"".format(obstime), "Time change successful")

    def render(self, referral=False):
        if referral:
            self._do_bindings()
            CONTROLLER.config(menu=self.menubar)

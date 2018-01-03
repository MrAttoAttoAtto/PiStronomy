import os
import queue
import threading
import time
import tkinter as tk
import uuid
from tkinter import filedialog, messagebox, simpledialog

from astropy.coordinates import EarthLocation
from astropy.coordinates.errors import UnknownSiteException
from astropy.coordinates.name_resolve import NameResolveError
from astropy.time import Time
from PIL import Image, ImageTk
from PIL.Image import ANTIALIAS

from astronomy_gui.controller import CONTROLLER
from astronomy_gui.images import get_imagepath
from astronomy_gui.page import Page
from get_picture import get_sky_picture
from planets import MAPPING_DICT, PLANET_COORDINATES, constant_planet_update
from tools import (from_deg_rep, from_hour_rep, get_constellation,
                   get_coordinates_from_observer,
                   get_earth_location_coordinates, get_magnitude,
                   get_object_coordinates, safe_put)

# True is the system is windows, False otherwise
WINDOWS = os.name == 'nt'

SAVE_INITIAL_DIR = "%userprofile%\\Pictures" if WINDOWS else "/home/pi/Pictures"

# the altitude at which it is considered impossible to see a star (i.e. too close to the horizon)
UNSEEABLE_START_ALTITUDE = 20

# the resolution (x and y) that each image is resized to (to fit)
IMAGE_RESOLUTION = (135, 135)

# astronomy main screen class
class AstroScreen(Page):
    # Pixel ofsets for the pixel shifts of the 3x3 sky view
    IMAGE_PIXEL_OFFSETS = [
        (256, 256),  (0, 256),  (-256, 256),
        (256, 0),    (0, 0),    (-256, 0),
        (256, -256), (0, -256), (-256, -256)
    ]

    def __init__(self, parent):
        #setup things
        super().__init__(parent)

        self.all_coords = []

        # The Pleiades
        self.base_ra = from_hour_rep(3, 47, 24)
        self.base_de = from_deg_rep(24, 7, 0)

        self.shiftx = 0
        self.shifty = 0
        self.magnification = 0.0

        self.location = 'Greenwich'
        self.lat, self.long = get_earth_location_coordinates(self.location.lower())
        self.time = time.strftime("%Y-%m-%d %H:%M:%S")
        self.time_manual = False

        self.width = 800
        self.height = 480
        self.grid()

        planet_update_process = threading.Thread(None, lambda: constant_planet_update(skip=True, screen=self))
        planet_update_process.setDaemon(True)
        planet_update_process.start()

        CONTROLLER.after(self.CHECK_FREQUENCY,
                         lambda: self.check_thread(planet_update_process,
                                                   lambda: self.display_info("Initial planet locations have been calculated", "Planet locations calculated")))

        #instruction label
        #instr_label = tk.Label(self, text="Please select a network to connect to:", font=("Helvetica", 34))
        #instr_label.grid(row=0, column=1, columnspan=3)

        #loading things
        load_image = tk.PhotoImage(file=self.loading_gif_path, format='gif -index 0')

        self.load_label = tk.Label(self, image=load_image, borderwidth=0, highlightthickness=0)
        self.load_label.image = load_image

        self.load_label.grid(row=1, column=1)

        self.image_label_list = [tk.Label(self, image=None, borderwidth=0, highlightthickness=0) for i in range(9)]
        for index, label in enumerate(self.image_label_list):
            row = (index // 3) + 1
            column = (index % 3) + 1

            label.grid(row=row, column=column)
            label.grid_remove()
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(4, weight=1)

        self._setup_menus()

        self._do_bindings()

        self.image_cache = {}

        CONTROLLER.after(self.LOADING_GIF_FREQUENCY, lambda: self.update_loading_gif(1, self.load_label, time.time()))

        self.image_queue_list = [queue.Queue(1) for i in range(9)]

        #shiftx, shifty, new_base_ra=None, new_base_de=None, new_base_magnification=None, overwrite_cache=False

        self.generate_batch_images(0, 0)
    
    def _setup_menus(self):
        self.menubar = tk.Menu(self, font=("Helvetica", self.MENU_FONT_SIZE), background='black', foreground='white',
                               activebackground='#262626', activeforeground='white', borderwidth=1, relief=tk.SUNKEN)

        # setting up the file submenu
        file_menu = tk.Menu(self.menubar, tearoff=0, font=("Helvetica", self.MENU_FONT_SIZE), background='black', foreground='white',
                            activebackground='#262626', activeforeground='white')
        file_menu.add_command(label="Save As", command=self.save_as_image)

        # setting up the astronomy submenu
        astronomy_menu = tk.Menu(self.menubar, tearoff=0, font=("Helvetica", self.MENU_FONT_SIZE), background='black', foreground='white',
                                 activebackground='#262626', activeforeground='white')

        planet_goto_menu = tk.Menu(astronomy_menu, tearoff=0, font=("Helvetica", self.MENU_FONT_SIZE), background='black', foreground='white',
                                   activebackground='#262626', activeforeground='white')
        planet_info_menu = tk.Menu(astronomy_menu, tearoff=0, font=("Helvetica", self.MENU_FONT_SIZE), background='black', foreground='white',
                                   activebackground='#262626', activeforeground='white')
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
        wifi_menu = tk.Menu(self.menubar, tearoff=0, font=("Helvetica", self.MENU_FONT_SIZE), background='black', foreground='white',
                            activebackground='#262626', activeforeground='white')
        wifi_menu.add_command(label='Open Wifi Screen', command=self.wifi_button_func)
        wifi_menu.add_command(label="Check IP", command=self.display_current_ip)
        wifi_menu.add_command(label="Check SSID", command=self.display_current_ssid)

        # setting up the settings submenu
        settings_menu = tk.Menu(self.menubar, tearoff=0, font=("Helvetica", self.MENU_FONT_SIZE), background='black', foreground='white',
                                activebackground='#262626', activeforeground='white')
        settings_menu.add_command(label="Change magnification", command=self.set_magnification)
        settings_menu.add_command(label="Change coordinates", command=self.set_coordinates)
        settings_menu.add_command(label="Change location", command=self.set_location)
        settings_menu.add_command(label="Change time", command=self.set_time)

        # setting up the help submenu
        help_menu = tk.Menu(self.menubar, tearoff=0, font=("Helvetica", self.MENU_FONT_SIZE), background='black', foreground='white',
                            activebackground='#262626', activeforeground='white')
        help_menu.add_command(label="List of sites", command=self.show_sites)
        help_menu.add_command(label="Movement slow?", command=self.slow_move)
        help_menu.add_command(label="Save and Save as", command=self.save_vs_saveas)

        self.menubar.add_cascade(label='File', menu=file_menu)
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
            self.generate_batch_images(0, 0, new_base_magnification=new_mag, overwrite_cache=True)

    def show_sites(self):
        locations = EarthLocation.get_site_names()

        locations = [location for location in locations if location != '']

        location_string = ', '.join(locations)

        self.display_info("List of astronomical sites:\n{}".format(location_string), "List of sites")
    
    def slow_move(self):
        info_string = "The movement will be slow for around the first minute the application is open, after that it should operate noticibly faster!"

        self.display_info(info_string, "Slow startup")
    
    def save_vs_saveas(self):
        info_string = ("\"Save as\" ALWAYS asks you for the folder and name you would like to save it as. " +
        "\"Save\", on the other hand, only asks the first time (or never if \"Save as\" has already been used) " +
        "and then saves the picture straight to the already-selected folder with the time as its name. " +
        "This folder can be changed by using \"Save as\" again.")

        self.display_info(info_string, "Save and Save as")
    
    def refresh_planets(self):
        planet_process = threading.Thread(None, lambda: constant_planet_update(True, screen=self))
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

        self.generate_batch_images(0, 0, righta, dec, overwrite_cache=True)

    def display_image(self, all_cached=False):
        print("Pics done")

        self.load_label.grid_remove()

        for index in range(9):
            starttime = time.time()

            while True and time.time() - starttime < 1:
                try:
                    image, shiftx, shifty = self.image_queue_list[index].get(block=False)
                    break
                except queue.Empty:
                    if all_cached:
                        return
                    continue

            try:
                if not (shiftx, shifty) in self.image_cache:
                    self.image_cache[(shiftx, shifty)] = image
            except UnboundLocalError:
                self.display_error("Whoah man! Easy on the movement! In all seriousness, spamming makes it break, but this can be fixed by just moving again (this time slowly!). " +
                                   "If you really need to scratch that spamming itch, load the images into the cache (by moving around) and then you can spam to your heart's content " +
                                   "within the images that you just loaded!", "Spamming is bad")
                return
            
            if not all_cached:
                self.image_label_list[index].grid_remove()
            
            image = image.resize(IMAGE_RESOLUTION, ANTIALIAS)

            tk_image = ImageTk.PhotoImage(image)

            self.image_label_list[index].configure(image=tk_image)
            self.image_label_list[index].image = tk_image

            self.image_label_list[index].grid()
    
    def generate_batch_images(self, shiftx, shifty, new_base_ra=None, new_base_de=None, new_base_magnification=None, overwrite_cache=False):
        if overwrite_cache:
            self.image_cache = {}

        if new_base_ra is not None:
            self.base_ra = new_base_ra

        if new_base_de is not None:
            self.base_de = new_base_de
        
        if new_base_de is not None or new_base_ra is not None:
            self.shiftx = 0
            self.shifty = 0
        
        if new_base_magnification is not None:
            self.magnification = new_base_magnification

        # shift for the middle square
        self.shiftx += shiftx
        self.shifty += shifty
        
        image_processes = []
        cached = 0
        
        for index, (aug_shiftx, aug_shifty) in enumerate(self.IMAGE_PIXEL_OFFSETS):
            real_shiftx = self.shiftx + aug_shiftx
            real_shifty = self.shifty + aug_shifty

            if (real_shiftx, real_shifty) in self.image_cache:
                print("Cached!")
                cached += 1
                safe_put(self.image_queue_list[index], (self.image_cache[(real_shiftx, real_shifty)], real_shiftx, real_shifty))
                continue

            image_process = threading.Thread(None, lambda real_shiftx=real_shiftx,real_shifty=real_shifty,index=index: safe_put(self.image_queue_list[index],
                                                                                                                                (get_sky_picture(self.base_ra, self.base_de, real_shiftx, real_shifty, self.magnification),
                                                                                                                                 real_shiftx, real_shifty)))
            image_process.setDaemon(True)
            image_process.start()

            image_processes.append(image_process)

        if not cached == 9:
            for label in self.image_label_list:
                label.grid_remove()
        
            self.load_label.grid(row=2, column=2)
            CONTROLLER.after(self.LOADING_GIF_FREQUENCY, lambda: self.update_loading_gif(1, self.load_label, time.time()))

        CONTROLLER.after(self.CHECK_FREQUENCY,
                         lambda: self.check_thread(image_processes,
                                                   lambda cached=cached: self.display_image(cached == 9),
                                                   True))
    
    def wifi_button_func(self):
        CONTROLLER.unbind("<Left>")
        CONTROLLER.unbind("<Right>")
        CONTROLLER.unbind("<Up>")
        CONTROLLER.unbind("<Down>")

        CONTROLLER.show_page('WifiScreen')
        CONTROLLER.config(menu=tk.Menu(self))
    
    def _do_bindings(self):
        CONTROLLER.bind("<Left>", lambda e: self.generate_batch_images(256, 0))
        CONTROLLER.bind("<Right>", lambda e: self.generate_batch_images(-256, 0))
        CONTROLLER.bind("<Up>", lambda e: self.generate_batch_images(0, 256))
        CONTROLLER.bind("<Down>", lambda e: self.generate_batch_images(0, -256))

        CONTROLLER.bind("<Control-a>", lambda e: self.generate_batch_images(256, 0))
        CONTROLLER.bind("<Control-d>", lambda e: self.generate_batch_images(-256, 0))
        CONTROLLER.bind("<Control-w>", lambda e: self.generate_batch_images(0, 256))
        CONTROLLER.bind("<Control-s>", lambda e: self.generate_batch_images(0, -256))

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

        self.generate_batch_images(0, 0, planet_ra, planet_de, overwrite_cache=True)
    
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

        name = next((name for name, map_index in MAPPING_DICT.items() if map_index == index))

        if not self.time_manual:
            self.time = time.strftime("%Y-%m-%d %H:%M:%S")

        planet_az, planet_alt = get_coordinates_from_observer(planet_ra, planet_de, self.location, self.time)

        visible = self.calculate_visibility(planet_az, planet_alt, self.time, self.location, "N/A", name=="Sun", name=="Moon")

        info_string = '''Name — {}
Right Ascension — {} hours
Declination — {} degrees
Azimuth — {} degrees
Altitude — {} degrees
Visible from {}? (latitude {} degrees) — {}
Within {} (Constellation)
(Information generated for {} at location {})'''.format(name, round(planet_ra, 2), round(planet_de, 2), round(planet_az, 2), round(planet_alt, 2),
                                                        self.location, round(self.lat, 2), visible, get_constellation(planet_ra, planet_de),
                                                        self.time, self.location)

        self.display_info(info_string, "Planet info")
    
    def show_object(self):
        obj = simpledialog.askstring("Enter object name", 'Enter the name of the celestial object you would like to find\n(Examples: , "Polaris", "M1", "Pleiades", "Andromeda", "Ursa Minor", "Orion")', parent=self)

        if obj is None:
            return
        
        try:
            righta, dec = get_object_coordinates(obj)
        except NameResolveError:
            self.display_error("This object \"{}\" is not recognised, please choose another object\nNote: Solar system objects must be selected from their menu".format(obj), "Object not recognised")
            return

        self.generate_batch_images(0, 0, righta, dec, overwrite_cache=True)
    
    def show_object_info(self):
        obj = simpledialog.askstring("Enter object name", 'Enter the name of the celestial object you would like to find\n(Examples: "Polaris", "M1", "Pleiades", "Andromeda", "Ursa Minor", "Orion")', parent=self)

        if obj is None:
            return
        
        try:
            righta, dec = get_object_coordinates(obj)
        except NameResolveError:
            self.display_error("This object \"{}\" is not recognised, please choose another object\nNote: Solar system objects must be selected from their menu".format(obj), "Object not recognised")
            return

        if not self.time_manual:
            self.time = time.strftime("%Y-%m-%d %H:%M:%S")

        azim, alt = get_coordinates_from_observer(righta, dec, self.location, self.time)

        mag = get_magnitude(obj)

        if mag is None:
            mag = "N/A"

        visible = self.calculate_visibility(azim, alt, self.time, self.location, mag)

        info_string = '''Name — {}
Right Ascension — {} hours
Declination — {} degrees
Azimuth — {} degrees
Altitude — {} degrees
Apparent Magnitude — {}
Visible from {}? (latitude {} degrees) — {}
Within {} (Constellation)
(Information generated for {} at location {})'''.format(obj, round(righta, 2), round(dec, 2), round(azim, 2),
                                                        round(alt, 2), mag, self.location, round(self.lat, 2), visible,
                                                        get_constellation(righta, dec), self.time, self.location)
        
        self.display_info(info_string, "Object info")
    
    def calculate_visibility(self, azim, alt, obstime, location, mag, sun=False, moon=False):
        visible_factor = 2
        impeders = []
        warnings = []

        try:
            self.all_coords = PLANET_COORDINATES.get(block=False)
        except queue.Empty:
            pass
        
        try:
            moon_ra, moon_dec = self.all_coords[8]
            sun_ra, sun_dec = self.all_coords[9]

            moon_az, moon_alt = get_coordinates_from_observer(moon_ra, moon_dec, location, obstime)
            sun_az, sun_alt = get_coordinates_from_observer(sun_ra, sun_dec, location, obstime)

            if not sun:
                if sun_alt > 10:
                    if moon:
                        visible_factor = visible_factor if visible_factor != 2 else 1
                    else:
                        visible_factor = 0
                    
                    impeders.append("being viewed when the sun is up")
                elif sun_alt > -5:
                    if not moon:
                        visible_factor = visible_factor if visible_factor != 2 else 1
                        impeders.append("being viewed when the sun is coming up")
            
            if not moon and not sun:
                if abs(moon_az-azim) < 2 or abs(moon_alt-alt) < 2:
                    visible_factor = 0
                    impeders.append("very close to the moon")
                elif abs(moon_az-azim) < 5 or abs(moon_alt-alt) < 5:
                    visible_factor = visible_factor if visible_factor != 2 else 1
                    impeders.append("close to the moon")
        except IndexError:
            warnings.append("the solar system objects have not yet been computed, so either wait and run this again or take these into account yourself")
            pass

        

        if alt < 0:
            visible_factor = 0
            impeders.append("below the horizon")
        elif alt < 20:
            if not sun:
                visible_factor = visible_factor if visible_factor != 2 else 1
                impeders.append("very close to the horizon")
        
        if mag != "N/A":
            if mag > 7:
                visible_factor = visible_factor if visible_factor != 2 else 1
                impeders.append("low magnitude")
            elif mag > 10:
                visible_factor = 0
                impeders.append("very low magnitude")
        else:
            warnings.append("magnitude could not be calculated, so take this into account yourself")
        
        if visible_factor == 0:
            message = "No\nReason(s): {}".format(', '.join(impeders))
        elif visible_factor == 1:
            message = "Probably not\nReason(s): {}".format(', '.join(impeders))
        else:
            message = "Yes"

        return message

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
    
    def save_as_image(self):
        fil = filedialog.asksaveasfilename(defaultextension='.png', filetypes=[("PNG", ".png"), ("JPEG", ".jpeg"),
                                                                           ("JPEG", ".jpg"), ("GIF", ".gif"),
                                                                           ("BMP", ".bmp")],
                                       initialdir=SAVE_INITIAL_DIR, initialfile=time.strftime("%Y-%m-%d %Hh %Mm %Ss"), parent=self, title="Save Image")
        
        if fil == '':
            return

        full_im = Image.new('RGB', (768, 768))

        for shiftx, shifty in self.IMAGE_PIXEL_OFFSETS:
            true_shiftx = shiftx + self.shiftx
            true_shifty = shifty + self.shifty

            positional_shiftx = abs(shiftx - 256)
            positional_shifty = abs(shifty - 256)

            full_im.paste(self.image_cache[(true_shiftx, true_shifty)], (positional_shiftx, positional_shifty))
        
        full_im.save(fil)

    def render(self, referral=False):
        if referral:
            self._do_bindings()
            CONTROLLER.config(menu=self.menubar)

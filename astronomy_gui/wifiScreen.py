import json
import os
import queue
import threading
import time
import tkinter as tk
from tkinter import simpledialog, messagebox

from astronomy_gui.controller import CONTROLLER
from astronomy_gui.page import Page
from tools import get_all_ssids, mobile_connect, get_current_ssid, delete_prior_connection


# Constant that is TRUE if being run on windows
WINDOWS = os.name == 'nt'

# wifi screen class
class WifiScreen(Page):
    """
    The class for an instance of Page that handles wifi-type functions
    """

    def __init__(self, parent):
        # setup things
        super().__init__(parent)

        # Background black for viewing at night and outside
        self.config(bg="black")

        self.current_network = 'NOT CONNECTED'

        # Loads the current wifi settings stored in "wifi_settings.json" (dict of ssid and password)
        try:
            self.known_configurations = json.load(open("wifi_settings.json"))
        except FileNotFoundError:
            self.known_configurations = []
            json.dump(self.known_configurations, open("wifi_settings.json", "w+"), sort_keys=True, indent=4)
        self.known_ssids = [diction['ssid'] for diction in self.known_configurations]

        # Loads in the loading cog image to display
        load_image = tk.PhotoImage(file=self.loading_gif_path, format='gif -index 0')

        # Sets up the size config for the pi screen (With the correct resolutions)
        self.width = 800
        self.height = 480
        self.grid()

        # Instruction label
        instr_label = tk.Label(self, text="Please select a network to connect to:", font=("Helvetica", 34), bg="black", fg="white")
        instr_label.grid(row=0, column=1, columnspan=3)

        # Loading things
        self.load_label = tk.Label(self, image=load_image)
        self.load_label.image = load_image

        # Sets up the scrollbar and list for wifi selection
        self.ssid_scrollbar = tk.Scrollbar(self, bg="black")
        self.ssid_listbox = tk.Listbox(self, yscrollcommand=self.ssid_scrollbar.set, font=("Helvetica", 20),
                                       selectbackground='#363636', bg="black", fg="white")

        # Different OSes look good with different things
        if WINDOWS:
            self.load_label.grid(row=1, column=0, columnspan=5, rowspan=3, pady=37)
        else:
            self.load_label.grid(row=1, column=0, columnspan=5, rowspan=3, pady=28)

        # Submit button things
        submit_button = tk.Button(self, text="Connect", command=self.wifi_connect, font=("Helvetica", 20), fg='green',
                                  activeforeground='green', bg="black", activebackground='#262626')
        submit_button.grid(row=4, column=2, pady=16)

        # Back button things
        back_button = tk.Button(self, text="Back", command=self.back, font=("Helvetica", 20), fg='red',
                                activeforeground='red', bg='black', activebackground='#262626')
        back_button.grid(row=4, column=1, pady=16)

        # Refresh button things
        refresh_button = tk.Button(self, text="Refresh", command=self.wifi_refresh, font=("Helvetica", 20), fg='cyan',
                                   activeforeground='cyan', bg='black', activebackground='#262626')
        refresh_button.grid(row=4, column=3, pady=16)

        # Sets up the animation of the loading cog
        CONTROLLER.after(self.LOADING_GIF_FREQUENCY, lambda: self.update_loading_gif(1, self.load_label, time.time()))

        # Sets up another thread to do the task of getting all available ssids
        self.ssid_queue = queue.Queue(1)
        ssid_list_process = threading.Thread(None, lambda: self.ssid_queue.put((get_all_ssids(), get_current_ssid())))
        ssid_list_process.start()
        CONTROLLER.after(self.CHECK_FREQUENCY,
                         lambda: self.check_thread(ssid_list_process,
                                                   self.display_ssids))

    def _setup_menus(self):
        self.menubar = tk.Menu(self, font=("Helvetica", self.MENU_FONT_SIZE), background='black', foreground='white',
                               activebackground='#262626', activeforeground='white', borderwidth=1, relief=tk.SUNKEN)

        # setting up the file submenu
        file_menu = tk.Menu(self.menubar, tearoff=0, font=("Helvetica", self.MENU_FONT_SIZE), background='black', foreground='white',
                            activebackground='#262626', activeforeground='white')
        file_menu.add_command(label="Exit", command=CONTROLLER.destroy)

        # setting up the wifi submenu
        wifi_menu = tk.Menu(self.menubar, tearoff=0, font=("Helvetica", self.MENU_FONT_SIZE), background='black', foreground='white',
                            activebackground='#262626', activeforeground='white')
        wifi_menu.add_command(label='Leave Wifi Screen', command=self.back)
        wifi_menu.add_command(label="Check IP", command=self.display_current_ip)
        wifi_menu.add_command(label="Check SSID", command=self.display_current_ssid)

        # setting up the settings submenu
        settings_menu = tk.Menu(self.menubar, tearoff=0, font=("Helvetica", self.MENU_FONT_SIZE), background='black', foreground='white',
                                activebackground='#262626', activeforeground='white')
        settings_menu.add_command(label="Delete saved credentials", command=self.delete_saved_connection)

        # setting up the help submenu
        help_menu = tk.Menu(self.menubar, tearoff=0, font=("Helvetica", self.MENU_FONT_SIZE), background='black', foreground='white',
                            activebackground='#262626', activeforeground='white')
        help_menu.add_command(label="Using this screen", command=self.how_to)
        help_menu.add_command(label="Deleting saved credentials", command=self.how_del)
        help_menu.add_command(label="Using a keyboard from your phone", command=self.how_use_phone)
        help_menu.add_command(label="Special Thanks", command=self.special_thanks)

        # adds all the submenus to the main menu
        self.menubar.add_cascade(label='File', menu=file_menu)
        self.menubar.add_cascade(label="Wifi", menu=wifi_menu)
        self.menubar.add_cascade(label="Settings", menu=settings_menu)
        self.menubar.add_cascade(label="Help", menu=help_menu)

        # sets the menu of the root Tk instance to what has just been generated
        CONTROLLER.config(menu=self.menubar)

    def how_to(self):
        """
        All of these how_* are help functions which just display a help
        box to the user with nice info
        """
        info_string = ("This screen is used to connect to a different wifi (your phone's personal hotspot for example). " +
                       "When connecting, you put in the password and this is automatically saved over sessions, unless it is deleted " +
                       "from the settings submenu. The primary use is to allow you to easily connect to a phone, so that while on the school " +
                       "wifi you can use your phone as a keyboard.")

        self.display_info(info_string, "Using this screen")

    def how_del(self):
        """
        All of these how_* are help functions which just display a help
        box to the user with nice info
        """
        info_string = ("Credentials are automatically saved the first time you input them. " +
                       "In order to delete them, select the \"Delete saved credentials\" option from the \"Settings\" submenu " +
                       "while selecting the wifi you wish to delete.")

        self.display_info(info_string, "Deleting credentials")
    
    def how_use_phone(self):
        """
        All of these how_* are help functions which just display a help
        box to the user with nice info
        """
        info_string = ("To use your phone as a keyboard, the first step is to download the \"Unified Remote\" app from your " +
                       "device's app store. Then, connect the Pi to your phone's personal hotspot (or, if it is in range, " +
                       "your personal wifi). Next, in the \"Wifi\" menu, select \"Check IP\" and input this value " +
                       "into the \"Host IP / Address\" field, after having selected \"Add a server manually\" from the \"Servers\" " +
                       "screen. You may change the \"Display name\" field to whatever you please, but keep the rest as default and " +
                       "select \"Done\". From here, make sure that your new server is selected and go back to the \"Remotes\" screen. " +
                       "From here, you may use any of the remotes, however, I suggest the standard keyboard as you can use the " +
                       "mouse from this screen (bottom-right corner) and may use the \"ctrl\" key for moving. Note: it may say " +
                       "\"Feature Locked\" if you try to use the \"ctrl\" or other special keys, but if they are used directly " +
                       "from the keyboard they will work (i.e. not from the iOS or Android intergrated keyboards). Another note: " +
                       "to use the \"ctrl\" and other similar keys, they must be pressed, then the other key (such as \"w\") " + 
                       "should be pressed, and then the special key pressed AGAIN to release it, otherwise it will not work.")

        self.display_info(info_string, "Using your phone to control the keyboard")
    
    def special_thanks(self):
        """
        Displays thanks to those who deserve it
        """
        info_string = ("Special thanks to:\nBhuvan Belur for some female-female cables for testing\nJoe Bell for " +
                       "many ideas that I could incorporate int omy program\nProbably some other people")

        self.display_info(info_string, "Special Thanks")

    def display_ssids(self):
        """
        Having gotten the ssids as a list in self.ssid_queue for the FIRST time,
        this function uses that list and generates the tkinter
        listbox from that info for the user to choose a wifi connection from

        In case of an error getting ssids, it just displays one element saying
        "ERROR GETTING AVAILABLE NETWORKS"
        """
        try:
            result_tuple = self.ssid_queue.get(block=False)
            print(result_tuple)
            ssids = result_tuple[0]
            self.current_network = result_tuple[1] or "NOT CONNECTED"
        except queue.Empty:
            print("ERROR GETTING AVAILABLE NETWORKS")
            ssids = ["Could not acquire network information, please refresh"]

        self.load_label.grid_remove()

        self.ssid_scrollbar.grid(row=1, column=4, rowspan=3, sticky=tk.W+tk.N+tk.S)

        saved_available_indexes = []

        for ssid in ssids:
            if ssid == self.current_network:
                connect_index = ssids.index(ssid)
                ssid += " - Connected"
            elif ssid in self.known_ssids:
                saved_available_indexes.append(ssids.index(ssid))
                ssid += " - Saved"
            self.ssid_listbox.insert(tk.END, ssid)

        if 'connect_index' in locals():
            self.ssid_listbox.itemconfig(connect_index, fg='green', selectforeground="green")

        for index in saved_available_indexes:
            self.ssid_listbox.itemconfig(index, fg='cyan', selectforeground="cyan")

        self.ssid_listbox.grid(row=1, column=0, rowspan=3, columnspan=4, sticky=tk.N+tk.S+tk.E+tk.W)

        self.ssid_scrollbar.config(command=self.ssid_listbox.yview)

    def wifi_connect(self):
        """
        Connects to a specified network that has been chosen in the listbox, as well as
        updating wifi_settings.json if it is a new login
        """
        selected_ssid = self.ssid_listbox.get(self.ssid_listbox.curselection()[0])

        if selected_ssid[:-12] == self.current_network:
            self.display_error("You can't connect to the same network you're connected to!", "Connection error")
            return

        if selected_ssid[:-8] in self.known_ssids:
            selected_ssid = selected_ssid[:-8]

        if not selected_ssid in self.known_ssids:
            psk = simpledialog.askstring("Enter Password", "Please enter the password for \"{}\"".format(selected_ssid), show="*", parent=self)

            if psk is None:
                self.display_error("A password cannot be empty", "Empty Password")
                return

            self.known_configurations.append({"ssid":selected_ssid, "psk":psk})
            self.known_ssids = [diction['ssid'] for diction in self.known_configurations]

            json.dump(self.known_configurations, open("wifi_settings.json", "w"), sort_keys=True, indent=4)

        else:
            for diction in self.known_configurations:
                if diction['ssid'] == selected_ssid:
                    psk = diction['psk']
                    break

        self.ssid_listbox.grid_remove()
        self.ssid_scrollbar.grid_remove()

        self.load_label.grid()

        CONTROLLER.after(self.LOADING_GIF_FREQUENCY, lambda: self.update_loading_gif(1, self.load_label, time.time()))

        change_connection_process = threading.Thread(None, lambda: (delete_prior_connection(), mobile_connect(selected_ssid, psk),
                                                                    self.ssid_queue.put((get_all_ssids(), get_current_ssid()))))
        change_connection_process.start()

        CONTROLLER.after(self.CHECK_FREQUENCY,
                         lambda: self.check_thread(change_connection_process,
                                                   self.update_ssids))

    def wifi_refresh(self):
        """
        Refreshes th list of wifis in a seperate thread
        """
        self.ssid_listbox.grid_remove()
        self.ssid_scrollbar.grid_remove()

        self.load_label.grid()

        CONTROLLER.after(self.LOADING_GIF_FREQUENCY, lambda: self.update_loading_gif(1, self.load_label, time.time()))

        ssid_list_process = threading.Thread(None, lambda: self.ssid_queue.put((get_all_ssids(), get_current_ssid())))
        ssid_list_process.start()

        CONTROLLER.after(self.CHECK_FREQUENCY,
                         lambda: self.check_thread(ssid_list_process,
                                                   self.update_ssids))

    def back(self):
        """
        Returns to the Astronomy main screen
        """
        CONTROLLER.config(menu=tk.Menu(self))
        CONTROLLER.show_page('AstroScreen', True)

    def delete_saved_connection(self):
        """
        Deletes a saved password and known ssid from wifi_settings.json (if it exists there)
        """
        try:
            selected_ssid = self.ssid_listbox.get(self.ssid_listbox.curselection()[0])
        except IndexError:
            return

        if selected_ssid[:-8] not in self.known_ssids:
            self.display_error("No login is saved for this wifi!", "No data found")
            return

        selected_ssid = selected_ssid[:-8]

        print(selected_ssid)
        print(self.known_ssids)

        resp = messagebox.askyesno("Delete \"{}\"".format(selected_ssid), "Are you sure you want to delete the password for \"{}\"?".format(selected_ssid))

        if resp:
            for index, config in enumerate(self.known_configurations):
                if config["ssid"] == selected_ssid:
                    del self.known_configurations[index]
            for index, ssid in enumerate(self.known_ssids):
                if ssid == selected_ssid:
                    del self.known_ssids[index]
            
            self.known_ssids = [diction['ssid'] for diction in self.known_configurations]

            json.dump(self.known_configurations, open("wifi_settings.json", "w"), sort_keys=True, indent=4)
            
            self.wifi_refresh()

    def update_ssids(self):
        """
        Does what display_ssids does, but without the first-time setup bits
        """
        try:
            result_tuple = self.ssid_queue.get(block=False)
            ssids = result_tuple[0]
            self.current_network = result_tuple[1] or "NOT CONNECTED"
            #self.current_network = 'NETGEAR59-5G'
        except queue.Empty:
            print("ERROR GETTING AVAILABLE NETWORKS")
            ssids = ["Could not acquire network information, please refresh"]

        self.load_label.grid_remove()

        self.ssid_listbox.delete(0, tk.END)

        saved_available_indexes = []

        for ssid in ssids:
            if ssid == self.current_network:
                connect_index = ssids.index(ssid)
                ssid += " - Connected"
            elif ssid in self.known_ssids:
                saved_available_indexes.append(ssids.index(ssid))
                ssid += " - Saved"
            self.ssid_listbox.insert(tk.END, ssid)

        if 'connect_index' in locals():
            self.ssid_listbox.itemconfig(connect_index, fg='green')

        for index in saved_available_indexes:
            self.ssid_listbox.itemconfig(index, fg='cyan')

        self.ssid_scrollbar.grid()
        self.ssid_listbox.grid()
    
    def render(self, data):
        '''
        A function which is run after the screen has been initialised and every time it wants to be displayed
        '''
        self._setup_menus()
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

WINDOWS = os.name == 'nt'

#wifi screen class
class WifiScreen(Page):
    def __init__(self, parent):
        #setup things
        super().__init__(parent)

        self.current_network = 'NOT CONNECTED'

        self.known_configurations = json.load(open("wifi_settings.json"))
        self.known_ssids = [diction['ssid'] for diction in self.known_configurations]

        load_image = tk.PhotoImage(file=self.loading_gif_path, format='gif -index 0')

        self.width = 800
        self.height = 480
        self.grid()

        #instruction label
        instr_label = tk.Label(self, text="Please select a network to connect to:", font=("Helvetica", 34))
        instr_label.grid(row=0, column=1, columnspan=3)

        #loading things
        self.load_label = tk.Label(self, image=load_image)
        self.load_label.image = load_image

        self.ssid_scrollbar = tk.Scrollbar(self)
        self.ssid_listbox = tk.Listbox(self, yscrollcommand=self.ssid_scrollbar.set, font=("Helvetica", 20))

        if WINDOWS:
            self.load_label.grid(row=1, column=0, columnspan=5, rowspan=3, pady=37)
        else:
            self.load_label.grid(row=1, column=0, columnspan=5, rowspan=3, pady=28)

        #submit button things
        submit_button = tk.Button(self, text="Connect", command=self.wifi_connect, font=("Helvetica", 20), fg='green', activeforeground='green')
        #submit_button.image = lockedButton
        submit_button.grid(row=4, column=2, pady=16)

        #back button things
        back_button = tk.Button(self, text="Back", command=self.back, font=("Helvetica", 20), fg='red', activeforeground='red')
        back_button.grid(row=4, column=1, pady=16)

        #refresh button things
        refresh_button = tk.Button(self, text="Refresh", command=self.wifi_refresh, font=("Helvetica", 20), fg='cyan', activeforeground='cyan')
        refresh_button.grid(row=4, column=3, pady=16)

        CONTROLLER.after(self.LOADING_GIF_FREQUENCY, lambda: self.update_loading_gif(1, self.load_label, time.time()))

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

        self.menubar.add_cascade(label='File', menu=file_menu)
        self.menubar.add_cascade(label="Wifi", menu=wifi_menu)
        self.menubar.add_cascade(label="Settings", menu=settings_menu)
        self.menubar.add_cascade(label="Help", menu=help_menu)

        CONTROLLER.config(menu=self.menubar)

    def how_to(self):
        info_string = ("This screen is used to connect to a different wifi (your phone's personal hotspot for example). " +
                       "When connecting, you put in the password and this is automatically saved over sessions, unless it is deleted " +
                       "from the settings submenu. The primary use is to allow you to easily connect to a phone, so that while on the school " +
                       "wifi you can use your phone as a keyboard.")

        self.display_info(info_string, "Using this screen")

    def how_del(self):
        info_string = ("Credentials are automatically saved the first time you input them. " +
                       "In order to delete them, select the \"Delete saved credentials\" option from the \"Settings\" submenu " +
                       "while selecting the wifi you wish to delete.")

        self.display_info(info_string, "Deleting credentials")
    
    def how_use_phone(self):
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

    def display_ssids(self):
        try:
            result_tuple = self.ssid_queue.get(block=False)
            print(result_tuple)
            ssids = result_tuple[0]
            self.current_network = result_tuple[1] or "NOT CONNECTED"
            #self.current_network = 'NETGEAR59-5G'
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
            self.ssid_listbox.itemconfig(connect_index, fg='green')

        for index in saved_available_indexes:
            self.ssid_listbox.itemconfig(index, fg='cyan')

        self.ssid_listbox.grid(row=1, column=0, rowspan=3, columnspan=4, sticky=tk.N+tk.S+tk.E+tk.W)

        self.ssid_scrollbar.config(command=self.ssid_listbox.yview)

    def wifi_connect(self):
        selected_ssid = self.ssid_listbox.get(self.ssid_listbox.curselection()[0])

        if selected_ssid[:-12] == self.current_network:
            self.display_error("You can't connect to the same network you're connected to!", "Connection error")
            return

        if selected_ssid in self.known_ssids:
            selected_ssid = selected_ssid[:-8]

        if not selected_ssid in self.known_ssids:
            psk = simpledialog.askstring("Enter Password", "Please enter the password for \"{}\"".format(selected_ssid), show="*", parent=self)

            if psk is None:
                self.display_error("A password cannot be empty", "Empty Password")
                return

            self.known_configurations.append({"ssid":selected_ssid, "psk":psk})

            json.dump(self.known_configurations, open("wifi_settings.json", "w"))

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
        CONTROLLER.config(menu=tk.Menu(self))
        CONTROLLER.show_page('AstroScreen', True)

    def delete_saved_connection(self):
        selected_ssid = self.ssid_listbox.get(self.ssid_listbox.curselection()[0])

        if selected_ssid not in self.known_ssids:
            self.display_error("No login is saved for this wifi!", "No data found")
            return

        resp = messagebox.askyesno("Delete \"{}\"".format(selected_ssid), "Are you sure you want to delete the password for \"{}\"?".format(selected_ssid))

        if resp:
            for index, config in enumerate(self.known_configurations):
                if config["ssid"] == selected_ssid:
                    del self.known_configurations[index]
            for index, ssid in enumerate(self.known_ssids):
                if ssid == selected_ssid:
                    del self.known_ssids[index]

            json.dump(self.known_configurations, open("wifi_settings.json", "w"))

    def update_ssids(self):
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
        self._setup_menus()

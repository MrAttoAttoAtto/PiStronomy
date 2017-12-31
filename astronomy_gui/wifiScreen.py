import json
import os
import queue
import threading
import tkinter as tk

from astronomy_gui.controller import CONTROLLER
from astronomy_gui.images import get_imagepath
from astronomy_gui.page import Page
from tools import get_all_ssids, mobile_connect, get_current_ssid

WINDOWS = os.name == 'nt'

# ms before gif update
LOADING_GIF_FREQUENCY = 30

# ms before thread re-check
CHECK_FREQUENCY = 200

#locked screen class
class WifiScreen(Page):
    def __init__(self, parent):
        #setup things
        super().__init__(parent)

        self.known_configuarions = json.load(open("wifi_settings.json"))

        self.loading_gif_path = get_imagepath("loadingIcon")
        print(self.loading_gif_path)

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

        CONTROLLER.after(LOADING_GIF_FREQUENCY, lambda: self.update_loading_gif(1, self.load_label))

        self.ssid_queue = queue.Queue(1)

        ssid_list_process = threading.Thread(None, lambda: self.ssid_queue.put((get_all_ssids(), get_current_ssid())))
        ssid_list_process.start()

        CONTROLLER.after(CHECK_FREQUENCY,
                         lambda: self.check_thread(ssid_list_process,
                                                   lambda: self.display_ssids(self.load_label)))

    def update_loading_gif(self, index, label):
        ''' update gif things '''
        if not label.winfo_ismapped():
            return

        try:
            loading_image = tk.PhotoImage(file=self.loading_gif_path,
                                          format="gif -index {}".format(index))
        except tk.TclError:
            loading_image = tk.PhotoImage(file=self.loading_gif_path, format="gif -index 0")
            index = 0

        label.configure(image=loading_image)
        label.image = loading_image

        CONTROLLER.after(LOADING_GIF_FREQUENCY, lambda: self.update_loading_gif(index+1, label))

    def check_thread(self, thread, callback):
        if thread.is_alive():
            CONTROLLER.after(CHECK_FREQUENCY, lambda: self.check_thread(thread, callback))
        else:
            callback()

    def display_ssids(self, label):
        try:
            ssids, self.current_network = self.ssid_queue.get(block=False)
            print(ssids)
        except queue.Empty:
            print("ERROR GETTING AVAILABLE NETWORKS")
            ssids = ["Could not acquire network information, please refresh"]

        label.grid_remove()

        self.ssid_scrollbar = tk.Scrollbar(self)
        self.ssid_scrollbar.grid(row=1, column=4, rowspan=3, sticky=tk.W+tk.N+tk.S)

        self.ssid_listbox = tk.Listbox(self, yscrollcommand=self.ssid_scrollbar.set, font=("Helvetica", 20))

        for ssid in ssids:
            if ssid == self.current_network:
                ssid += " - Connected"
            self.ssid_listbox.insert(tk.END, ssid)
        self.ssid_listbox.grid(row=1, column=0, rowspan=3, columnspan=4, sticky=tk.N+tk.S+tk.E+tk.W)

        self.ssid_scrollbar.config(command=self.ssid_listbox.yview)
    
    def wifi_connect(self):
        selected_ssid = self.ssid_listbox.get(self.ssid_listbox.curselection()[0])

        if selected_ssid[:-12] == self.current_network:
            # error! You can't connect to the network you're already connected to!
            print("You can't connect to the same network you're connected to!")
            # TODO: add error box

        if not selected_ssid in [diction['ssid'] for diction in self.known_configuarions]:
            # do extra password getting
            pass
        else:
            for diction in self.known_configuarions:
                if diction['ssid'] == selected_ssid:
                    psk = diction['psk']
                    break
        
        mobile_connect(selected_ssid, psk)
    
    def wifi_refresh(self):
        self.ssid_listbox.grid_remove()
        self.ssid_scrollbar.grid_remove()

        self.load_label.grid()

        CONTROLLER.after(LOADING_GIF_FREQUENCY, lambda: self.update_loading_gif(1, self.load_label))

        ssid_list_process = threading.Thread(None, lambda: self.ssid_queue.put(get_all_ssids()))
        ssid_list_process.start()

        CONTROLLER.after(CHECK_FREQUENCY,
                         lambda: self.check_thread(ssid_list_process,
                                                   lambda: self.update_ssids(self.load_label)))
    
    def back(self):
        CONTROLLER.show_page('mainMenu')
    
    def update_ssids(self, label):
        try:
            ssids, self.current_network = self.ssid_queue.get(block=False)
            print(ssids)
        except queue.Empty:
            print("ERROR GETTING AVAILABLE NETWORKS")
            ssids = ["Could not acquire network information, please refresh"]

        label.grid_remove()

        self.ssid_listbox.delete(0, tk.END)

        for ssid in ssids:
            if ssid == self.current_network:
                ssid += " - Connected"
            self.ssid_listbox.insert(tk.END, ssid)

        self.ssid_scrollbar.grid()
        self.ssid_listbox.grid()

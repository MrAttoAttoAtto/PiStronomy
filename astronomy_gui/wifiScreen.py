import queue
import threading
import tkinter as tk

from astronomy_gui.controller import CONTROLLER
from astronomy_gui.images import get_imagepath
from astronomy_gui.page import Page
from tools import get_all_ssids

# ms before gif update
LOADING_GIF_FREQUENCY = 30

# ms before thread re-check
CHECK_FREQUENCY = 200

#locked screen class
class WifiScreen(Page):
    def __init__(self, parent):
        #setup things
        super().__init__(parent)

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
        self.load_label.grid(row=1, column=0, columnspan=5, rowspan=3)

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

        ssid_list_process = threading.Thread(None, lambda: self.ssid_queue.put(get_all_ssids()))
        ssid_list_process.start()

        CONTROLLER.after(CHECK_FREQUENCY,
                         lambda: self.check_thread(ssid_list_process,
                                                   lambda: self.display_ssids(self.load_label)))

    def update_loading_gif(self, index, label):
        ''' update gif things '''

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
            ssids = self.ssid_queue.get(block=False)
            print(ssids)
        except queue.Empty:
            print("ERROR GETTING AVAILABLE NETWORKS")
            ssids = ["Could not acquire network information, please refresh"]

        label.grid_forget()

        self.ssid_scrollbar = tk.Scrollbar(self)
        self.ssid_scrollbar.grid(row=1, column=4, rowspan=3, sticky=tk.W+tk.N+tk.S)

        self.ssid_listbox = tk.Listbox(self, yscrollcommand=self.ssid_scrollbar.set, font=("Helvetica", 20))

        for ssid in ssids:
            self.ssid_listbox.insert(tk.END, ssid)
        self.ssid_listbox.grid(row=1, column=0, rowspan=3, columnspan=4, sticky=tk.N+tk.S+tk.E+tk.W)

        self.ssid_scrollbar.config(command=self.ssid_listbox.yview)

        print(self.all_children(CONTROLLER))
    
    def wifi_connect(self):
        pass
    
    def wifi_refresh(self):
        self.ssid_listbox.grid_forget()
        self.ssid_scrollbar.grid_forget()

        self.load_label.grid(row=1, column=0, columnspan=5, rowspan=3)

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
            ssids = self.ssid_queue.get(block=False)
            print(ssids)
        except queue.Empty:
            print("ERROR GETTING AVAILABLE NETWORKS")
            ssids = ["Could not acquire network information, please refresh"]

        label.grid_forget()

        self.ssid_listbox.delete(0, tk.END)

        for ssid in ssids:
            self.ssid_listbox.insert(tk.END, ssid)

        self.ssid_scrollbar.grid(row=1, column=4, rowspan=3, sticky=tk.W+tk.N+tk.S)

        self.ssid_listbox.grid(row=1, column=0, rowspan=3, columnspan=4, sticky=tk.N+tk.S+tk.E+tk.W)

        print(self.all_children(CONTROLLER))

    @staticmethod
    def all_children(wid):
        _list = wid.winfo_children()

        for item in _list :
            if item.winfo_children():
                _list.extend(item.winfo_children())

        return _list

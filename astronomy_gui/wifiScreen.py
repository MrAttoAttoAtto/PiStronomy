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
        load_label = tk.Label(self, image=load_image)
        load_label.image = load_image
        load_label.grid(row=1, column=0, columnspan=5, rowspan=3)

        #submit button things
        submit_button = tk.Button(self, text="Connect", command=lambda: print("noot"), font=("Helvetica", 20), fg='green')
        #submit_button.image = lockedButton
        submit_button.grid(row=4, column=2, pady=16)

        CONTROLLER.after(LOADING_GIF_FREQUENCY, lambda: self.update_loading_gif(1, load_label))

        self.ssid_queue = queue.Queue(1)

        ssid_list_process = threading.Thread(None, lambda: self.ssid_queue.put(get_all_ssids()))
        ssid_list_process.start()

        CONTROLLER.after(CHECK_FREQUENCY,
                         lambda: self.check_thread(ssid_list_process,
                                                   lambda: self.display_ssids(load_label)))

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
            ssids = []

        label.grid_forget()

        ssid_scrollbar = tk.Scrollbar(self)
        ssid_scrollbar.grid(row=1, column=4, rowspan=3, sticky=tk.W+tk.N+tk.S)

        ssid_listbox = tk.Listbox(self, yscrollcommand=ssid_scrollbar.set, font=("Helvetica", 20))

        for ssid in ssids:
            ssid_listbox.insert(tk.END, ssid)
        ssid_listbox.grid(row=1, column=0, rowspan=3, columnspan=4, sticky=tk.N+tk.S+tk.E+tk.W)

        ssid_scrollbar.config(command=ssid_listbox.yview)

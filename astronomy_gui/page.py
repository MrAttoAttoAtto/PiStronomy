import time
import tkinter as tk

from astronomy_gui.controller import CONTROLLER
from astronomy_gui.images import get_imagepath
from tools import get_current_ssid, get_ip


class Page(tk.Frame):
    # ms before gif update
    LOADING_GIF_FREQUENCY = 30

    # ms before thread re-check
    CHECK_FREQUENCY = 200

    # seconds before being able to kill loading gifs
    LOADING_GIF_KILL = 1

    def __init__(self, parent):
        super().__init__(master=parent)

        self.loading_gif_path = get_imagepath("loadingIcon")

    def render(self, data=False):
        '''Receives render data through kwargs, and has to change values.'''
        pass
    
    def update_loading_gif(self, index, label, start_time):
        ''' update gif things '''
        if not label.winfo_ismapped() and time.time() - start_time > self.LOADING_GIF_KILL:
            return

        try:
            loading_image = tk.PhotoImage(file=self.loading_gif_path,
                                          format="gif -index {}".format(index))
        except tk.TclError:
            loading_image = tk.PhotoImage(file=self.loading_gif_path, format="gif -index 0")
            index = 0

        label.configure(image=loading_image)
        label.image = loading_image

        CONTROLLER.after(self.LOADING_GIF_FREQUENCY, lambda: self.update_loading_gif(index+1, label, start_time))
    
    def check_thread(self, thread, callback):
        if thread.is_alive():
            CONTROLLER.after(self.CHECK_FREQUENCY, lambda: self.check_thread(thread, callback))
        else:
            callback()
    
    def display_current_ip(self):
        curr_ip = get_ip()

        info_string = "The current internal IP address is \"{}\""

        self.display_info(info_string.format(curr_ip), "Current IP")
    
    def display_current_ssid(self):
        curr_ssid = get_current_ssid()
        
        if curr_ssid != "NOT CONNECTED":
            info_string = "This device is currently connected to \"{}\""
            self.display_info(info_string.format(curr_ssid), "Current SSID")
        else:
            info_string = "This device is currently not connected to any network"
            self.display_warning(info_string, "Error: Not connected")

    def display_info(self, info, title):
        tk.messagebox.showinfo(title, message=info)
    
    def display_warning(self, info, title):
        tk.messagebox.showwarning(title, message=info)
    
    def display_error(self, info, title):
        tk.messagebox.showerror(title, message=info)

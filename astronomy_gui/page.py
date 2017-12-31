import tkinter as tk
from astronomy_gui.images import get_imagepath
from astronomy_gui.controller import CONTROLLER


class Page(tk.Frame):
    # ms before gif update
    LOADING_GIF_FREQUENCY = 30

    # ms before thread re-check
    CHECK_FREQUENCY = 200

    def __init__(self, parent):
        super().__init__(master=parent)

        self.loading_gif_path = get_imagepath("loadingIcon")

    def render(self, data=False):
        '''Receives render data through kwargs, and has to change values.'''
        pass
    
    def update_loading_gif(self, index, label, ignore_placement=False):
        ''' update gif things '''
        if not label.winfo_ismapped() and not ignore_placement:
            return

        try:
            loading_image = tk.PhotoImage(file=self.loading_gif_path,
                                          format="gif -index {}".format(index))
        except tk.TclError:
            loading_image = tk.PhotoImage(file=self.loading_gif_path, format="gif -index 0")
            index = 0

        label.configure(image=loading_image)
        label.image = loading_image

        CONTROLLER.after(self.LOADING_GIF_FREQUENCY, lambda: self.update_loading_gif(index+1, label))
    
    def check_thread(self, thread, callback):
        if thread.is_alive():
            CONTROLLER.after(self.CHECK_FREQUENCY, lambda: self.check_thread(thread, callback))
        else:
            callback()
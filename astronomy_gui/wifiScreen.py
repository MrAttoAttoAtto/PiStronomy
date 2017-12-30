import tkinter as tk

from astronomy_gui.images import get_imagepath
from astronomy_gui.page import Page
from astronomy_gui.controller import CONTROLLER

# ms before gif update
LOADING_GIF_FREQUENCY = 30

#locked screen class
class WifiScreen(Page):
    def __init__(self, parent):
        #setup things
        super().__init__(parent)

        self.loading_gif_path = get_imagepath("loadingIcon")
        print(self.loading_gif_path)

        #lockedButton = tk.PhotoImage(file=get_imagepath("unlockTest"))
        load_image = tk.PhotoImage(file=self.loading_gif_path, format='gif -index 0')

        self.width = 800
        self.height = 480
        self.grid()

        #background things
        load_label = tk.Label(self, image=load_image)
        #load_label = tk.Label(self, text="jjj")
        load_label.image = load_image
        load_label.pack()

        #submit button things
        #submit_button = tk.Button(self, image=lockedButton, command=lambda: print("noot"),
        #                          bg="black", activebackground="black", bd=0, highlightthickness=0)
        #submit_button.image = lockedButton
        #submit_button.grid(row=1, column=1, padx=326, pady=151)

        CONTROLLER.after(LOADING_GIF_FREQUENCY, lambda: self.update_loading_gif(1, load_label))

    def update_loading_gif(self, index, label):
        ''' update gif things '''
        try:
            loading_image = tk.PhotoImage(file=self.loading_gif_path, format="gif -index {}".format(index))
        except tk.TclError:
            loading_image = tk.PhotoImage(file=self.loading_gif_path, format="gif -index 0")
            index = 0

        label.configure(image=loading_image)
        label.image = loading_image

        CONTROLLER.after(LOADING_GIF_FREQUENCY, lambda: self.update_loading_gif(index+1, label))

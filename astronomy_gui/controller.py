'''The gui controller'''
import os
import tkinter as tk
import tkinter.font

class Controller(tk.Tk):
    def __init__(self, fullscreen=False, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.title_font = tkinter.font.Font(
            family='Helvetica', size=18, weight="bold", slant="italic")

        self.resizable(width=False, height=False)
        self.configure(background='white')

        if fullscreen:
            w, h = self.winfo_screenwidth(), self.winfo_screenheight()
            self.overrideredirect(1)
            self.geometry("{}x{}+0+0".format(w, h))
        else:
            self.geometry('{}x{}'.format(800, 480))

        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        self.container = tk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.bind("<Escape>", lambda e: self.destroy())
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.pages = {}

    def show_page(self, name, data=False):
        self.pages[name].render(data)
        self.pages[name].tkraise()

    def add_page(self, page):
        self.pages[page.__name__] = page(parent=self.container)
        self.pages[page.__name__].grid(row=0, column=0, sticky="nsew")

if os.name == "nt":
    CONTROLLER = Controller(False)
else:
    CONTROLLER = Controller(True)
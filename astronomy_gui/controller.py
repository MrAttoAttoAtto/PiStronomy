'''The gui controller'''
import tkinter as tk
import tkinter.font

class Controller(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.title_font = tkinter.font.Font(
            family='Helvetica', size=18, weight="bold", slant="italic")

        self.resizable(width=False, height=False)
        self.geometry('{}x{}'.format(800, 480))
        self.configure(background='white')

        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        self.container = tk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.pages = {}

    def show_page(self, name, data=False):
        self.pages[name].render(data)
        self.pages[name].tkraise()

    def add_page(self, page):
        self.pages[page.__name__] = page(parent=self.container)
        self.pages[page.__name__].grid(row=0, column=0, sticky="nsew")

CONTROLLER = Controller() # PLS IMPORT ME FOR LOLS

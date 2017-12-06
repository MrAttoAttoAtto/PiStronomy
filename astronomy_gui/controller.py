'''The gui controller'''
import tkinter as tk
import tkinter.font

class Controller(tk.Tk):
    padding=3
    dimensions="{0}x{1}+0+0"
    def __init__(self, fullscreen=False, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.title_font = tk.font.Font(
            family='Helvetica', size=18, weight="bold", slant="italic")

        self.resizable(width=False, height=False)
        self.geometry('{}x{}'.format(800, 480))
        self.configure(background='white')
        if fullscreen:
            self.wm_attributes('-fullscreen','true')
            width=self.winfo_screenwidth()-self.padding
            height=self.winfo_screenheight()-self.padding
            self.geometry(self.dimensions.format(width, height))
        else:
            self.geometry('{}x{}'.format(800, 460))
        

        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        self.container = tk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.bind("a", lambda e: self.show_page("AdminScreen")) # TODO create admin screen
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.pages = {}

    def show_page(self, name, data=False):
        self.pages[name].render(data)
        self.pages[name].tkraise()

    def add_page(self, page):
        self.pages[page.__name__] = page(parent=self.container)
        self.pages[page.__name__].grid(row=0, column=0, sticky="nsew")

CONTROLLER = Controller(False) # PLS IMPORT ME FOR LOLS

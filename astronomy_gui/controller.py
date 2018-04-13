'''The gui controller'''
import platform
import tkinter as tk
import tkinter.font

from tools import delete_prior_connection

LINUX = platform.system() == "Linux"
if LINUX:
    import RPi.GPIO as GPIO

class Controller(tk.Tk):
    """
    Class for a Tk instance which controls its own Page instances
    """
    def __init__(self, fullscreen=False, *args, **kwargs):
        """
        Primary setup for the tkinter window
        """
        tk.Tk.__init__(self, *args, **kwargs)

        self.title("PiStronomy")
        self.title_font = tkinter.font.Font(
            family='Helvetica', size=18, weight="bold", slant="italic")

        self.resizable(width=False, height=False)
        self.configure(background='white')

        if fullscreen:
            w, h = self.winfo_screenwidth(), self.winfo_screenheight()-45
            self.attributes('-fullscreen', True)
            self.geometry("{}x{}+0+0".format(w, h))
        else:
            self.geometry('{}x{}'.format(800, 480))

        self.focus_set()

        self.bind("<Escape>", lambda e: self.destroy())

        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        self.container = tk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.current_page = ""

        self.pages = {}

    def show_page(self, name, data=False):
        """
        Shows a page based on name
        """
        self.pages[name].render(data)
        self.pages[name].tkraise()

        self.current_page = name

    def add_page(self, page):
        """
        Adds a page by supplying a page object
        """
        self.pages[page.__name__] = page(parent=self.container)
        self.pages[page.__name__].grid(row=0, column=0, sticky="nsew")
    
    def destroy(self):
        """
        Runs on exit, kills the screen and deletes the connection to the current network from
        wpa_supplicant.conf
        """
        super().destroy()
        delete_prior_connection()
        if LINUX:
            GPIO.cleanup()

# Fullscreen only if on the Pi
if not LINUX:
    CONTROLLER = Controller(False)
else:
    CONTROLLER = Controller(True)

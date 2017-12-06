import tkinter as tk


class Page(tk.Frame):
    def __init__(self, parent):
        super().__init__(master=parent)

    def render(self, data=False):
        '''Receives render data through kwargs, and has to change values.'''
        pass
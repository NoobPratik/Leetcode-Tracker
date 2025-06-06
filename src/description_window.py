import customtkinter
from customtkinter import *
from tkhtmlview import HTMLLabel

class DescriptionBox(CTkToplevel):
    def __init__(self, text):
        super().__init__()
        self.title('Description')
        self.geometry("1280x720")
        html = f"<div style='background-color: #242424; color: #e0e0e0; font-family: Arial, sans-serif;'>{text}</div>"
        html_label = HTMLLabel(self, background="#242424", html=html, )
        html_label.pack(fill="both", expand=True, padx=10, pady=10)


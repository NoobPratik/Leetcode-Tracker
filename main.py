import base64
import os.path
import socket
import sqlite3
import tkinter
from customtkinter import *

from src.main_window import TabView

set_appearance_mode('dark')
set_default_color_theme('green')


class App(CTk):
    def __init__(self):
        super().__init__()
        self.connection_ip_and_port = None
        self.title('LeetCode Tracker')
        self.geometry('935x350')
        self.columnconfigure(0, weight=1)
        self.iconbitmap(self.resource_path("logo_sm.ico"))

        self.leet_code_folder = f'{os.getenv("LOCALAPPDATA")}/LeetcodeTracker'
        self.db_file = f"{self.leet_code_folder}\\db.sqlite"
        self.run_checks()

        self.tabview = TabView(self)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="NSEW")

    def resource_path(self, relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("./assets/"), relative_path)

    def execute(self, sql, *args):
        with sqlite3.connect(self.db_file, timeout=100) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute(sql, args)
            conn.commit()

    def fetchone(self, sql, *args):
        with sqlite3.connect(self.db_file, timeout=100) as conn:
            conn.row_factory = sqlite3.Row
            response = conn.execute(sql, args)
            return response.fetchone()

    def fetchall(self, sql, *args):
        with sqlite3.connect(self.db_file, timeout=100) as conn:
            conn.row_factory = sqlite3.Row
            response = conn.execute(sql, args)
            return response.fetchall()

    def run_checks(self):
        if os.path.exists(self.leet_code_folder):
            return

        os.mkdir(self.leet_code_folder)

        host_name = socket.gethostname()

        queries = {
            "create_settings_table": """
                CREATE TABLE "user_settings" (
                    "id"	INTEGER,
                    "ide_path"	TEXT,
                    "leetcode_session"	TEXT,
                    "ide_option"	TEXT,
                    "user_name"	TEXT,
                    "server_ip_address"	TEXT NULL,
                    PRIMARY KEY("id" AUTOINCREMENT)
                )
            """,
            "create_submissions_table": """
                CREATE TABLE IF NOT EXISTS user_submissions (
                    submission_id INTEGER,
                    title TEXT,
                    slug TEXT,
                    memory TEXT,
                    runtime TEXT,
                    status TEXT,
                    language TEXT,
                    timestamp INTEGER,
                    timetaken INTEGER,
                    code TEXT,
                    url TEXT
                );
            """,
            "insert_default_settings": """
                INSERT INTO user_settings (id, ide_path, leetcode_session, ide_option, user_name, server_ip_address)
                VALUES (?, ?, ?, ?, ?, ?);
            """
        }

        self.execute(queries["create_settings_table"])
        self.execute(queries["create_submissions_table"])

        default_settings = (
            1,
            "IDE path here.....",
            "LeetCode Session here.....",
            "vs_code",
            host_name,
            "127.0.0.1"
        )
        self.execute(queries["insert_default_settings"], default_settings)

if __name__ == "__main__":
    app = App()
    # app.resizable(False, False)
    app.mainloop()

import json
import re
import socket
from random import choice
from tkinter import messagebox

import bs4
from customtkinter import *
import requests
from threading import Thread

from CTkToolTip import *
from src.client import Client
from src.settings_window import SettingView
from src.description_window import DescriptionBox
from src.session_window import StartNewSession
from src.submissions_window import Submissions


class TabView(CTkTabview):
    def __init__(self, master, **kwargs):
        super().__init__(master, command=self.on_tab_change, **kwargs)
        self.filtered_question = {"Easy": {}, "Medium": {}, "Hard": {}}
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)  # noqa
        self.regex = r'https:\/\/leetcode\.com\/problems\/([^\/]+).*?'
        self.session = requests.Session()
        self.app = master
        self.client = None
        self.task = None
        self.ide_option = None
        self.all_questions = None
        self.online_button = None
        self.in_session = None
        self.leet_code_session = None
        self.ide_path = None
        self.user_name = None
        self.thread = None
        self.client_socket = None
        self.toplevel_window = None
        self.description = None
        self.discord_forum_id = None
        self.server_ip_address = None

        self.add("Add New")
        self.get_settings()
        self.submission_view = Submissions(self)
        self.add('Settings')
        self.create_buttons()

        SettingView(self)
        Thread(target=self.get_all_problems, daemon=True).start()

    def create_buttons(self):
        self.radio_var = StringVar(value='Easy')
        self.vs_code_value = IntVar(value=1)
        self.discord_value = IntVar(value=1)
        self.chrome_value = IntVar(value=0)

        # LEFT SIDE
        rb_frame = CTkFrame(master=self.tab('Add New'))
        radio_button_1 = CTkRadioButton(master=rb_frame, text='Easy', variable=self.radio_var, value='Easy')
        radio_button_2 = CTkRadioButton(master=rb_frame, text='Medium', variable=self.radio_var, value='Medium')
        radio_button_3 = CTkRadioButton(master=rb_frame, text='Hard', variable=self.radio_var, value='Hard')
        
        self.company_name_label = CTkEntry(rb_frame, placeholder_text="Company Name...")
        CTkToolTip(self.company_name_label, message='Enter the company name for tag-based questions')

        rb_frame.grid(row=0, column=1, padx=(20, 20), pady=(20, 20), sticky="nsew")
        radio_button_1.grid(row=1, column=1, pady=(20, 10), padx=20, sticky="n")
        radio_button_2.grid(row=2, column=1, pady=10, padx=20, sticky="n")
        radio_button_3.grid(row=3, column=1, pady=10, padx=20, sticky="n")
        self.company_name_label.grid(row=4, column=1, pady=10, padx=20, sticky='n')

        # MIDDLE
        label_frame = CTkFrame(master=self.tab('Add New'))
        self.url_label = CTkEntry(label_frame, placeholder_text="LeetCode URL here.....", width=400)
        self.pick_random_button = CTkButton(label_frame, text='Pick Random', command=self.pick_random)
        self.preview_description_button = CTkButton(label_frame, text='Preview Description', state="disabled",
                                                    command=self.open_dialog)
        self.submit_button = CTkButton(label_frame, text='Start New Session', state="disabled",
                                       command=lambda: self.start_new_session(self.url_label.get()))

        self.url_label.bind("<KeyRelease>", self.on_entry_change)
        label_frame.grid(row=0, column=2, padx=(10, 20), pady=(20, 20), sticky="nsew")
        self.url_label.grid(row=0, column=0, padx=(20, 20), pady=(20, 20), sticky="nsew", columnspan=2)
        self.pick_random_button.grid(row=1, column=0, columnspan=1, padx=(20, 20), pady=(20, 20), sticky="nsew")
        self.preview_description_button.grid(row=1, column=1, padx=(20, 20), pady=(20, 20), sticky="nsew")
        self.submit_button.grid(row=2, column=0, columnspan=2, padx=(20, 20), pady=(20, 20), sticky="nsew")

        # RIGHT SIDE
        checkbox_frame = CTkFrame(master=self.tab('Add New'))
        self.vs_code = CTkCheckBox(checkbox_frame, text='File', variable=self.vs_code_value)
        CTkToolTip(self.vs_code, message='This will open your text editor and create a new python file')
        self.chrome = CTkCheckBox(checkbox_frame, text='Chrome', variable=self.chrome_value)
        CTkToolTip(self.chrome, message='This will open the link in your default browser')
        self.discord = CTkCheckBox(checkbox_frame, text='Discord', variable=self.discord_value)
        CTkToolTip(self.discord, message='This will send your submitted code to a discord forum')
        self.online = CTkSwitch(checkbox_frame, text='Online', command=self.start_online)
        CTkToolTip(self.online, message='While this option is toggled, you can receive and send links to your friends')

        checkbox_frame.grid(row=0, column=3, padx=(10, 20), pady=(20, 20), ipadx=10, sticky="nsew")
        self.vs_code.grid(row=0, column=0, pady=(20, 10), padx=20, sticky="n")
        self.discord.grid(row=1, column=0, pady=10, padx=20, sticky="n")
        self.chrome.grid(row=2, column=0, pady=10, padx=20, sticky="n")
        self.online.grid(row=3, column=0, pady=10, padx=20, sticky="n")

    def start_online(self):

        if self.online.get() == 1:
            self.client = Client(self.server_ip_address, self)

            if not self.client.test_connection(self.server_ip_address):
                messagebox.showerror('Connection Refused', message='Could not connect to the server')
                self.online.deselect()
                self.client = None
                return

            self.client.connect()

        else:
            self.client.disconnect()
            self.client = None

    def send_url(self):
        url_dict = {
            "type": "URL",
            "content": self.url_label.get(),
            'difficulty': self.radio_var.get()
        }
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(self.server_ip_address)
        client_socket.send(json.dumps(url_dict).encode('utf-8'))
        client_socket.close()

    def on_closing(self):
        if self.client:
            self.client.disconnect()
            self.client = None
        self.master.destroy()

    def start_new_session(self, url):
        if not self.in_session:
            self.in_session = StartNewSession(url, self)
            if self.in_session.error:
                self.after(50, self.in_session.cancel)
        else:
            messagebox.showwarning('Session In Progress', message='You are already in a session, finish that first')

    def on_entry_change(self, event):  # noqa
        if re.match(self.regex, self.url_label.get()):
            self.submit_button.configure(state='normal')
            self.preview_description_button.configure(state='normal')
            if self.client:
                self.send_url()
        else:
            self.submit_button.configure(state='disabled')
            self.preview_description_button.configure(state='disabled')
        self.description = None

    def on_tab_change(self):
        tab = self.get()
        if tab == 'Submissions':
            self.master.geometry('1300x750')
        if tab == 'Add New':
            self.master.geometry('935x350')
        if tab == 'Session':
            self.master.geometry('400x330')
        if tab == 'Settings':
            self.master.geometry('950x450')

    def pick_random(self):
        if company := self.company_name_label.get():
            random_slug_list = [key for key, value in self.filtered_question[self.radio_var.get()].items() if
                                company in value]
        else:
            random_slug_list = list(self.filtered_question[self.radio_var.get()].keys())

        random_slug = None
        if random_slug_list:
            random_slug = choice(random_slug_list)

        url = f"https://leetcode.com/problems/{random_slug}" if random_slug else "No question found with that company name"
        self.url_label.delete(0, "end")
        self.url_label.insert('0', url)
        self.on_entry_change(None)

    def open_dialog(self):
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            if not self.description:
                self.description = self.get_description(self.url_label.get())
            self.toplevel_window = DescriptionBox(self.description)
            self.toplevel_window.focus_force()
        else:
            self.toplevel_window.focus_force()

    def get_description(self, url):
        self.base_url = 'https://leetcode.com/graphql'
        query = """
            query questionDetail($titleSlug: String!) {
            question(titleSlug: $titleSlug) {
                content
                translatedContent
            }
        }
        """

        json_data = {
                'query': query,
                'variables': {
                    'titleSlug': url.split('/')[-1],
                },
                'operationName': 'questionDetail',
            }

        response = requests.post(self.base_url, json=json_data, stream=True, verify=False)
        return response.json()['data']['question']['content']

    def get_all_problems(self):
        data = self.session.get('https://leetcode.com/api/problems/all/').json()
        self.all_questions = data['stat_status_pairs']
        self.sort_filtered_list()

    @staticmethod
    def load_company_data():
        try:
            company_data = requests.get(
                'https://raw.githubusercontent.com/ssavi-ict/LeetCode-Which-Company/main/data/company_info.json',
                timeout=5).json()
        except (requests.ConnectionError, requests.ConnectTimeout, requests.ReadTimeout):
            messagebox.showerror('Github error',
                                 'Could not retrieve company data from github, maybe rate limit or dns issue')
            return {}
        return {slug: [c.lower() for c in company[1:]] if company else [] for slug, company in company_data.items()}

    def sort_filtered_list(self):
        company_data = self.load_company_data()
        easy_questions = self.filtered_question['Easy']
        medium_questions = self.filtered_question['Medium']
        hard_questions = self.filtered_question['Hard']
        user_submissions = self.app.fetchall('SELECT slug FROM user_submissions')
        title_slugs = [row["slug"] for row in user_submissions]

        for problem in self.all_questions:
            difficulty_level = problem['difficulty']['level']
            slug = problem['stat']['question__title_slug']
            companies = company_data.get(f'https://leetcode.com/problems/{slug}/')
            is_paid = problem['paid_only']

            if slug in title_slugs:
                continue

            if not is_paid:
                if difficulty_level == 1:
                    easy_questions[slug] = companies if companies else []
                elif difficulty_level == 2:
                    medium_questions[slug] = companies if companies else []
                elif difficulty_level == 3:
                    hard_questions[slug] = companies if companies else []

    def get_settings(self):
        options = self.app.fetchone('SELECT * FROM user_settings')
        self.ide_option = options['ide_option']
        self.ide_path = options['ide_path']
        self.leet_code_session = options['leetcode_session']
        self.user_name = options['user_name']
        self.discord_forum_id = options['discord_forum_id']
        self.server_ip_address = (options['server_ip_address'].split(':')[0],
                                  int(options['server_ip_address'].split(':')[1]))

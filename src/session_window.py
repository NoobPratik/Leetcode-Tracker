import json
import os.path
import re
import shutil
import socket
import subprocess
import webbrowser
from tkinter import messagebox

import requests
from customtkinter import *


class StartNewSession:
    def __init__(self, url, tabview):
        self.time_label = None
        self.time_str = None
        self.error = None
        self.tabview = tabview
        tabview.add('Session')
        tabview.set('Session')
        tabview.on_tab_change()

        if not tabview.description:
            tabview.description = tabview.get_description(url)

        self.create_buttons()
        self.url = url

        if tabview.chrome_value.get() == 1:
            self.open_in_chrome()

        if tabview.vs_code_value.get() == 1:
            self.open_vs_and_make_files(url)

        self.elapsed_time = 0
        self.running = True
        self.update_time()

    def update_time(self):
        if self.running:
            self.update_label()
            self.tabview.master.after(1000, self.update_time)
        else:
            return

    def update_label(self):
        self.elapsed_time += 1
        hours, remainder = divmod(self.elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0:
            self.time_str = f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            self.time_str = f"{minutes:02d}:{seconds:02d}"

        self.time_label.configure(text=self.time_str)

    def cancel(self):
        self.tabview.delete('Session')
        self.tabview.set('Add New')
        self.tabview.on_tab_change()
        self.tabview.in_session = None
        self.running = False

    def send_code(self, url_slug):
        r = requests.get('https://leetcode.com/api/submissions/?limit=1',
                         cookies={"LEETCODE_SESSION": self.tabview.leet_code_session})

        latest_submission = r.json()['submissions_dump'][0]
        if latest_submission['title_slug'] == url_slug and latest_submission['status'] == 10:
            url_dict = {
                "type": "DISCORD_FORUM",
                "title": latest_submission["title"],
                "code": latest_submission["code"],
                "runtime": latest_submission["runtime"],
                "memory": latest_submission["memory"],
                "time_taken": self.time_str,
                "url_slug": url_slug,
                "user": self.tabview.user_name,
            }
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.connect(self.tabview.server_ip_address)
                sock.send(json.dumps(url_dict).encode('utf-8'))
            except (ConnectionRefusedError, TimeoutError):
                return

    def complete(self):
        self.cancel()
        url_slug = self.url.split('problems/')[-1].split('/')[0]
        self.tabview.submission_view.get_submissions()
        messagebox.showinfo('Problem completed', 'Problem completed and added in submissions')

        if self.tabview.discord_value.get() == 1:
            self.send_code(url_slug)

        self.tabview.set('Submissions')
        self.tabview.on_tab_change()
        self.tabview.submission_view.filter_rows(1)

    def create_buttons(self):
        frame = CTkFrame(self.tabview.tab('Session'))
        frame.grid(row=0, column=0, padx=10, pady=10, sticky='n')

        self.time_label = CTkLabel(frame, text="0:00:00", font=("Helvetica", 48))
        self.time_label.grid(row=0, column=0, pady=(50, 20), columnspan=2)

        description_button = CTkButton(frame, text="Description", command=self.tabview.open_dialog)
        description_button.grid(row=1, column=0, padx=10, pady=10, sticky='n')

        cancel_button = CTkButton(frame, text="Cancel", command=self.cancel)
        cancel_button.grid(row=1, column=1, padx=10, pady=10, sticky='n')

        complete_button = CTkButton(frame, text="Complete", command=self.complete)
        complete_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')

    def open_vs_and_make_files(self, url):
        folders = ['Easy', 'Medium', 'Hard']
        target_folder = self.tabview.radio_var.get()
        url_slug = url.split('problems/')[-1].split('/')[0]

        payload = {'operationName': 'questionEditorData', 'variables': {'titleSlug': url_slug},
                   'query': "query questionEditorData($titleSlug: String!) {question(titleSlug: $titleSlug) {questionId questionFrontendId codeSnippets {lang langSlug code}}}"}  # noqa

        response = self.tabview.session.post('https://leetcode.com/graphql', data=json.dumps(payload),
                                             headers={'Content-Type': 'application/json',
                                                      'x-csrftoken': self.tabview.session.cookies.get('csrftoken')})

        file_name = f'{url_slug}.py'
        code = [snipet['code'] for snipet in response.json()['data']['question']['codeSnippets'] if
                snipet['lang'] == 'Python']

        if not code:
            self.tabview.url_label.delete(0, 'end')
            self.tabview.url_label.insert(0, 'Question not in python. Choose another one')
            self.error = True
            return

        for folder in folders:
            if not os.path.exists(folder):
                os.mkdir(folder)

        file_path = os.path.join(target_folder, file_name)

        with open(file_path, 'w') as f:
            f.write(f'"""{url}"""\n\n\n')

            # Code
            f.writelines(code)
            f.write('\n')

            # Run cases
            examples = self.get_examples(self.tabview.description)
            func = re.search(r'def (\w+)\(', ''.join(code)).group(1)
            for idx, (input_var, output) in enumerate(examples):
                if idx == 0:
                    f.write(f'\nprint(Solution().{func}({input_var}))\n'
                            f'# output --> {output}\n')
                else:
                    f.write(f'\n# print(Solution().{func}({input_var}))\n'
                            f'# output --> {output}\n')

        self.open_ide(file_path)

    def open_ide(self, file_path):

        if self.tabview.ide_path in ['', None]:
            messagebox.showwarning('Setting Error', message='Please enter IDE path in settings')
            return

        path = shutil.which('code') if self.tabview.ide_option == 'vs_code' else shutil.which('pycharm')
        if not path:
            path = self.tabview.ide_path

        try:
            subprocess.Popen([path, os.path.abspath(file_path)])
        except FileNotFoundError:
            messagebox.showerror('IDE not found',
                                 message='IDE path not found, try pasting vs code or pycharm path in the settings')

    def open_in_chrome(self):
        webbrowser.open(self.url)

    @staticmethod
    def get_examples(description):
        def extract_example(text):
            input_match = re.search(r'Input:\s*(.*?)\nOutput:', text, re.DOTALL)
            _input = input_match.group(1) if input_match else ""
            output_match = re.search(r'Output:\s*(.*?)\n(?:Explanation:\s*(.*))?', text, re.DOTALL)
            _output = output_match.group(1) if output_match else ""
            return _input.strip(), _output.strip()

        examples = []
        description = description.split("Constraints:")[0]
        for match in re.finditer(r'Example \d:[\s\S]*?(?=(?:\nExample \d:)|\Z)', description):
            examples.append(extract_example(match.group(0)))
        print(examples)
        return examples

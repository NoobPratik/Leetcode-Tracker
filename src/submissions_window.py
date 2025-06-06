import random
import threading
import time
import webbrowser
from time import mktime

import requests
from CTkTable import CTkTable
from customtkinter import *
from tkcalendar import DateEntry
from datetime import datetime
from CTkMessagebox import CTkMessagebox


class Submissions:
    def __init__(self, tabview):
        super().__init__()

        self.offset = 0
        self.code_window = None
        self.pagination_label = None
        self.table = None
        self.middle_frame = None
        self.current_page = None
        self.total_pages = None
        self.toplevel_window = None
        self.synced = None
        self.date_range = None

        self.db = tabview.master
        self.tabview = tabview
        self.tabview.add('Submissions')
        self.tabview.tab('Submissions').columnconfigure(0, weight=1)
        self.status_var = StringVar(value='All status')
        self.language_var = StringVar(value='All languages')

        latest_local = self.db.fetchone('SELECT submission_id FROM user_submissions ORDER BY timestamp DESC LIMIT 1')
        self.latest_local_id = latest_local['submission_id'] if latest_local else None
        self.start_up()

    def get_submissions(self):
        def get_data(_offset):
            _url = f'https://leetcode.com/api/submissions?offset={_offset}'
            cookies = {"LEETCODE_SESSION": self.tabview.leet_code_session}
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/16.16299',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/58.0',
                'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
                'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/16.16299',
                'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/58.0',
            ]
            headers = {
                'User-Agent': random.choice(user_agents),
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            response = requests.get(_url, cookies=cookies, headers=headers)
            if response.status_code == 401:
                self.has_next = False
                self.synced = 'error'
                return None
            return response.json()

        def add_submission(s):
            x = self.db.fetchone('SELECT submission_id FROM user_submissions WHERE submission_id = ?', s['id'])
            print(s)
            if not x:
                _id = s['id']
                title = s['title']
                slug = s['title_slug']
                memory = s['memory']
                runtime = s['runtime']
                status = s['status_display']
                timestamp = s['timestamp']
                code = s['code']
                language = s['lang_name']
                url = f'https://leetcode.com{s["url"]}'
                self.db.execute(
                    'INSERT INTO user_submissions '
                    '(submission_id, title, slug, memory, runtime, status, language, timestamp, timetaken, code, url) '
                    'VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                    _id, title, slug, memory, runtime, status, language, timestamp, None, code, url)

        def get_all_submissions():
            data = get_data(self.offset)
            if not data:
                return
            submissions = data['submissions_dump']
            for _submission in submissions:
                if _submission['id'] == self.latest_local_id:
                    self.synced = 'completed'
                    return
                add_submission(_submission)

            has_next = data['has_next'] if data else False

            if has_next:
                self.offset += 20
                time.sleep(3)
                get_all_submissions()
                return
            self.synced = 'completed'

        get_all_submissions()

    def start_up(self):
        if self.tabview.leet_code_session not in ['LeetCode Session here.....', '']:
            self.temp_label = CTkLabel(self.tabview.tab('Submissions'), text='Retrieving  submissions, please wait',
                                       font=('Comic Sans MS', 15))
            self.temp_label.grid(row=0, column=0, pady=20, padx=20, sticky='NSEW')
            threading.Thread(target=self.get_submissions, daemon=True).start()
            self.check_for_sync()
        else:
            instructions_text = """To view your LeetCode submissions, follow these steps:\n
1. Go to https://leetcode.com/api/submissions/
2. Open the 'Network' tab in your web browser's developer tools.
3. Click on 'submissions/' in the list.
4. Copy everything that comes after 'LEETCODE_SESSION.'
5. Paste it into your LeetCode settings.

Note: After pasting, please restart the app for the changes to take effect."""

            label = CTkLabel(self.tabview.tab('Submissions'), text=instructions_text, padx=10, pady=10,
                             font=("Comic Sans MS", 15),
                             justify='left')
            label.grid(row=0, column=0, padx=10, pady=10, sticky='w')

    def check_for_sync(self):
        if not self.synced:
            self.tabview.after(1000, self.check_for_sync)
            return
        if self.synced == 'error':
            self.temp_label.configure(text='Could not retrieve submissions, try again later')
            return
        if self.synced == 'completed':
            self.temp_label.destroy()
            self.create_widgets()

    def open_top_level(self):
        if not self.toplevel_window or not self.toplevel_window.winfo_exists():
            self.toplevel_window = FilterByDate(self)
        self.toplevel_window.focus_force()

    def create_widgets(self):
        self.create_top_frame()
        self.create_bottom_frame()
        self.filter_rows(page=1)

    def filter_rows(self, page, date_range=None, title=None):
        self.date_range = date_range if date_range else self.date_range

        sql_query = f"SELECT * FROM user_submissions"
        filters = ''
        if self.status_var.get() != "All status":
            filters += f"status = '{self.status_var.get()}' AND "

        if self.language_var.get() != "All languages":
            filters += f"language = '{self.language_var.get()}' AND "

        if self.date_range:
            start_date, end_date = self.date_range
            filters += f"timestamp >= '{start_date}' AND timestamp <= '{end_date}' AND "

        if title:
            filters += f"title LIKE '%{title}%' AND "

        if filters.endswith("AND "):
            filters = filters[:-5]

        if filters:
            sql_query += ' WHERE ' + filters

        sql_query += f" ORDER BY timestamp DESC LIMIT 10 OFFSET {(page - 1) * 10}"
        self.current_page = page
        rows = self.db.fetchall(sql_query)
        count = self.db.fetchone(sql_query.replace('*', 'COUNT(*)').split('LIMIT')[0])
        count = count[0] if count else 0
        self.create_middle_frame(rows, count)
        self.disable_buttons()

    def disable_buttons(self):
        self.next_btn.configure(state='normal')
        self.previous_btn.configure(state='normal')
        if self.current_page >= self.total_pages:
            self.next_btn.configure(state='disabled')
        if self.current_page == 1:
            self.previous_btn.configure(state='disabled')

    def create_top_frame(self):
        top_frame = CTkFrame(self.tabview.tab('Submissions'))
        top_frame.grid(row=0, column=0, padx=20, pady=20, sticky='NSEW')

        status_values = ['All status'] + [x["status"] for x in
                                          self.db.fetchall('SELECT DISTINCT status FROM user_submissions')]
        status_option = CTkOptionMenu(top_frame, values=status_values, command=lambda *args: self.filter_rows(1),
                                      variable=self.status_var)
        status_option.grid(row=0, column=0, padx=20, pady=20, sticky='W')

        filter_by_date_btn = CTkButton(top_frame, command=self.open_top_level, text='Filter By Date')
        filter_by_date_btn.grid(row=0, column=1, padx=20, pady=20, sticky='EW')

        language_values = ['All languages'] + [x["language"] for x in
                                               self.db.fetchall('SELECT DISTINCT language FROM user_submissions')]
        language_option = CTkOptionMenu(top_frame, values=language_values, command=lambda *args: self.filter_rows(1),
                                        variable=self.language_var)
        language_option.grid(row=0, column=2, padx=20, pady=20, sticky='E')
        top_frame.columnconfigure(1, weight=1)

    def create_middle_frame(self, rows, total_rows):
        data = [[row['submission_id'], row['title'], row['status'], row['language'],
                 datetime.fromtimestamp(row["timestamp"]).strftime('%d %b, %y')]
                for row in rows]
        self.total_pages = (total_rows + 10 - 1) // 10

        if self.middle_frame:
            self.table.update_values([['ID', 'Title', 'Status', 'Language', 'Date']] + data)
            if rows:
                self.pagination_label.configure(text=f'Total submissions: {total_rows}\n'
                                                     f'Page: {self.current_page}/{self.total_pages}')
            else:
                self.pagination_label.configure(text='No submissions found with current filters')
            return

        self.middle_frame = CTkFrame(self.tabview.tab('Submissions'))
        self.middle_frame.grid(row=1, column=0, padx=20, pady=(5, 20), columnspan=3, sticky='N')
        self.middle_frame.grid_columnconfigure(0, weight=1)

        self.table = CTkTable(self.middle_frame, row=11, column=5, header_color='green',
                              values=[['ID', 'Title', 'Status', 'Language', 'Date']], command=self.cell_command,
                              font=('Comic Sans MS', 14), anchor='w')

        self.table.grid(row=0, column=0, padx=20, pady=(20, 5))
        self.table.update_values([['ID', 'Title', 'Status', 'Language', 'Date']] + data)

        self.table.edit_column(0, hover=True)
        self.table.edit_column(1, hover=True)

        self.pagination_label = CTkLabel(self.middle_frame, text=f'Total submissions: {total_rows}\n'
                                                                 f'Page: {self.current_page}/{self.total_pages}',
                                         font=('Comic Sans MS', 20))

        self.pagination_label.grid(row=12, column=0, padx=20, pady=(5, 20), sticky='NSEW')

    def cell_command(self, cell):
        if cell['column'] == 0 and cell['row'] != 0:

            msg = CTkMessagebox(title='Open Link',
                                message=f'Do you want to open link?\n'
                                        f'https://leetcode.com/submissions/detail/{cell["value"]}/',
                                option_1="No", option_2="Yes", width=650)
            if msg.get() == 'Yes':
                webbrowser.open(f'https://leetcode.com/submissions/detail/{cell["value"]}/')

        elif cell['column'] == 1 and cell['row'] != 0:
            if not self.code_window or not self.code_window.winfo_exists():
                code = self.db.fetchone('SELECT code FROM user_submissions WHERE submission_id = ?',
                                        self.table.get(row=cell['row'], column=cell['column'] - 1))
                self.code_window = CodeSnippet(code['code'])
            self.code_window.focus_force()

    def create_bottom_frame(self):
        bottom_frame = CTkFrame(self.tabview.tab('Submissions'))
        bottom_frame.grid(row=2, column=0, padx=20, pady=(5, 20), sticky='NSEW')
        bottom_frame.columnconfigure(1, weight=1)

        self.previous_btn = CTkButton(bottom_frame, text='Previous', command=self.previous_page, state='disabled')
        self.search_entry = CTkEntry(bottom_frame, placeholder_text='Search by title')
        self.next_btn = CTkButton(bottom_frame, text='Next', command=self.next_page)
        self.search_entry.bind('<Return>', lambda *args: self.filter_rows(1, title=self.search_entry.get()))

        self.previous_btn.grid(row=0, column=0, padx=20, pady=20, sticky='W')
        self.search_entry.grid(row=0, column=1, padx=20, pady=20, sticky='EW')
        self.next_btn.grid(row=0, column=2, padx=20, pady=20, sticky='E')

    def next_page(self):
        self.current_page += 1
        self.filter_rows(self.current_page, title=self.search_entry.get())

    def previous_page(self):
        self.current_page -= 1
        self.filter_rows(self.current_page, title=self.search_entry.get())


class FilterByDate(CTkToplevel):
    def __init__(self, submission_obj):
        super().__init__()
        self.title('Filter By Date')
        self.grab_set()
        self.submission_obj = submission_obj
        frame = CTkFrame(self)
        frame.grid(padx=20, pady=20)

        label = CTkLabel(frame, text='Select a date range to pick submissions', font=('Comic Sans MS', 28))
        label.grid(row=0, column=0, padx=10, pady=10, sticky='N', columnspan=3)

        label_from = CTkLabel(frame, text='From:', font=('Comic Sans MS', 14))
        self.date_entry_1 = DateEntry(frame, selectmode='day', date_pattern='dd/mm/yyyy')
        label_from.grid(row=1, column=0, padx=10, pady=10)
        self.date_entry_1.grid(row=1, column=1, padx=10, pady=10, columnspan=2, sticky='W')

        label_to = CTkLabel(frame, text='To:', font=('Comic Sans MS', 14))
        self.date_entry_2 = DateEntry(frame, selectmode='day', date_pattern='dd/mm/yyyy', maxdate=datetime.today())
        label_to.grid(row=2, column=0, padx=10, pady=10)
        self.date_entry_2.grid(row=2, column=1, padx=10, pady=10, columnspan=2, sticky='W')

        self.date_entry_1.bind("<<DateEntrySelected>>",
                               lambda *args: self.date_entry_2.config(mindate=self.date_entry_1.get_date()))
        self.date_entry_2.bind("<<DateEntrySelected>>",
                               lambda *args: self.date_entry_1.config(maxdate=self.date_entry_2.get_date()))

        button1 = CTkButton(frame, text='Clear filters', command=self.clear_filters)
        button2 = CTkButton(frame, text='Filter', command=self._filter)
        button3 = CTkButton(frame, text='Cancel', command=lambda *args: self.destroy())
        button1.grid(row=3, column=0, padx=10, pady=10)
        button2.grid(row=3, column=1, padx=10, pady=10)
        button3.grid(row=3, column=2, padx=10, pady=10)

    def _filter(self):
        d1 = mktime(self.date_entry_1.get_date().timetuple())
        d2 = mktime(self.date_entry_2.get_date().timetuple())
        self.submission_obj.filter_rows(1, (d1, d2))
        self.destroy()

    def clear_filters(self):
        self.submission_obj.date_range = None
        self.submission_obj.filter_rows(1)
        self.destroy()


class CodeSnippet(CTkToplevel):
    def __init__(self, code):
        super().__init__()
        self.grab_set()
        textbox = CTkTextbox(self, width=500, height=500)
        textbox.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        textbox.insert('1.0', code)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

from tkinter import messagebox
from customtkinter import *

class SettingView:
    def __init__(self, tabview):
        self.tabview = tabview

        frame = CTkFrame(tabview.tab('Settings'))
        frame.grid(row=0, column=0, padx=(20, 20), pady=(20, 20), sticky="n")

        ide_path = StringVar(value=tabview.ide_path)
        session_var = StringVar(value=tabview.leet_code_session)
        username_var = StringVar(value=tabview.user_name)
        server_ip_var = StringVar(value=tabview.server_ip_address)
        self.ide_option = StringVar(value=tabview.ide_option)

        self.ide_path_label = CTkLabel(frame, text='IDE path: ')
        self.ide_path_entry = CTkEntry(
            frame,
            placeholder_text=ide_path.get() if ide_path.get() == "IDE path here....." else "",
            textvariable=ide_path if ide_path.get() != "IDE path here....." else None,
            width=600
        )

        self.leetcode_session_label = CTkLabel(frame, text='Leet Code Session: ')
        self.leetcode_session_entry = CTkEntry(
            frame,
            placeholder_text=session_var.get() if session_var.get() == "LeetCode Session here....." else "",
            textvariable=session_var if session_var.get() != "LeetCode Session here....." else None,
            width=650
        )

        self.user_name_label = CTkLabel(frame, text='Username: ')
        self.user_name_entry = CTkEntry(frame, textvariable=username_var)

        self.server_ip_label = CTkLabel(frame, text='Server IP Address: ')
        self.server_ip_entry = CTkEntry(frame, textvariable=server_ip_var)

        radio_button_1 = CTkRadioButton(master=frame, text='PyCharm', variable=self.ide_option, value='pycharm')
        radio_button_2 = CTkRadioButton(master=frame, text='Visual Studio Code', variable=self.ide_option, value='vs_code')

        self.apply_button = CTkButton(frame, text='Apply', command=self.apply)

        self.ide_path_label.grid(row=0, column=0, padx=(20, 20), pady=(20, 20), sticky="nsew")
        self.ide_path_entry.grid(row=0, column=1, padx=(20, 20), pady=(20, 20), sticky="nsew", columnspan=1)
        self.leetcode_session_label.grid(row=1, column=0, padx=(20, 20), pady=(20, 20), sticky="nsew")
        self.leetcode_session_entry.grid(row=1, column=1, padx=(20, 20), pady=(20, 20), sticky="nsew", columnspan=1)

        self.user_name_label.grid(row=2, column=0, sticky="nsew")
        self.user_name_entry.grid(row=3, column=0, padx=(20,20), pady=(0, 20), sticky="nsew")
        self.server_ip_label.grid(row=2, column=1, sticky="nsew")
        self.server_ip_entry.grid(row=3, column=1, padx=(20, 20), pady=(0, 20), sticky="nsew")

        radio_button_1.grid(row=5, column=0, padx=30, pady=10, sticky="w")
        radio_button_2.grid(row=5, column=1, padx=30, pady=10, sticky="w")
        self.apply_button.grid(row=6, column=0, columnspan=2, padx=(20, 20), pady=(20, 20), sticky="s")

        self.server_ip_var = server_ip_var

    def apply(self):
        self.tabview.app.execute(
            '''UPDATE user_settings 
               SET ide_path=?, leetcode_session=?, ide_option=?, user_name=?, server_ip_address=? 
               WHERE id = 1''',
            self.ide_path_entry.get(),
            self.leetcode_session_entry.get(),
            self.ide_option.get(),
            self.user_name_entry.get(),
            self.server_ip_entry.get()
        )
        self.tabview.ide_path = self.ide_path_entry.get()
        self.tabview.leet_code_session = self.leetcode_session_entry.get()
        self.tabview.ide_option = self.ide_option.get()
        self.tabview.user_name = self.user_name_entry.get()
        self.tabview.server_ip_address = self.server_ip_entry.get()

        messagebox.showinfo('Success', 'Settings successfully applied')

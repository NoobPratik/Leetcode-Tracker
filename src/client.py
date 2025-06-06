import asyncio
import json
import socket
import threading
import tkinter as tk


class Client:

    def __init__(self, connection, root):
        self.task = None
        self.host = connection[0]
        self.port = connection[1]
        self.reader = None
        self.writer = None
        self.tabview = root
        self.loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()

    @staticmethod
    def test_connection(connection):
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5)
            client_socket.connect(connection)
            client_socket.close()
            return True
        except (socket.timeout, ConnectionRefusedError):
            return False

    def connect(self):
        self.task = self.loop.create_task(self.listen_messages(self.tabview.url_label, self.tabview.radio_var))
        threading.Thread(target=self.loop.run_forever, daemon=True).start()

    def disconnect(self):
        if self.task:
            self.task.cancel()
            self.task = None
        if self.writer:
            self.writer.close()

    async def listen_messages(self, text_widget, radio_var):
        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            text_widget.delete(0, 'end')
            text_widget.insert(0, "Connected to the server. Listening for messages...\n")

            while True:
                data = await self.reader.read(500)
                if not data:
                    self.tabview.online.deselect()
                    break

                data = data.decode('utf-8')
                text_widget.delete(0, 'end')

                if data == 'Unauthorized Connection':
                    text_widget.insert(0, data)
                    await self.writer.drain()
                    self.tabview.online.deselect()
                    return

                if data == 'quit':
                    text_widget.insert(0, 'Server closed')
                    await self.writer.drain()
                    self.tabview.online.deselect()
                    return

                data = json.loads(data)
                text_widget.insert(0, data['content'])
                radio_var.set(data['difficulty'])

                await self.writer.drain()

        except Exception as e:
            text_widget.insert(tk.END, f"Error: {e}\n")
            self.tabview.online.deselect()

        finally:
            if self.writer:
                self.writer.close()
                await self.writer.wait_closed()

    def send_message(self, message):
        if self.writer:
            self.writer.write(message.encode())

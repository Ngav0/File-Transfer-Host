import socket
import os
import tkinter as tk
from tkinter import ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
import threading
import queue
import time

SERVER_IP = "Other PC's IP Adress Here"
PORT = 5001
SECRET_KEY = "hansriegel8"
BUFFER_SIZE = 4096
MAX_WORKERS = 5


class ClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("File Sender (Client)")

        self.label = tk.Label(root, text="Drag & Drop files here", font=("Arial", 12))
        self.label.pack(pady=10)

        self.drop_area = tk.Label(
            root,
            text="📂 Drop Files",
            relief="ridge",
            width=40,
            height=10
        )
        self.drop_area.pack(pady=10)

        self.progress = ttk.Progressbar(root, length=300)
        self.progress.pack(pady=10)

        self.status = tk.Label(root, text="", font=("Arial", 10))
        self.status.pack()

        self.log = tk.Text(root, height=10, width=50)
        self.log.pack()

        self.queue = queue.Queue()

        self.drop_area.drop_target_register(DND_FILES)
        self.drop_area.dnd_bind("<<Drop>>", self.drop)

        for _ in range(MAX_WORKERS):
            threading.Thread(target=self.worker, daemon=True).start()

    def log_msg(self, msg):
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)

    def drop(self, event):
        files = self.root.tk.splitlist(event.data)
        for file in files:
            if os.path.isfile(file):
                self.queue.put(file)

    def worker(self):
        while True:
            filepath = self.queue.get()
            try:
                self.send_file(filepath)
            finally:
                self.queue.task_done()

    def send_exact(self, sock, data):
        sock.sendall(data)

    def send_file(self, filepath):
        filename = os.path.basename(filepath)
        filesize = os.path.getsize(filepath)

        for attempt in range(3):
            try:
                self.status.config(text=f"Sending: {filename}")
                self.log_msg(f"Connecting ({attempt+1}/3): {filename}")

                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(10)
                    s.connect((SERVER_IP, PORT))

                    # Super duper secure key
                    key_bytes = SECRET_KEY.encode()
                    self.send_exact(s, f"{len(key_bytes):<16}".encode())
                    self.send_exact(s, key_bytes)

                    # Filename
                    filename_bytes = filename.encode()
                    self.send_exact(s, f"{len(filename_bytes):<16}".encode())
                    self.send_exact(s, filename_bytes)

                    # Filesize
                    self.send_exact(s, f"{filesize:<16}".encode())

                    sent = 0
                    with open(filepath, "rb") as f:
                        while True:
                            data = f.read(BUFFER_SIZE)
                            if not data:
                                break
                            self.send_exact(s, data)
                            sent += len(data)

                            progress = int((sent / filesize) * 100)
                            self.progress["value"] = progress
                            self.root.update_idletasks()

                self.log_msg(f"Sent: {filename}")
                self.progress["value"] = 0
                return

            except Exception as e:
                self.log_msg(f"Retry {attempt+1} failed: {filename} ({e})")
                time.sleep(1)

        self.log_msg(f"FAILED: {filename}")
        self.progress["value"] = 0


if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = ClientGUI(root)
    root.mainloop()
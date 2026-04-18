import socket
import threading
import os
import tkinter as tk
from tkinter import ttk
import queue

HOST = "0.0.0.0"
PORT = 5001
SAVE_DIR = "received_files"
SECRET_KEY = "hansriegel8"
ALLOWED_IP = "Put the IP adress of the other PC here" # Extra security, so only files from this PC get accepted.

os.makedirs(SAVE_DIR, exist_ok=True)


class ServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("File Receiver (Server)")

        self.label = tk.Label(root, text="Waiting for files...", font=("Arial", 12))
        self.label.pack(pady=10)

        self.progress = ttk.Progressbar(root, length=300)
        self.progress.pack(pady=10)

        self.log = tk.Text(root, height=12, width=60)
        self.log.pack()

        self.gui_queue = queue.Queue()
        self.root.after(100, self.process_gui_queue)

        threading.Thread(target=self.start_server, daemon=True).start()

    def log_msg(self, msg):
        self.gui_queue.put(("log", msg))

    def set_progress(self, value):
        self.gui_queue.put(("progress", value))

    def process_gui_queue(self):
        while not self.gui_queue.empty():
            action, value = self.gui_queue.get()
            if action == "log":
                self.log.insert(tk.END, value + "\n")
                self.log.see(tk.END)
            elif action == "progress":
                self.progress["value"] = value
        self.root.after(100, self.process_gui_queue)

    def start_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((HOST, PORT))
        server.listen(50)

        self.log_msg(f"Server listening on port {PORT}...")

        while True:
            conn, addr = server.accept()
            client_ip = addr[0]

            if client_ip != ALLOWED_IP:
                self.log_msg(f"Blocked IP: {client_ip}")
                conn.close()
                continue

            self.log_msg(f"Accepted IP: {client_ip}")

            threading.Thread(
                target=self.handle_client,
                args=(conn,),
                daemon=True
            ).start()

    def recv_exact(self, conn, size):
        data = b""
        while len(data) < size:
            packet = conn.recv(size - len(data))
            if not packet:
                return None
            data += packet
        return data

    def handle_client(self, conn):
        try:
            # Secret key
            key_size = int(self.recv_exact(conn, 16).decode().strip())
            received_key = self.recv_exact(conn, key_size).decode()

            if received_key != SECRET_KEY:
                self.log_msg("Invalid secret key")
                return

            # Filename
            filename_size = int(self.recv_exact(conn, 16).decode().strip())
            filename = self.recv_exact(conn, filename_size).decode()

            # Filesize
            filesize = int(self.recv_exact(conn, 16).decode().strip())

            filepath = os.path.join(SAVE_DIR, os.path.basename(filename))

            received = 0
            with open(filepath, "wb") as f:
                while received < filesize:
                    data = conn.recv(min(4096, filesize - received))
                    if not data:
                        break
                    f.write(data)
                    received += len(data)

                    progress = int((received / filesize) * 100)
                    self.set_progress(progress)

            if received == filesize:
                self.log_msg(f"Received: {filename}")
            else:
                self.log_msg(f"Incomplete: {filename}")

            self.set_progress(0)

        except Exception as e:
            self.log_msg(f"Error: {e}")
        finally:
            conn.close()


if __name__ == "__main__":
    root = tk.Tk()
    app = ServerGUI(root)
    root.mainloop()
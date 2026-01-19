import socket
import threading
import queue
import tkinter as tk
from tkinter import messagebox

ENC = "utf-8"

class ChatClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TCP Chat (GUI)")

        self.sock = None
        self.recv_thread = None
        self.incoming = queue.Queue()

        # Top connection frame
        top = tk.Frame(root)
        top.pack(fill="x", padx=10, pady=8)

        tk.Label(top, text="Host:").grid(row=0, column=0, sticky="w")
        self.host_var = tk.StringVar(value="127.0.0.1")  # חשוב: לא 0.0.0.0
        tk.Entry(top, textvariable=self.host_var, width=18).grid(row=0, column=1, padx=5)

        tk.Label(top, text="Port:").grid(row=0, column=2, sticky="w")
        self.port_var = tk.StringVar(value="55555")
        tk.Entry(top, textvariable=self.port_var, width=8).grid(row=0, column=3, padx=5)

        tk.Label(top, text="Nickname:").grid(row=0, column=4, sticky="w")
        self.nick_var = tk.StringVar(value="")
        tk.Entry(top, textvariable=self.nick_var, width=14).grid(row=0, column=5, padx=5)

        self.connect_btn = tk.Button(top, text="Connect", command=self.connect)
        self.connect_btn.grid(row=0, column=6, padx=8)

        # Chat display
        self.text = tk.Text(root, height=18, state="disabled", wrap="word")
        self.text.pack(fill="both", expand=True, padx=10)

        # Bottom send frame
        bottom = tk.Frame(root)
        bottom.pack(fill="x", padx=10, pady=8)

        self.msg_var = tk.StringVar()
        self.entry = tk.Entry(bottom, textvariable=self.msg_var)
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entry.bind("<Return>", lambda e: self.send_message())

        self.send_btn = tk.Button(bottom, text="Send", command=self.send_message, state="disabled")
        self.send_btn.pack(side="left")

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # polling messages
        self.root.after(50, self.poll_incoming)

    def log(self, line: str):
        self.text.configure(state="normal")
        self.text.insert("end", line + "\n")
        self.text.see("end")
        self.text.configure(state="disabled")

    def connect(self):
        host = self.host_var.get().strip()
        try:
            port = int(self.port_var.get().strip())
        except:
            messagebox.showerror("Error", "Port must be a number")
            return

        nick = self.nick_var.get().strip()
        if not nick:
            messagebox.showerror("Error", "Enter a nickname")
            return

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((host, port))
        except Exception as e:
            messagebox.showerror("Error", f"Could not connect:\n{e}")
            self.sock = None
            return

        # send nickname
        try:
            self.sock.sendall(f"NICK|{nick}\n".encode(ENC))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send nickname:\n{e}")
            self.sock.close()
            self.sock = None
            return

        self.connect_btn.config(state="disabled")
        self.send_btn.config(state="normal")
        self.entry.focus_set()
        self.log(f"[SYSTEM] Connected as {nick}")
        self.log("[SYSTEM] Private message format: @nickname your message")

        self.recv_thread = threading.Thread(target=self.recv_loop, daemon=True)
        self.recv_thread.start()

    def recv_loop(self):
        buffer = ""
        try:
            while True:
                data = self.sock.recv(4096)
                if not data:
                    break
                buffer += data.decode(ENC, errors="ignore")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if line:
                        self.incoming.put(line)
        except:
            pass
        finally:
            self.incoming.put("SYS|Disconnected from server")

    def send_message(self):
        if not self.sock:
            return

        text = self.msg_var.get().strip()
        if not text:
            return

        self.msg_var.set("")

        # DM if starts with @nick
        if text.startswith("@") and " " in text:
            to_nick, msg = text[1:].split(" ", 1)
            to_nick = to_nick.strip()
            msg = msg.strip()
            if to_nick and msg:
                payload = f"DM|{to_nick}|{msg}\n"
                try:
                    self.sock.sendall(payload.encode(ENC))
                except:
                    self.log("[SYSTEM] Failed to send message")
        else:
            payload = f"MSG|{text}\n"
            try:
                self.sock.sendall(payload.encode(ENC))
            except:
                self.log("[SYSTEM] Failed to send message")

    def poll_incoming(self):
        while True:
            try:
                line = self.incoming.get_nowait()
            except queue.Empty:
                break

            parts = line.split("|")
            tag = parts[0]

            if tag == "MSG" and len(parts) >= 3:
                from_nick = parts[1]
                msg = "|".join(parts[2:])
                self.log(f"{from_nick}: {msg}")

            elif tag == "DM" and len(parts) >= 3:
                from_nick = parts[1]
                msg = "|".join(parts[2:])
                self.log(f"[DM from {from_nick}] {msg}")

            elif tag == "DM_SENT" and len(parts) >= 3:
                to_nick = parts[1]
                msg = "|".join(parts[2:])
                self.log(f"[DM to {to_nick}] {msg}")

            elif tag == "SYS" and len(parts) >= 2:
                msg = "|".join(parts[1:])
                self.log(f"[SYSTEM] {msg}")

            elif tag == "ERR":
                msg = "|".join(parts[1:]) if len(parts) > 1 else "Error"
                self.log(f"[ERROR] {msg}")

            elif tag == "OK":
                # Optional: ignore
                pass
            else:
                self.log(f"[RAW] {line}")

        self.root.after(50, self.poll_incoming)

    def on_close(self):
        try:
            if self.sock:
                self.sock.close()
        except:
            pass
        self.root.destroy()


def main():
    root = tk.Tk()
    app = ChatClientGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()

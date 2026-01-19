import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox

HOST = '127.0.0.1'
PORT = 55555

class ClientGUI:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((HOST, PORT))

        # חלון הודעה לבחירת שם משתמש
        msg = tk.Tk()
        msg.withdraw()
        self.nickname = simpledialog.askstring("Nickname", "Please choose a nickname", parent=msg)
        
        self.gui_done = False
        self.running = True

        # הפעלת התהליכון לניהול הממשק והתקשורת
        gui_thread = threading.Thread(target=self.gui_loop)
        receive_thread = threading.Thread(target=self.receive)
        
        gui_thread.start()
        receive_thread.start()

    def gui_loop(self):
        self.win = tk.Tk()
        self.win.configure(bg="lightgray")
        self.win.title(f"Chat Room - {self.nickname}")

        # כותרת
        self.label = tk.Label(self.win, text=f"Logged in as: {self.nickname}", bg="lightgray")
        self.label.pack(padx=20, pady=5)

        # אזור הצ'אט (טקסט)
        self.text_area = scrolledtext.ScrolledText(self.win)
        self.text_area.pack(padx=20, pady=5)
        self.text_area.config(state='disabled')

        # אזור ההקלדה
        self.msg_label = tk.Label(self.win, text="Message:", bg="lightgray")
        self.msg_label.pack(padx=20, pady=5)

        self.input_area = tk.Entry(self.win)
        self.input_area.pack(padx=20, pady=5)

        # כפתור שליחה
        self.send_button = tk.Button(self.win, text="Send", command=self.write)
        self.send_button.pack(padx=20, pady=5)

        self.gui_done = True
        
        # טיפול בסגירת החלון
        self.win.protocol("WM_DELETE_WINDOW", self.stop)
        
        self.win.mainloop()

    def write(self):
        # פונקציה לשליחת הודעה
        message = f"{self.nickname}: {self.input_area.get()}"
        self.client.send(message.encode('utf-8'))
        self.input_area.delete(0, 'end')

    def stop(self):
        self.running = False
        self.win.destroy()
        self.client.close()
        exit(0)

    def receive(self):
        while self.running:
            try:
                message = self.client.recv(1024).decode('utf-8')
                if message == 'NICK':
                    self.client.send(self.nickname.encode('utf-8'))
                else:
                    if self.gui_done:
                        self.text_area.config(state='normal')
                        self.text_area.insert('end', message + '\n')
                        self.text_area.yview('end')
                        self.text_area.config(state='disabled')
            except ConnectionAbortedError:
                break
            except:
                print("Error")
                self.client.close()
                break

client = ClientGUI()
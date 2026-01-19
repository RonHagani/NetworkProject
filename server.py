import socket
import threading

# הגדרות חיבור
HOST = '0.0.0.0'
PORT = 55555

# רשימות לניהול לקוחות ושמות
clients = []
nicknames = []

def broadcast(message):
    """שליחת הודעה לכל הלקוחות המחוברים"""
    for client in clients:
        try:
            client.send(message)
        except:
            pass

def handle(client):
    """טיפול בחיבור ספציפי מול לקוח"""
    while True:
        try:
            # קבלת הודעה מהלקוח והפצתה לכולם
            message = client.recv(1024)
            broadcast(message)
        except:
            # במקרה של ניתוק או שגיאה
            if client in clients:
                index = clients.index(client)
                clients.remove(client)
                client.close()
                nickname = nicknames[index]
                broadcast(f'{nickname} left the chat!'.encode('utf-8'))
                nicknames.remove(nickname)
                print(f"[-] {nickname} disconnected.")
                break

def receive():
    """הפונקציה הראשית שמקבלת חיבורים חדשים"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    print(f"[+] Server is running and listening on {HOST}:{PORT}...")

    while True:
        client, address = server.accept()
        print(f"[+] Connected with {str(address)}")

        # בקשת כינוי מהלקוח
        client.send('NICK'.encode('utf-8'))
        nickname = client.recv(1024).decode('utf-8')
        
        nicknames.append(nickname)
        clients.append(client)

        print(f"[+] Nickname of the client is {nickname}")
        broadcast(f'{nickname} joined the chat!'.encode('utf-8'))
        client.send('Connected to server!'.encode('utf-8'))

        # פתיחת תהליכון נפרד לטיפול בלקוח זה
        thread = threading.Thread(target=handle, args=(client,))
        thread.start()

if __name__ == "__main__":
    receive()
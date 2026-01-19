import socket
import threading

HOST = "0.0.0.0"
PORT = 55555
ENC = "utf-8"

clients_lock = threading.Lock()
clients_by_name = {}   # nickname -> socket
names_by_sock = {}     # socket -> nickname


def send_line(sock: socket.socket, text: str):
    try:
        sock.sendall((text + "\n").encode(ENC))
    except:
        pass


def broadcast(from_nick: str, text: str):
    line = f"MSG|{from_nick}|{text}"
    with clients_lock:
        targets = list(clients_by_name.values())
    for s in targets:
        send_line(s, line)


def send_dm(from_nick: str, to_nick: str, text: str):
    with clients_lock:
        target = clients_by_name.get(to_nick)
        sender = clients_by_name.get(from_nick)

    if not target:
        if sender:
            send_line(sender, f"SYS|User '{to_nick}' not found")
        return

    send_line(target, f"DM|{from_nick}|{text}")
    # פידבק לשולח (כדי שיראה שזה נשלח בפרטי)
    if sender:
        send_line(sender, f"DM_SENT|{to_nick}|{text}")


def remove_client(sock: socket.socket):
    with clients_lock:
        nick = names_by_sock.pop(sock, None)
        if nick:
            clients_by_name.pop(nick, None)
    try:
        sock.close()
    except:
        pass
    if nick:
        print(f"[-] {nick} disconnected")
        # הודעת מערכת לכולם
        with clients_lock:
            targets = list(clients_by_name.values())
        for s in targets:
            send_line(s, f"SYS|{nick} left the chat")


def handle_client(sock: socket.socket, addr):
    buffer = ""
    nick = names_by_sock.get(sock, "Unknown")

    try:
        while True:
            data = sock.recv(4096)
            if not data:
                break

            buffer += data.decode(ENC, errors="ignore")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue

                parts = line.split("|")
                cmd = parts[0]

                if cmd == "MSG" and len(parts) >= 2:
                    text = "|".join(parts[1:]).strip()
                    if text:
                        print(f"[MSG] {nick}: {text}")
                        broadcast(nick, text)

                elif cmd == "DM" and len(parts) >= 3:
                    to_nick = parts[1].strip()
                    text = "|".join(parts[2:]).strip()
                    if to_nick and text:
                        print(f"[DM] {nick} -> {to_nick}: {text}")
                        send_dm(nick, to_nick, text)

                else:
                    send_line(sock, "SYS|Bad message format")

    except Exception as e:
        # אפשר להדפיס e לדיבאג אם צריך
        pass
    finally:
        remove_client(sock)


def accept_loop(server_sock: socket.socket):
    print(f"[+] Server listening on {HOST}:{PORT}")
    while True:
        client_sock, addr = server_sock.accept()
        print(f"[+] New connection from {addr}")

        # שלב התחברות: חייב לשלוח NICK|name
        try:
            send_line(client_sock, "SYS|Send nickname as: NICK|your_name")
            first = ""
            while "\n" not in first:
                chunk = client_sock.recv(1024)
                if not chunk:
                    raise RuntimeError("No nickname received")
                first += chunk.decode(ENC, errors="ignore")

            first_line = first.split("\n", 1)[0].strip()
            parts = first_line.split("|", 1)
            if len(parts) != 2 or parts[0] != "NICK":
                send_line(client_sock, "ERR|BAD_NICK_FORMAT")
                client_sock.close()
                continue

            nick = parts[1].strip()
            if not nick:
                send_line(client_sock, "ERR|EMPTY_NICK")
                client_sock.close()
                continue

            with clients_lock:
                if nick in clients_by_name:
                    send_line(client_sock, "ERR|NICK_TAKEN")
                    client_sock.close()
                    continue

                clients_by_name[nick] = client_sock
                names_by_sock[client_sock] = nick

            print(f"[+] Nickname set: {nick}")

            # הודעות מערכת
            send_line(client_sock, "OK|CONNECTED")
            send_line(client_sock, "SYS|Commands: normal text = broadcast, @nick text = private")
            with clients_lock:
                targets = list(clients_by_name.values())
            for s in targets:
                if s is not client_sock:
                    send_line(s, f"SYS|{nick} joined the chat")

            t = threading.Thread(target=handle_client, args=(client_sock, addr), daemon=True)
            t.start()

        except Exception:
            try:
                client_sock.close()
            except:
                pass


def main():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(10)
    accept_loop(server_sock)


if __name__ == "__main__":
    main()

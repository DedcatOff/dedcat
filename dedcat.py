#!/usr/bin/env python3
import os
import sys
import subprocess
import socket
import threading
import time
import platform

# ================== KONFIG ==================

REPO_DIR = "repos"
CURRENT_REPO = None

DISCOVERY_PORT = 45454
TRANSFER_PORT = 45455
BUFFER = 4096

AUTO_REPOS = [
    "https://github.com/htr-tech/zphisher.git",
    "https://github.com/RetroXploit/DDoS-Ripper.git",
]

DEDCAT_GIT = "https://github.com/DedcatOff/dedcat"

# ================== LOGO ==================

LOGO = r"""
            /\           /\
           /  \_________/  \
          |   O         X   |
          |    ___ ___ ___  |
          |   / D \ E \ D \ |
          |  |  E  |  C  | |
          |   \ A /  T  /  |
          |    \___\___/   |
           \               /
            \_____________/

      ██████╗ ███████╗██████╗  ██████╗ █████╗ ████████╗
      ██╔══██╗██╔════╝██╔══██╗██╔════╝██╔══██╗╚══██╔══╝
      ██║  ██║█████╗  ██║  ██║██║     ███████║   ██║
      ██║  ██║██╔══╝  ██║  ██║██║     ██╔══██║   ██║
      ██████╔╝███████╗██████╔╝╚██████╗██║  ██║   ██║
      ╚═════╝ ╚══════╝╚═════╝  ╚═════╝╚═╝  ╚═╝   ╚═╝

                free the world !
"""

# ================== UTIL ==================

def c(t, col): return f"\033[{col}m{t}\033[0m"
def clear(): os.system("clear")
def run(cmd, cwd=None): subprocess.run(cmd, shell=True, cwd=cwd)

# ================== UPDATE ==================

def system_update():
    if "termux" in platform.platform().lower():
        run("pkg update -y && pkg upgrade -y")
    else:
        run("apt update -y && apt upgrade -y")

def dedcat_self_update():
    if os.path.isdir(".git"):
        print(c("[DED CAT] checking updates...", "33"))
        run("git pull")
    else:
        print(c("[DED CAT] not installed via git", "90"))

# ================== UI ==================

def show():
    clear()
    print(c(LOGO, "36"))
    print(c(f"Aktivní repo: {CURRENT_REPO if CURRENT_REPO else 'žádné'}\n", "35"))

def menu():
    print(c("""
[1] Vypsat repozitáře
[2] Přidat repo
[5] Vybrat repo
[8] Shell mód
[9] LAN file transfer
[0] Konec
""", "36"))

# ================== REPOS ==================

def ensure_repos():
    os.makedirs(REPO_DIR, exist_ok=True)

def auto_clone():
    ensure_repos()
    for url in AUTO_REPOS:
        name = url.split("/")[-1].replace(".git", "")
        path = f"{REPO_DIR}/{name}"
        if not os.path.isdir(path):
            run(f"git clone {url}", cwd=REPO_DIR)
        else:
            run("git pull", cwd=path)

def list_repos():
    ensure_repos()
    for r in os.listdir(REPO_DIR):
        print("-", r)

def select_repo():
    global CURRENT_REPO
    list_repos()
    r = input("Repo: ")
    if os.path.isdir(f"{REPO_DIR}/{r}"):
        CURRENT_REPO = r

# ================== SHELL ==================

def shell_mode():
    rc = "/tmp/dedcatrc"
    with open(rc, "w") as f:
        f.write("shelloff(){ exit; }\n")
    subprocess.run(
        ["bash", "--rcfile", rc, "-i"],
        cwd=f"{REPO_DIR}/{CURRENT_REPO}" if CURRENT_REPO else None
    )
    os.remove(rc)

# ================== PROGRESS ==================

def progress(done, total):
    percent = int(done / total * 100)
    mb_d = done / 1024 / 1024
    mb_t = total / 1024 / 1024
    print(f"\r[{percent:3}%] {mb_d:.2f}/{mb_t:.2f} MB", end="", flush=True)

# ================== LAN ==================

def receiver():
    name = input("Session name: ")
    password = input("Password: ")

    def broadcast():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while True:
            s.sendto(f"DEDCAT:{name}".encode(), ('<broadcast>', DISCOVERY_PORT))
            time.sleep(2)

    threading.Thread(target=broadcast, daemon=True).start()

    srv = socket.socket()
    srv.bind(("", TRANSFER_PORT))
    srv.listen(1)

    print(c("[WAITING]", "32"))
    conn, _ = srv.accept()

    if conn.recv(1024).decode() != password:
        conn.close()
        return

    filename = conn.recv(1024).decode()
    size = int(conn.recv(1024).decode())

    received = 0
    with open(filename, "wb") as f:
        while received < size:
            data = conn.recv(BUFFER)
            if not data:
                break
            f.write(data)
            received += len(data)
            progress(received, size)

    print("\n" + c("[RECEIVED]", "32"))
    conn.close()

def sender():
    sessions = {}

    def discover():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("", DISCOVERY_PORT))
        while True:
            d, a = s.recvfrom(1024)
            if d.startswith(b"DEDCAT:"):
                sessions[d.decode().split(":")[1]] = a[0]

    threading.Thread(target=discover, daemon=True).start()
    time.sleep(3)

    for s in sessions:
        print("-", s)

    name = input("connect: ")
    pwd = input("pass: ")
    path = input("upload: ")

    size = os.path.getsize(path)
    ip = sessions.get(name)
    if not ip:
        return

    sock = socket.socket()
    sock.connect((ip, TRANSFER_PORT))
    sock.send(pwd.encode())
    time.sleep(0.2)
    sock.send(os.path.basename(path).encode())
    time.sleep(0.2)
    sock.send(str(size).encode())

    sent = 0
    with open(path, "rb") as f:
        while data := f.read(BUFFER):
            sock.send(data)
            sent += len(data)
            progress(sent, size)

    print("\n" + c("[SENT]", "32"))
    sock.close()

def lan():
    m = input("[1] přijímat | [2] posílat: ")
    receiver() if m == "1" else sender()

# ================== MAIN ==================

def main():
    system_update()
    dedcat_self_update()
    auto_clone()

    while True:
        show()
        menu()
        c = input("dedcat> ")

        if c == "1": list_repos()
        elif c == "2": auto_clone()
        elif c == "5": select_repo()
        elif c == "8": shell_mode()
        elif c == "9": lan()
        elif c == "0": break

if __name__ == "__main__":
    main()

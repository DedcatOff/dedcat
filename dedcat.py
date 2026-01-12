#!/usr/bin/env python3
import os
import sys
import subprocess
import socket
import threading
import time
import hashlib
from pathlib import Path

# ================== KONFIG ==================

REPO_DIR = "repos"
INSTALL_FLAG = ".dedcat_installed"
CURRENT_REPO = None
SHELL_MODE = False

AUTO_REPOS = [
    "https://github.com/htr-tech/zphisher.git",
    "https://github.com/RetroXploit/DDoS-Ripper.git",
]

LAN_PORT = 50505
BUF = 4096

DED_REPO_URL = "https://github.com/DedcatOff/dedcat.git"

# ================== CRYPTO ==================

def ensure_crypto():
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        print("[DED CAT] installing cryptography...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--user", "cryptography"]
        )
    from cryptography.fernet import Fernet
    return Fernet

Fernet = ensure_crypto()

def make_key(password: str):
    digest = hashlib.sha256(password.encode()).digest()
    return Fernet(digest[:32].hex().encode())

# ================== UTIL ==================

def color(t, c):
    return f"\033[{c}m{t}\033[0m"

def clear():
    os.system("clear")

def pause():
    input(color("\n[ENTER] pokračuj...", "90"))

def run(cmd, cwd=None):
    env = os.environ.copy()
    env["HOME"] = os.path.expanduser("~")
    subprocess.run(cmd, shell=True, cwd=cwd, env=env)

def progress(sent, total):
    pct = int((sent / total) * 100) if total else 100
    bar = "█" * (pct // 5)
    print(f"\r[{bar:<20}] {pct:3d}%", end="", flush=True)

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

# ================== UI ==================

def show_logo():
    clear()
    print(color(LOGO, "36"))
    print(color(
        f"Aktivní repo: {CURRENT_REPO if CURRENT_REPO else 'žádné'} | Shell mód: {'ON' if SHELL_MODE else 'OFF'}\n",
        "35"
    ))

def menu():
    print(color("""
[1] Vypsat repozitáře
[2] Přidat repo RUČNĚ (clone)
[3] Aktualizovat repozitář
[4] Aktualizovat VŠECHNY repozitáře
[5] Vybrat aktivní repo
[6] Smazat repozitář
[7] System update & upgrade
[8] Shell mód (bash)
[9] LAN přenos (AES)
[0] Konec
""", "36"))

# ================== DEDCAT UPDATE ==================

def dedcat_update():
    if not Path(".git").exists():
        return

    status = subprocess.run(
        "git status --porcelain",
        shell=True,
        capture_output=True,
        text=True
    )

    print("[DED CAT] checking updates...")
    if status.stdout.strip():
        print("[DED CAT] local changes detected – update skipped")
        return

    run("git pull")

# ================== REPOS ==================

def ensure_repo_dir():
    os.makedirs(REPO_DIR, exist_ok=True)

def repo_name_from_url(url):
    return url.split("/")[-1].replace(".git", "")

def auto_clone_and_update():
    ensure_repo_dir()
    for url in AUTO_REPOS:
        name = repo_name_from_url(url)
        path = f"{REPO_DIR}/{name}"

        if not os.path.isdir(path):
            print(color(f"[CLONE] {name}", "33"))
            run(f"git clone {url}", cwd=REPO_DIR)
        else:
            print(color(f"[UPDATE] {name}", "34"))
            run("git pull", cwd=path)

def list_repos():
    ensure_repo_dir()
    repos = os.listdir(REPO_DIR)
    if not repos:
        print(color("Žádné repozitáře.", "90"))
    for r in repos:
        print(color(f"- {r}", "32"))

def clone_repo_manual():
    ensure_repo_dir()
    url = input(color("GitHub URL: ", "36"))
    run(f"git clone {url}", cwd=REPO_DIR)

def update_repo():
    list_repos()
    repo = input(color("Repo název: ", "36"))
    path = f"{REPO_DIR}/{repo}"
    if os.path.isdir(path):
        run("git pull", cwd=path)

def update_all_repos():
    ensure_repo_dir()
    for r in os.listdir(REPO_DIR):
        path = f"{REPO_DIR}/{r}"
        if os.path.isdir(path):
            print(color(f"→ {r}", "34"))
            run("git pull", cwd=path)

def select_repo():
    global CURRENT_REPO
    list_repos()
    repo = input(color("Repo název: ", "36"))
    if os.path.isdir(f"{REPO_DIR}/{repo}"):
        CURRENT_REPO = repo

def delete_repo():
    list_repos()
    repo = input(color("Smazat repo: ", "31"))
    path = f"{REPO_DIR}/{repo}"
    if os.path.isdir(path):
        run(f"rm -rf {path}")

# ================== SHELL MODE ==================

def shell_loop():
    global SHELL_MODE
    SHELL_MODE = True

    rcfile = "/tmp/dedcat_bashrc"
    with open(rcfile, "w") as f:
        f.write("shelloff(){ exit; }\n")

    try:
        subprocess.run(
            ["bash", "--rcfile", rcfile, "-i"],
            cwd=f"{REPO_DIR}/{CURRENT_REPO}" if CURRENT_REPO else None
        )
    finally:
        SHELL_MODE = False
        if os.path.exists(rcfile):
            os.remove(rcfile)

# ================== LAN ==================

def broadcast_session(name):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    while True:
        s.sendto(name.encode(), ('<broadcast>', LAN_PORT))
        time.sleep(2)

def listen_sessions():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', LAN_PORT))
    print("[LAN] hledám Dedcat session...")
    while True:
        data, addr = s.recvfrom(1024)
        print(f"→ {data.decode()} @ {addr[0]}")

def receive_file(password):
    key = make_key(password)
    fernet = Fernet(key)

    s = socket.socket()
    s.bind(('', LAN_PORT + 1))
    s.listen(1)
    conn, _ = s.accept()

    name = conn.recv(256).decode()
    size = int(conn.recv(32).decode())

    with open(name, "wb") as f:
        received = 0
        while received < size:
            data = conn.recv(BUF)
            if not data:
                break
            chunk = fernet.decrypt(data)
            f.write(chunk)
            received += len(chunk)
            progress(received, size)

    print("\n[LAN] přijato:", name)

def send_file(ip, password, path):
    key = make_key(password)
    fernet = Fernet(key)

    s = socket.socket()
    s.connect((ip, LAN_PORT + 1))

    size = os.path.getsize(path)
    s.send(os.path.basename(path).encode())
    s.send(str(size).encode())

    sent = 0
    with open(path, "rb") as f:
        while chunk := f.read(BUF):
            enc = fernet.encrypt(chunk)
            s.send(enc)
            sent += len(chunk)
            progress(sent, size)

    print("\n[LAN] odesláno")

def lan_menu():
    print("""
[1] PŘÍJEM
[2] ODESLÁNÍ
""")
    c = input("> ")

    if c == "1":
        name = input("session name: ")
        pwd = input("heslo: ")
        threading.Thread(
            target=broadcast_session, args=(name,), daemon=True
        ).start()
        receive_file(pwd)

    if c == "2":
        listen_sessions()
        ip = input("IP cíle: ")
        pwd = input("heslo: ")
        path = input("cesta k souboru: ")
        send_file(ip, pwd, path)

# ================== SYSTEM ==================

def system_update():
    run("sudo apt update && sudo apt upgrade -y")

# ================== MAIN ==================

def main():
    dedcat_update()
    auto_clone_and_update()

    while True:
        show_logo()
        menu()
        cmd = input(color("dedcat> ", "32"))

        if cmd == "1": list_repos()
        elif cmd == "2": clone_repo_manual()
        elif cmd == "3": update_repo()
        elif cmd == "4": update_all_repos()
        elif cmd == "5": select_repo()
        elif cmd == "6": delete_repo()
        elif cmd == "7": system_update()
        elif cmd == "8": shell_loop()
        elif cmd == "9": lan_menu()
        elif cmd == "0": break

        pause()

if __name__ == "__main__":
    main()

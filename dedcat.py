#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
import socket
import threading
import time

# ================= KONFIG =================

REPO_DIR = "repos"
INSTALL_FLAG = ".dedcat_installed"
CURRENT_REPO = None
SHELL_MODE = False

AUTO_REPOS = [
    "https://github.com/htr-tech/zphisher.git",
]

LAN_PORT = 50505
BUFFER = 4096

# ================= LOGO =================

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

# ================= UTIL =================

def c(t, col):
    return f"\033[{col}m{t}\033[0m"

def clear():
    os.system("clear")

def run(cmd, cwd=None):
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    subprocess.run(cmd, shell=True, cwd=cwd, env=env)

def pause():
    input(c("\n[ENTER] pokračuj...", "90"))

def require_sudo():
    if os.geteuid() != 0:
        print(c("Spusť Dedcat pomocí sudo!", "31"))
        sys.exit(1)

# ================= SYSTEM INFO =================

def ram_usage():
    try:
        with open("/proc/meminfo") as f:
            mem = f.read()
        total = int([x for x in mem.splitlines() if "MemTotal" in x][0].split()[1])
        free = int([x for x in mem.splitlines() if "MemAvailable" in x][0].split()[1])
        used = total - free
        return f"{used//1024}MB / {total//1024}MB"
    except:
        return "N/A"

def os_name():
    return platform.system() + " " + platform.release()

# ================= UI =================

def show_logo():
    clear()
    print(c(LOGO, "36"))
    print(c(f"OS: {os_name()} | RAM: {ram_usage()}", "35"))
    print(c(f"Aktivní repo: {CURRENT_REPO if CURRENT_REPO else 'žádné'} | Shell: {'ON' if SHELL_MODE else 'OFF'}\n", "33"))

def menu():
    print(c("""
[1] Vypsat repozitáře
[2] Přidat repo RUČNĚ
[3] Aktualizovat repo
[4] Aktualizovat VŠECHNY
[5] Vybrat aktivní repo
[6] Smazat repo
[7] System update
[8] Shell mód
[9] LAN přenos souborů
[0] Konec
""", "36"))

# ================= SYSTEM =================

def system_update():
    if os.path.exists("/data/data/com.termux"):
        run("pkg update -y && pkg upgrade -y")
    else:
        run("apt update && apt upgrade -y")

def self_update():
    if os.path.isdir(".git"):
        print(c("[DED CAT] checking updates...", "33"))
        run("git fetch origin")
        run("git reset --hard origin/main")

# ================= REPOS =================

def ensure_repo_dir():
    os.makedirs(REPO_DIR, exist_ok=True)

def repo_name(url):
    return url.split("/")[-1].replace(".git", "")

def auto_clone_update():
    ensure_repo_dir()
    for url in AUTO_REPOS:
        name = repo_name(url)
        path = f"{REPO_DIR}/{name}"
        if not os.path.isdir(path):
            print(c(f"[CLONE] {name}", "33"))
            run(f"git clone {url}", cwd=REPO_DIR)
        else:
            print(c(f"[UPDATE] {name}", "34"))
            run("git pull", cwd=path)

def list_repos():
    ensure_repo_dir()
    for r in os.listdir(REPO_DIR):
        print(c(f"- {r}", "32"))

def select_repo():
    global CURRENT_REPO
    list_repos()
    r = input("Repo: ")
    if os.path.isdir(f"{REPO_DIR}/{r}"):
        CURRENT_REPO = r

# ================= SHELL =================

def shell_mode():
    print(c("[SHELL MODE] napiš 'shelloff' pro návrat", "33"))
    while True:
        cmd = input(c("(dedcat)$ ", "32"))
        if cmd.strip() == "shelloff":
            break
        subprocess.call(cmd, shell=True)

# ================= LAN TRANSFER =================

def progress(sent, total):
    pct = int((sent/total)*100)
    bar = "#"*(pct//5)
    print(f"\r[{bar:<20}] {pct}%", end="")

def lan_receive():
    name = input("Session název: ")
    password = input("Heslo: ")

    s = socket.socket()
    s.bind(("", LAN_PORT))
    s.listen(1)
    print("Čekám na připojení...")

    conn, _ = s.accept()
    if conn.recv(1024).decode() != password:
        conn.close()
        return

    fname = conn.recv(1024).decode()
    size = int(conn.recv(1024).decode())
    received = 0

    with open(fname, "wb") as f:
        while received < size:
            data = conn.recv(BUFFER)
            if not data:
                break
            f.write(data)
            received += len(data)
            progress(received, size)

    print("\nHotovo.")
    conn.close()

def lan_send():
    target = input("IP cíle: ")
    password = input("Heslo: ")
    path = input("Cesta k souboru: ")

    size = os.path.getsize(path)
    s = socket.socket()
    s.connect((target, LAN_PORT))
    s.send(password.encode())
    s.send(os.path.basename(path).encode())
    s.send(str(size).encode())

    sent = 0
    with open(path, "rb") as f:
        while chunk := f.read(BUFFER):
            s.send(chunk)
            sent += len(chunk)
            progress(sent, size)

    print("\nOdesláno.")
    s.close()

def lan_menu():
    print("[1] Příchozí\n[2] Odchozí")
    c = input("> ")
    if c == "1":
        lan_receive()
    elif c == "2":
        lan_send()

# ================= MAIN =================

def main():
    require_sudo()
    system_update()
    self_update()
    auto_clone_update()

    global SHELL_MODE

    while True:
        show_logo()
        menu()
        ch = input("dedcat> ")

        if ch == "1": list_repos()
        elif ch == "5": select_repo()
        elif ch == "8": shell_mode()
        elif ch == "9": lan_menu()
        elif ch == "0": break

        pause()

if __name__ == "__main__":
    main()

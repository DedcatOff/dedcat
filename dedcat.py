#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
import socket

# ================= GLOBAL =================

REPO_DIR = "repos"
CURRENT_REPO = None
LAN_PORT = 50505
BUF = 4096

# ================= AUTO REPOS =================
# ⬇⬇⬇ SEM SI BUDEŠ PŘIDÁVAT DALŠÍ REPOZITÁŘE ⬇⬇⬇

AUTO_REPOS = [
    "https://github.com/palahsu/DDoS-Ripper.git",
]

# ================= LOGO =================

LOGO = r"""
 ________  _______   ________  ________  ________  _________   
|\   ___ \|\  ___ \ |\   ___ \|\   ____\|\   __  \|\___   ___\ 
\ \  \_|\ \ \   __/|\ \  \_|\ \ \  \___|\ \  \|\  \|___ \  \_| 
 \ \  \ \\ \ \  \_|/_\ \  \ \\ \ \  \    \ \   __  \   \ \  \  
  \ \  \_\\ \ \  \_|\ \ \  \_\\ \ \  \____\ \  \ \  \   \ \  \ 
   \ \_______\ \_______\ \_______\ \_______\ \__\ \__\   \ \__\
    \|_______|\|_______|\|_______|\|_______|\|__|\|__|    \|__|
                        free the world !
"""

# ================= UTIL =================

def blue(t): return f"\033[94m{t}\033[0m"
def clear(): os.system("clear")
def pause(): input("\n[ENTER] pokračuj...")

def is_termux():
    return os.path.exists("/data/data/com.termux")

def run(cmd, cwd=None):
    subprocess.run(cmd, shell=True, cwd=cwd)

# ================= SYSTEM =================

def system_update():
    print("[*] system update")
    if is_termux():
        run("pkg update -y && pkg upgrade -y")
    else:
        run("apt update && apt upgrade -y")

def dedcat_update():
    if os.path.isdir(".git"):
        print("[*] dedcat update")
        run("git pull")

# ================= AUTO REPOS =================

def repo_name(url):
    return url.split("/")[-1].replace(".git", "")

def auto_clone_update():
    os.makedirs(REPO_DIR, exist_ok=True)
    for url in AUTO_REPOS:
        name = repo_name(url)
        path = f"{REPO_DIR}/{name}"

        if not os.path.isdir(path):
            print(f"[CLONE] {name}")
            run(f"git clone {url}", cwd=REPO_DIR)
        else:
            print(f"[UPDATE] {name}")
            run("git pull", cwd=path)

# ================= UI =================

def show():
    clear()
    print(blue(LOGO))
    print(blue(f"OS: {platform.system()} {platform.release()}"))
    print(blue(f"Aktivní repo: {CURRENT_REPO if CURRENT_REPO else 'žádné'}"))
    print()

def menu():
    print("""
[1] Vypsat repozitáře
[2] Přidat repo (git clone)
[3] Vybrat repo
[4] Shell mód
[5] LAN přenos
[0] Konec
""")

# ================= REPOS =================

def list_repos():
    os.makedirs(REPO_DIR, exist_ok=True)
    r = os.listdir(REPO_DIR)
    if not r:
        print("Žádné repozitáře")
    for x in r:
        print("-", x)

def add_repo():
    os.makedirs(REPO_DIR, exist_ok=True)
    url = input("Git URL: ")
    run(f"git clone {url}", cwd=REPO_DIR)

def select_repo():
    global CURRENT_REPO
    list_repos()
    r = input("Repo: ")
    if os.path.isdir(f"{REPO_DIR}/{r}"):
        CURRENT_REPO = r

# ================= SHELL MODE =================

def shell_mode():
    print("[SHELL MODE] napiš exit pro návrat")
    if CURRENT_REPO:
        run("bash", cwd=f"{REPO_DIR}/{CURRENT_REPO}")
    else:
        run("bash")

# ================= LAN =================

def lan_send():
    ip = input("IP: ")
    path = input("Soubor: ")
    size = os.path.getsize(path)

    s = socket.socket()
    s.connect((ip, LAN_PORT))
    s.send(os.path.basename(path).encode()+b"\n")
    s.send(str(size).encode()+b"\n")

    with open(path, "rb") as f:
        while d := f.read(BUF):
            s.send(d)
    s.close()
    print("Odesláno")

def lan_recv():
    s = socket.socket()
    s.bind(("", LAN_PORT))
    s.listen(1)
    print("Čekám na připojení...")
    c, _ = s.accept()

    name = c.recv(256).decode().strip()
    size = int(c.recv(64).decode().strip())
    got = 0

    with open(name, "wb") as f:
        while got < size:
            d = c.recv(BUF)
            if not d:
                break
            f.write(d)
            got += len(d)

    c.close()
    print("Přijato")

def lan_menu():
    print("[1] Odeslat\n[2] Přijmout")
    c = input("> ")
    if c == "1":
        lan_send()
    elif c == "2":
        lan_recv()

# ================= MAIN =================

def main():
    if not is_termux() and os.geteuid() != 0:
        print("Na Linuxu spusť přes sudo")
        sys.exit(1)

    system_update()
    dedcat_update()
    auto_clone_update()
    pause()

    while True:
        show()
        menu()
        c = input("dedcat> ")

        if c == "1": list_repos()
        elif c == "2": add_repo()
        elif c == "3": select_repo()
        elif c == "4": shell_mode()
        elif c == "5": lan_menu()
        elif c == "0": break

        pause()

if __name__ == "__main__":
    main()

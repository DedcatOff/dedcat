#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
import time

REPO_DIR = "repos"

AUTO_REPOS = [
    # SEM SI BUDEŠ PŘIDÁVAT DALŠÍ REPOS
    "https://github.com/palahsu/DDoS-Ripper.git",
]

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

def blue(t): return f"\033[94m{t}\033[0m"
def clear(): os.system("clear")

def is_termux():
    return os.path.exists("/data/data/com.termux")

def pause():
    input("\nENTER")

def run(cmd, cwd=None):
    subprocess.run(cmd, shell=True, cwd=cwd)

def run_user(cmd, cwd=None):
    user = os.environ.get("SUDO_USER")
    if user:
        subprocess.run(f"sudo -u {user} {cmd}", shell=True, cwd=cwd)
    else:
        subprocess.run(cmd, shell=True, cwd=cwd)

def show():
    clear()
    print(blue(LOGO))
    print(blue(f"OS: {platform.system()} {platform.release()}"))
    print(blue(f"Aktivní repo: {CURRENT_REPO if CURRENT_REPO else 'žádné'}"))
    print()

def menu():
    print("""
[1] Vypsat repozitáře
[2] Vybrat repo
[3] Shell mód
[4] LAN přenos
[0] Konec
""")

def system_update():
    print("[SYSTEM] update & upgrade")
    if is_termux():
        run("pkg update -y && pkg upgrade -y")
    else:
        run("apt update && apt upgrade -y")

def dedcat_update():
    if not os.path.isdir(".git"):
        return
    print("[DED CAT] checking updates...")
    run_user("git fetch origin")
    run_user("git reset --hard origin/main")

def ensure_repo_dir():
    run_user(f"mkdir -p {REPO_DIR}")

def repo_name(url):
    return url.split("/")[-1].replace(".git", "")

def auto_clone():
    ensure_repo_dir()
    for url in AUTO_REPOS:
        name = repo_name(url)
        path = f"{REPO_DIR}/{name}"
        if not os.path.isdir(path):
            print(f"[CLONE] {name}")
            run_user(f"git clone --depth 1 {url}", cwd=REPO_DIR)
        else:
            print(f"[UPDATE] {name}")
            run_user("git pull", cwd=path)

def list_repos():
    if not os.path.isdir(REPO_DIR):
        print("žádné")
        return
    for r in os.listdir(REPO_DIR):
        print("-", r)

def select_repo():
    global CURRENT_REPO
    list_repos()
    r = input("Repo: ")
    if os.path.isdir(f"{REPO_DIR}/{r}"):
        CURRENT_REPO = r

def shell_mode():
    print("\n[SHELL MODE] napiš 'exit' pro návrat\n")
    cwd = f"{REPO_DIR}/{CURRENT_REPO}" if CURRENT_REPO else None
    os.execvp("bash", ["bash"] if not cwd else ["bash", "-i"])

def pad(data):
    l = 16 - len(data) % 16
    return data + bytes([l]) * l

def unpad(data):
    return data[:-data[-1]]

def key_from_pass(p):
    return hashlib.sha256(p.encode()).digest()

def lan_receive():
    name = input("Session: ")
    passwd = input("Heslo: ")
    key = key_from_pass(passwd)

    s = socket.socket()
    s.bind(("", LAN_PORT))
    s.listen(1)
    print("Čekám na připojení...")

    c, _ = s.accept()
    iv = c.recv(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)

    fname = c.recv(256).decode()
    size = int(c.recv(64).decode())
    data = b""

    while len(data) < size:
        data += c.recv(BUF)

    with open(fname, "wb") as f:
        f.write(unpad(cipher.decrypt(data)))

    print("Hotovo.")
    c.close()

def lan_send():
    ip = input("IP: ")
    passwd = input("Heslo: ")
    path = input("Soubor: ")

    key = key_from_pass(passwd)
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)

    data = open(path, "rb").read()
    enc = cipher.encrypt(pad(data))

    s = socket.socket()
    s.connect((ip, LAN_PORT))
    s.send(iv)
    s.send(os.path.basename(path).encode().ljust(256))
    s.send(str(len(enc)).encode().ljust(64))
    s.send(enc)
    s.close()
    print("Odesláno.")

def lan_menu():
    print("[1] Příjem\n[2] Odeslání")
    c = input("> ")
    if c == "1": lan_receive()
    if c == "2": lan_send()

def main():
    if not is_termux() and os.geteuid() != 0:
        print("Spusť přes sudo (Linux) / v Termuxu bez sudo")
        sys.exit(1)

    system_update()
    dedcat_update()
    auto_clone()
    pause()

    while True:
        show()
        menu()
        c = input("> ")

        if c == "1": list_repos()
        elif c == "2": select_repo()
        elif c == "3": shell_mode()
        elif c == "4": lan_menu()
        elif c == "0": break

        pause()

if __name__ == "__main__":
    main()

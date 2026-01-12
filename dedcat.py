#!/usr/bin/env python3
import os, sys, socket, time, threading, subprocess, platform

# ================== KONFIG ==================

REPO_DIR = "repos"
AUTO_REPOS = [
    # SEM SI PŘIDÁVEJ REPA:
    # "https://github.com/user/repo.git",
]

LAN_BROADCAST_PORT = 40404
LAN_TRANSFER_PORT = 50505
BUF = 4096

CURRENT_REPO = None

# ================== LOGO ==================

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

# ================== UTIL ==================

def blue(t): return f"\033[94m{t}\033[0m"
def clear(): os.system("clear")
def pause(): input("\nENTER")

def run(cmd, cwd=None):
    subprocess.run(cmd, shell=True, cwd=cwd)

def is_termux():
    return os.path.exists("/data/data/com.termux")

# ================== UI ==================

def show():
    clear()
    print(blue(LOGO))
    print(blue(f"OS: {platform.system()} {platform.release()}"))
    print(blue(f"Aktivní repo: {CURRENT_REPO if CURRENT_REPO else 'žádné'}\n"))

def menu():
    print("""
[1] Vypsat repozitáře
[2] Přidat repo ručně
[3] Aktualizovat všechny repa
[4] Vybrat repo
[5] Shell mód
[6] LAN přenos
[0] Konec
""")

# ================== REPOS ==================

def ensure_repo_dir():
    os.makedirs(REPO_DIR, exist_ok=True)

def repo_name(url):
    return url.split("/")[-1].replace(".git", "")

def auto_clone():
    ensure_repo_dir()
    for url in AUTO_REPOS:
        name = repo_name(url)
        path = f"{REPO_DIR}/{name}"
        if not os.path.isdir(path):
            run(f"git clone {url}", cwd=REPO_DIR)

def list_repos():
    ensure_repo_dir()
    for r in os.listdir(REPO_DIR):
        print("-", r)

def add_repo():
    ensure_repo_dir()
    url = input("Repo URL: ")
    run(f"git clone {url}", cwd=REPO_DIR)

def update_all():
    ensure_repo_dir()
    for r in os.listdir(REPO_DIR):
        run("git pull", cwd=f"{REPO_DIR}/{r}")

def select_repo():
    global CURRENT_REPO
    list_repos()
    r = input("Repo: ")
    if os.path.isdir(f"{REPO_DIR}/{r}"):
        CURRENT_REPO = r

# ================== SHELL ==================

def shell_mode():
    print("shelloff = návrat")
    cwd = f"{REPO_DIR}/{CURRENT_REPO}" if CURRENT_REPO else None
    while True:
        cmd = input("$ ")
        if cmd == "shelloff":
            break
        run(cmd, cwd=cwd)

# ================== PROGRESS ==================

def progress(done, total):
    p = int(done / total * 100)
    bar = "#" * (p // 5)
    print(f"\r[{bar:<20}] {p}%", end="", flush=True)

# ================== LAN ==================

def lan_host():
    name = input("Session jméno: ")
    password = input("Heslo: ")

    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    tcp = socket.socket()
    tcp.bind(("", LAN_TRANSFER_PORT))
    tcp.listen(1)

    def broadcaster():
        while True:
            udp.sendto(f"DEDCAST|{name}".encode(), ("<broadcast>", LAN_BROADCAST_PORT))
            time.sleep(2)

    threading.Thread(target=broadcaster, daemon=True).start()
    print("Čekám na připojení...")

    conn, _ = tcp.accept()
    if conn.recv(64).decode() != password:
        conn.close()
        return

    while True:
        cmd = conn.recv(256).decode()
        if cmd.startswith("UPLOAD"):
            _, fname, size = cmd.split("|")
            size = int(size)
            got = 0
            with open(fname, "wb") as f:
                while got < size:
                    d = conn.recv(BUF)
                    f.write(d)
                    got += len(d)
                    progress(got, size)
            print("\nPřijato:", fname)
        elif cmd == "EXIT":
            break

    conn.close()

def lan_discover():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("", LAN_BROADCAST_PORT))
    s.settimeout(5)
    found = {}
    start = time.time()
    while time.time() - start < 5:
        try:
            d, a = s.recvfrom(1024)
            if d.startswith(b"DEDCAST|"):
                found[d.decode().split("|")[1]] = a[0]
        except:
            pass
    return found

def lan_connect():
    sessions = lan_discover()
    if not sessions:
        print("Žádné session")
        return

    for i, s in enumerate(sessions):
        print(f"[{i}] {s}")

    sel = int(input("Vyber: "))
    name = list(sessions)[sel]
    ip = sessions[name]

    password = input("Heslo: ")

    sock = socket.socket()
    sock.connect((ip, LAN_TRANSFER_PORT))
    sock.send(password.encode())

    print("Připojeno – shell mód")
    while True:
        cmd = input("(lan)$ ")
        if cmd == "shelloff":
            sock.send(b"EXIT")
            break
        if cmd.startswith("upload "):
            path = cmd.split(" ", 1)[1]
            size = os.path.getsize(path)
            sock.send(f"UPLOAD|{os.path.basename(path)}|{size}".encode())
            sent = 0
            with open(path, "rb") as f:
                while d := f.read(BUF):
                    sock.send(d)
                    sent += len(d)
                    progress(sent, size)
            print("\nOdesláno")

    sock.close()

def lan_menu():
    print("[1] Vytvořit session")
    print("[2] Připojit se")
    c = input("> ")
    if c == "1":
        lan_host()
    elif c == "2":
        lan_connect()

# ================== MAIN ==================

def main():
    if not is_termux() and os.geteuid() != 0:
        print("Na Linuxu spusť přes sudo")
        sys.exit(1)

    if not is_termux():
        run("apt update && apt upgrade -y")

    auto_clone()

    while True:
        show()
        menu()
        c = input("> ")

        if c == "1": list_repos()
        elif c == "2": add_repo()
        elif c == "3": update_all()
        elif c == "4": select_repo()
        elif c == "5": shell_mode()
        elif c == "6": lan_menu()
        elif c == "0": break

        pause()

if __name__ == "__main__":
    main()

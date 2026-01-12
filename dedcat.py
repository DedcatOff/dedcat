#!/usr/bin/env python3
import os, sys, subprocess, platform, socket, time

# ================= KONFIG =================

REPO_DIR = "repos"
CURRENT_REPO = None
SHELL_MODE = False

DED_CAT_REPO = "https://github.com/DedcatOff/dedcat.git"

AUTO_REPOS = [
    "https://github.com/RetroXploit/DDoS-Ripper.git",
]

LAN_PORT = 50505
BUF = 4096

# ================= LOGO =================

LOGO = r"""
                               ^Q,                              Q;
                              QQQQ                            QQQ
                             QQQQQ:                          QQQQQ
                             QQQQQQQ                         QQQQQQ
                            QQQQQQQQQ                       QQQQQQQQ
                            QQQQ QQQQQ   QQQQQQQ+QQQQQQ~QQ QQQQQQQQQ
                           QQQQQQQvQQ<QQxQQQQQQQQQQQQQQ<QQQQQ~QQQQQ<Q
                           QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ
                free the world !
"""

# ================= UTIL =================

def c(t, col): return f"\033[{col}m{t}\033[0m"
def clear(): os.system("clear")

def run_root(cmd):
    subprocess.run(cmd, shell=True)

def run_user(cmd, cwd=None):
    user = os.environ.get("SUDO_USER")
    if user:
        subprocess.run(f"sudo -u {user} {cmd}", shell=True, cwd=cwd)
    else:
        subprocess.run(cmd, shell=True, cwd=cwd)

def pause():
    input(c("\n[ENTER] pokračuj...", "90"))

# ================= INFO =================

def ram():
    try:
        m = open("/proc/meminfo").read()
        t = int([x for x in m.splitlines() if "MemTotal" in x][0].split()[1])
        a = int([x for x in m.splitlines() if "MemAvailable" in x][0].split()[1])
        return f"{(t-a)//1024}MB / {t//1024}MB"
    except:
        return "N/A"

def os_name():
    return f"{platform.system()} {platform.release()}"

# ================= UI =================

def show():
    clear()
    print(c(LOGO, "36"))
    print(c(f"OS: {os_name()} | RAM: {ram()}", "35"))
    print(c(f"Aktivní repo: {CURRENT_REPO if CURRENT_REPO else 'žádné'}", "33"))

def menu():
    print(c("""
[1] Vypsat repozitáře
[5] Vybrat repo
[8] Shell mód
[9] LAN přenos
[0] Konec
""", "36"))

# ================= SYSTEM =================

def system_update():
    if os.path.exists("/data/data/com.termux"):
        run_root("pkg update -y && pkg upgrade -y")
    else:
        run_root("apt update && apt upgrade -y")

# ================= DEDCAT UPDATE =================

def dedcat_update():
    if not os.path.isdir(".git"):
        return
    print(c("[DED CAT] checking updates...", "33"))
    run_user("git fetch origin")
    run_user("git reset --hard origin/main")

# ================= REPOS =================

def ensure_repo_dir():
    run_user(f"mkdir -p {REPO_DIR}")

def repo_name(url):
    return url.split("/")[-1].replace(".git", "")

def auto_clone_update():
    ensure_repo_dir()
    for url in AUTO_REPOS:
        name = repo_name(url)
        path = f"{REPO_DIR}/{name}"
        if not os.path.isdir(path):
            print(c(f"[CLONE] {name}", "32"))
            run_user(f"git clone --depth 1 {url}", cwd=REPO_DIR)
        else:
            print(c(f"[UPDATE] {name}", "34"))
            run_user("git pull", cwd=path)

def list_repos():
    if not os.path.isdir(REPO_DIR):
        print("Žádné repozitáře")
        return
    for r in os.listdir(REPO_DIR):
        print("-", r)

def select_repo():
    global CURRENT_REPO
    list_repos()
    r = input("Repo: ")
    if os.path.isdir(f"{REPO_DIR}/{r}"):
        CURRENT_REPO = r

# ================= SHELL =================

def shell():
    print(c("[SHELL MODE] napiš 'shelloff' pro návrat", "33"))
    while True:
        cmd = input("(dedcat)$ ")
        if cmd == "shelloff":
            break
        run_user(cmd)

# ================= LAN =================

def progress(done, total):
    p = int(done/total*100)
    bar = "#"*(p//5)
    print(f"\r[{bar:<20}] {p}%", end="")

def lan_receive():
    name = input("Session název: ")
    passwd = input("Heslo: ")

    s = socket.socket()
    s.bind(("", LAN_PORT))
    s.listen(1)
    print("Čekám na připojení...")

    c, _ = s.accept()
    if c.recv(64).decode() != passwd:
        c.close(); return

    fname = c.recv(256).decode()
    size = int(c.recv(64).decode())
    got = 0

    with open(fname, "wb") as f:
        while got < size:
            d = c.recv(BUF)
            if not d: break
            f.write(d)
            got += len(d)
            progress(got, size)

    print("\nHotovo.")
    c.close()

def lan_send():
    ip = input("IP cíle: ")
    passwd = input("Heslo: ")
    path = input("Soubor: ")

    size = os.path.getsize(path)
    s = socket.socket()
    s.connect((ip, LAN_PORT))
    s.send(passwd.encode())
    s.send(os.path.basename(path).encode())
    s.send(str(size).encode())

    sent = 0
    with open(path, "rb") as f:
        while d := f.read(BUF):
            s.send(d)
            sent += len(d)
            progress(sent, size)

    print("\nOdesláno.")
    s.close()

def lan_menu():
    print("[1] Příjem\n[2] Odeslání")
    c = input("> ")
    if c == "1": lan_receive()
    if c == "2": lan_send()

# ================= MAIN =================

def main():
    if os.geteuid() != 0:
        print("Spusť přes sudo"); sys.exit(1)

    system_update()
    dedcat_update()
    auto_clone_update()

    while True:
        show()
        menu()
        ch = input("dedcat> ")

        if ch == "1": list_repos()
        elif ch == "5": select_repo()
        elif ch == "8": shell()
        elif ch == "9": lan_menu()
        elif ch == "0": break

        pause()

if __name__ == "__main__":
    main()

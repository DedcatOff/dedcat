#!/usr/bin/env python3
import os, sys, socket, time, platform, subprocess, hashlib, base64, threading, curses
from cryptography.fernet import Fernet

# ================== KONFIG ==================

REPO_DIR = "repos"
AUTO_REPOS = [
    "https://github.com/palahsu/DDoS-Ripper.git",
]

DED_CAT_REPO = "https://github.com/DedcatOff/dedcat.git"

LAN_PORT = 50505
BROADCAST_PORT = 50506
BUF = 4096

CURRENT_REPO = None

# ================== LOGO ==================

LOGO = r"""
                               ^Q,                              Q;
                              QQQQ                            QQQ
                             QQQQQ:                          QQQQQ
                             QQQQQQQ                         QQQQQQ
                            QQQQQQQQQ                       QQQQQQQQ
                            QQQQ QQQQQ   QQQQQQQ+QQQQQQ~QQ QQQQQQQQQ
                           QQQQQQQvQQ<QQxQQQQQQQQQQQQQQ<QQQQQ~QQQQQ<Q
                           QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ

                                D E D C A T
                             free the world !
"""

# ================== AES ==================

def make_key(password: str) -> bytes:
    h = hashlib.sha256(password.encode()).digest()
    return base64.urlsafe_b64encode(h)

# ================== INFO ==================

def ram():
    try:
        m = open("/proc/meminfo").read()
        t = int([x for x in m.splitlines() if "MemTotal" in x][0].split()[1])
        a = int([x for x in m.splitlines() if "MemAvailable" in x][0].split()[1])
        return f"{(t-a)//1024}MB/{t//1024}MB"
    except:
        return "N/A"

def os_name():
    return f"{platform.system()} {platform.release()}"

# ================== RUN HELPERS ==================

def run_root(cmd):
    subprocess.run(cmd, shell=True)

def run_user(cmd, cwd=None):
    user = os.environ.get("SUDO_USER")
    if user:
        subprocess.run(f"sudo -u {user} {cmd}", shell=True, cwd=cwd)
    else:
        subprocess.run(cmd, shell=True, cwd=cwd)

# ================== DEDCAT UPDATE ==================

def dedcat_update_check():
    if not os.path.isdir(".git"):
        return 0
    subprocess.run("git fetch origin", shell=True, stdout=subprocess.DEVNULL)
    out = subprocess.check_output(
        "git rev-list HEAD...origin/main --count",
        shell=True
    ).decode().strip()
    return int(out)

def dedcat_update():
    run_root("git reset --hard origin/main")

# ================== REPOS ==================

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
            run_user(f"git clone --depth 1 {url}", cwd=REPO_DIR)
        else:
            run_user("git pull", cwd=path)

def list_repos(stdscr):
    ensure_repo_dir()
    y = 10
    for r in os.listdir(REPO_DIR):
        stdscr.addstr(y, 4, f"- {r}")
        y += 1

def select_repo(stdscr):
    global CURRENT_REPO
    curses.echo()
    stdscr.addstr(10, 4, "Repo: ")
    r = stdscr.getstr().decode()
    curses.noecho()
    if os.path.isdir(f"{REPO_DIR}/{r}"):
        CURRENT_REPO = r

# ================== SHELL MODE ==================

def shell_mode(stdscr):
    curses.endwin()
    print("\n[SHELL MODE] napiš 'shelloff'\n")
    while True:
        cmd = input("(dedcat)$ ")
        if cmd == "shelloff":
            break
        run_user(cmd)
    curses.initscr()

# ================== LAN DISCOVERY ==================

def broadcast_listener(found):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("", BROADCAST_PORT))
    while True:
        data, addr = s.recvfrom(128)
        if data == b"DEDCAT_DISCOVERY":
            found.add(addr[0])
            s.sendto(socket.gethostname().encode(), addr)

def discover_dedcats(timeout=3):
    found = set()
    threading.Thread(target=broadcast_listener, args=(found,), daemon=True).start()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.sendto(b"DEDCAT_DISCOVERY", ("<broadcast>", BROADCAST_PORT))
    time.sleep(timeout)
    return list(found)

# ================== LAN TRANSFER (AES) ==================

def lan_receive(stdscr):
    curses.echo()
    stdscr.addstr(10, 4, "Heslo: ")
    pwd = stdscr.getstr().decode()
    curses.noecho()

    key = Fernet(make_key(pwd))
    s = socket.socket()
    s.bind(("", LAN_PORT))
    s.listen(1)

    stdscr.addstr(12, 4, "Čekám na připojení...")
    stdscr.refresh()

    c, _ = s.accept()
    size = int(c.recv(32).decode())
    name = c.recv(256).decode()

    data = b""
    got = 0
    while got < size:
        d = c.recv(BUF)
        if not d:
            break
        data += d
        got += len(d)

    dec = key.decrypt(data)
    open(name, "wb").write(dec)

    stdscr.addstr(14, 4, f"Přijato: {name}")
    c.close()

def lan_send(stdscr):
    curses.echo()
    stdscr.addstr(10, 4, "IP: ")
    ip = stdscr.getstr().decode()
    stdscr.addstr(11, 4, "Heslo: ")
    pwd = stdscr.getstr().decode()
    stdscr.addstr(12, 4, "Soubor: ")
    path = stdscr.getstr().decode()
    curses.noecho()

    key = Fernet(make_key(pwd))
    raw = open(path, "rb").read()
    enc = key.encrypt(raw)

    s = socket.socket()
    s.connect((ip, LAN_PORT))
    s.send(str(len(enc)).encode().ljust(32))
    s.send(os.path.basename(path).encode().ljust(256))
    s.send(enc)
    s.close()

    stdscr.addstr(14, 4, "Odesláno.")

# ================== SYSTEM ==================

def system_update():
    if os.path.exists("/data/data/com.termux"):
        run_root("pkg update -y && pkg upgrade -y")
    else:
        run_root("apt update && apt upgrade -y")

# ================== TUI ==================

def tui(stdscr):
    curses.curs_set(0)

    upd = dedcat_update_check()
    if upd > 0:
        stdscr.addstr(2, 2, f"[UPDATE] Dedcat má {upd} změn – ENTER = update / skip")
        stdscr.getch()
        dedcat_update()

    auto_clone_update()

    while True:
        stdscr.clear()
        stdscr.border()

        stdscr.addstr(1, 2, LOGO)
        stdscr.addstr(8, 2, f"OS: {os_name()} | RAM: {ram()}")

        stdscr.addstr(10, 4, "[1] Repozitáře")
        stdscr.addstr(11, 4, "[2] Vybrat repo")
        stdscr.addstr(12, 4, "[3] Shell mód")
        stdscr.addstr(13, 4, "[4] LAN příjem (AES)")
        stdscr.addstr(14, 4, "[5] LAN odeslání (AES)")
        stdscr.addstr(15, 4, "[6] Najít Dedcaty v LAN")
        stdscr.addstr(16, 4, "[7] System update")
        stdscr.addstr(17, 4, "[0] Konec")

        k = stdscr.getch()

        if k == ord("1"):
            list_repos(stdscr); stdscr.getch()
        elif k == ord("2"):
            select_repo(stdscr)
        elif k == ord("3"):
            shell_mode(stdscr)
        elif k == ord("4"):
            lan_receive(stdscr); stdscr.getch()
        elif k == ord("5"):
            lan_send(stdscr); stdscr.getch()
        elif k == ord("6"):
            res = discover_dedcats()
            y = 19
            for ip in res:
                stdscr.addstr(y, 4, f"- {ip}")
                y += 1
            stdscr.getch()
        elif k == ord("7"):
            system_update()
        elif k == ord("0"):
            break

# ================== MAIN ==================

def main():
    if os.geteuid() != 0:
        print("Spusť přes sudo")
        sys.exit(1)
    curses.wrapper(tui)

if __name__ == "__main__":
    main()

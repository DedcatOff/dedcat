#!/usr/bin/env python3
import os, sys, subprocess, platform, time, socket, threading, hashlib, base64, curses, psutil
from cryptography.fernet import Fernet

REPO_DIR = "repos"
LAN_PORT = 50505
BROADCAST_PORT = 50506
BUF = 4096
CURRENT_REPO = None

LOGO = """
 ▄▄▄▄▄▄▄▄▄▄   ▄▄▄▄▄▄▄▄▄▄▄  ▄▄▄▄▄▄▄▄▄▄   ▄▄▄▄▄▄▄▄▄▄▄  ▄▄▄▄▄▄▄▄▄▄▄  ▄▄▄▄▄▄▄▄▄▄▄ 
▐░░░░░░░░░░▌ ▐░░░░░░░░░░░▌▐░░░░░░░░░░▌ ▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌
▐░█▀▀▀▀▀▀▀█░▌▐░█▀▀▀▀▀▀▀▀▀ ▐░█▀▀▀▀▀▀▀█░▌▐░█▀▀▀▀▀▀▀▀▀ ▐░█▀▀▀▀▀▀▀█░▌ ▀▀▀▀█░█▀▀▀▀ 
▐░▌       ▐░▌▐░▌          ▐░▌       ▐░▌▐░▌          ▐░▌       ▐░▌     ▐░▌     
▐░▌       ▐░▌▐░█▄▄▄▄▄▄▄▄▄ ▐░▌       ▐░▌▐░▌          ▐░█▄▄▄▄▄▄▄█░▌     ▐░▌     
▐░▌       ▐░▌▐░░░░░░░░░░░▌▐░▌       ▐░▌▐░▌          ▐░░░░░░░░░░░▌     ▐░▌     
▐░▌       ▐░▌▐░█▀▀▀▀▀▀▀▀▀ ▐░▌       ▐░▌▐░▌          ▐░█▀▀▀▀▀▀▀█░▌     ▐░▌     
▐░▌       ▐░▌▐░▌          ▐░▌       ▐░▌▐░▌          ▐░▌       ▐░▌     ▐░▌     
▐░█▄▄▄▄▄▄▄█░▌▐░█▄▄▄▄▄▄▄▄▄ ▐░█▄▄▄▄▄▄▄█░▌▐░█▄▄▄▄▄▄▄▄▄ ▐░▌       ▐░▌     ▐░▌     
▐░░░░░░░░░░▌ ▐░░░░░░░░░░░▌▐░░░░░░░░░░▌ ▐░░░░░░░░░░░▌▐░▌       ▐░▌     ▐░▌     
 ▀▀▀▀▀▀▀▀▀▀   ▀▀▀▀▀▀▀▀▀▀▀  ▀▀▀▀▀▀▀▀▀▀   ▀▀▀▀▀▀▀▀▀▀▀  ▀         ▀       ▀ 
  _____ ____  _____ _____   _____ _     _____   _      ____  ____  _     ____    _ 
/    //  __\/  __//  __/  /__ __Y \ /|/  __/  / \  /|/  _ \/  __\/ \   /  _ \  / \
|  __\|  \/||  \  |  \      / \ | |_|||  \    | |  ||| / \||  \/|| |   | | \|  | |
| |   |    /|  /_ |  /_     | | | | |||  /_   | |/\||| \_/||    /| |_/\| |_/|  \_/
\_/   \_/\_\\____\\____\    \_/ \_/ \|\____\  \_/  \|\____/\_/\_\\____/\____/  (_)
"""

DED_CAT_REPO = "https://github.com/DedcatOff/dedcat.git"

def run_root(cmd):
    subprocess.run(cmd, shell=True)

def run_user(cmd, cwd=None):
    u = os.environ.get("SUDO_USER")
    if u:
        subprocess.run(f"sudo -u {u} {cmd}", shell=True, cwd=cwd)
    else:
        subprocess.run(cmd, shell=True, cwd=cwd)

def system_update():
    if os.path.exists("/data/data/com.termux"):
        run_root("pkg update -y && pkg upgrade -y")
    else:
        run_root("apt update && apt upgrade -y")

def dedcat_update_check():
    if not os.path.isdir(".git"):
        return 0
    run_user("git fetch origin")
    return int(subprocess.check_output("git rev-list HEAD...origin/main --count", shell=True))

def dedcat_update():
    run_root("git reset --hard origin/main")

def ensure_repo_dir():
    os.makedirs(REPO_DIR, exist_ok=True)

def list_repos():
    ensure_repo_dir()
    return os.listdir(REPO_DIR)

def clone_repo(url):
    ensure_repo_dir()
    run_user(f"git clone {url}", cwd=REPO_DIR)

def update_repos():
    for r in list_repos():
        run_user("git pull", cwd=f"{REPO_DIR}/{r}")

def make_key(p):
    return base64.urlsafe_b64encode(hashlib.sha256(p.encode()).digest())

def progress(scr, y, done, total):
    w = 30
    p = int(done / total * w)
    scr.addstr(y, 2, "[" + "#" * p + " " * (w - p) + "]")

def discover():
    found = set()
    def listen():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("", BROADCAST_PORT))
        while True:
            d, a = s.recvfrom(64)
            if d == b"DEDCAT":
                found.add(a[0])
                s.sendto(b"OK", a)
    threading.Thread(target=listen, daemon=True).start()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.sendto(b"DEDCAT", ("<broadcast>", BROADCAST_PORT))
    time.sleep(2)
    return list(found)

def lan_recv(scr):
    curses.echo()
    scr.clear()
    scr.addstr(1,2,"Heslo: ")
    p = scr.getstr().decode()
    curses.noecho()
    f = Fernet(make_key(p))
    s = socket.socket()
    s.bind(("", LAN_PORT))
    s.listen(1)
    scr.addstr(3,2,"Čekám na připojení...")
    scr.refresh()
    c,_ = s.accept()
    size = int(c.recv(32).decode())
    name = c.recv(256).decode().strip()
    data=b""; got=0
    while got < size:
        d=c.recv(BUF)
        data+=d; got+=len(d)
        progress(scr,5,got,size); scr.refresh()
    open(name,"wb").write(f.decrypt(data))
    c.close()
    scr.addstr(7,2,"Hotovo"); scr.getch()

def lan_send(scr):
    curses.echo()
    scr.clear()
    scr.addstr(1,2,"IP: "); ip=scr.getstr().decode()
    scr.addstr(2,2,"Heslo: "); p=scr.getstr().decode()
    scr.addstr(3,2,"Soubor: "); path=scr.getstr().decode()
    curses.noecho()
    f=Fernet(make_key(p))
    raw=open(path,"rb").read()
    enc=f.encrypt(raw)
    s=socket.socket()
    s.connect((ip,LAN_PORT))
    s.send(str(len(enc)).encode().ljust(32))
    s.send(os.path.basename(path).encode().ljust(256))
    sent=0
    for i in range(0,len(enc),BUF):
        s.send(enc[i:i+BUF])
        sent+=BUF
        progress(scr,5,min(sent,len(enc)),len(enc)); scr.refresh()
    s.close()
    scr.addstr(7,2,"Odesláno"); scr.getch()

def shell_mode():
    rc="/tmp/dedcatrc"
    with open(rc,"w") as f:
        f.write("shelloff(){ exit; }\n")
    cwd = f"{REPO_DIR}/{CURRENT_REPO}" if CURRENT_REPO else None
    subprocess.run(["bash","--rcfile",rc,"-i"], cwd=cwd)
    os.remove(rc)

def draw_logo(scr):
    h,w=scr.getmaxyx()
    for i,l in enumerate(LOGO.splitlines()):
        if i+1<h-6:
            scr.addstr(i+1,2,l[:w-4])

def status_bar(scr):
    h,w=scr.getmaxyx()
    ram=psutil.virtual_memory()
    cpu=psutil.cpu_percent()
    osn=f"{platform.system()} {platform.release()}"
    txt=f" OS:{osn} | RAM:{ram.used//1024//1024}/{ram.total//1024//1024}MB | CPU:{cpu}% "
    scr.addstr(h-2,1,txt[:w-2],curses.A_REVERSE)

def tui(scr):
    global CURRENT_REPO
    curses.curs_set(0)
    while True:
        scr.clear(); scr.border()
        draw_logo(scr)
        status_bar(scr)
        scr.addstr(12,2,"1 List repos")
        scr.addstr(13,2,"2 Add repo")
        scr.addstr(14,2,"3 Update repos")
        scr.addstr(15,2,"4 Select repo")
        scr.addstr(16,2,"5 Shell mode")
        scr.addstr(17,2,"6 LAN")
        scr.addstr(18,2,"0 Exit")
        scr.refresh()
        k=scr.getch()
        if k==ord("1"):
            scr.clear()
            y=2
            for r in list_repos():
                scr.addstr(y,2,r); y+=1
            scr.getch()
        elif k==ord("2"):
            curses.echo()
            scr.clear()
            scr.addstr(2,2,"Repo URL: ")
            clone_repo(scr.getstr().decode())
            curses.noecho()
        elif k==ord("3"):
            update_repos()
        elif k==ord("4"):
            curses.echo()
            scr.clear()
            scr.addstr(2,2,"Repo name: ")
            r=scr.getstr().decode()
            if r in list_repos(): CURRENT_REPO=r
            curses.noecho()
        elif k==ord("5"):
            shell_mode()
        elif k==ord("6"):
            scr.clear()
            scr.addstr(2,2,"1 Receive")
            scr.addstr(3,2,"2 Send")
            c=scr.getch()
            if c==ord("1"): lan_recv(scr)
            if c==ord("2"): lan_send(scr)
        elif k==ord("0"):
            break

def main():
    if os.geteuid()!=0:
        print("Run with sudo"); sys.exit(1)
    system_update()
    u=dedcat_update_check()
    if u>0:
        print(f"DED CAT update {u}")
        input("ENTER"); dedcat_update()
    input("ENTER")
    curses.wrapper(tui)

if __name__=="__main__":
    main()

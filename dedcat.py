#!/usr/bin/env python3
import os, sys, subprocess, platform, time, socket, threading, hashlib, base64, curses, psutil
from cryptography.fernet import Fernet

REPO_DIR = "repos"
LAN_PORT = 50505
BROADCAST_PORT = 50506
BUF = 4096
CURRENT_REPO = None

AUTO_REPOS = [
    # SEM PŘIDÁVEJ GITHUB REPOZITÁŘE
    # "https://github.com/user/repo.git",
    "https://github.com/palahsu/DDoS-Ripper.git",
]

DED_CAT_REPO = "https://github.com/DedcatOff/dedcat.git"

LOGO = r"""
                               ^Q,                              Q;
                              QQQQ                            QQQ
                             QQQQQ:                          QQQQQ
                             QQQQQQQ                         QQQQQQ
                            QQQQQQQQQ                       QQQQQQQQ
                           QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ
                                free the world !
"""

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

def repo_name(url):
    return url.split("/")[-1].replace(".git", "")

def auto_clone_repos():
    ensure_repo_dir()
    for url in AUTO_REPOS:
        name = repo_name(url)
        path = f"{REPO_DIR}/{name}"
        if not os.path.isdir(path):
            run_user(f"git clone --depth 1 {url}", cwd=REPO_DIR)
        else:
            run_user("git pull", cwd=path)

def list_repos():
    ensure_repo_dir()
    return os.listdir(REPO_DIR)

def make_key(p):
    return base64.urlsafe_b64encode(hashlib.sha256(p.encode()).digest())

def progress(scr, y, done, total):
    w = 30
    p = int(done / total * w)
    scr.addstr(y, 2, "[" + "#" * p + " " * (w - p) + "]")

def lan_recv(scr):
    curses.echo()
    scr.clear()
    scr.addstr(2,2,"Heslo: ")
    p = scr.getstr().decode()
    curses.noecho()
    f = Fernet(make_key(p))
    s = socket.socket()
    s.bind(("", LAN_PORT))
    s.listen(1)
    scr.addstr(4,2,"Čekám na připojení...")
    scr.refresh()
    c,_ = s.accept()
    size = int(c.recv(32).decode())
    name = c.recv(256).decode().strip()
    data=b""; got=0
    while got < size:
        d=c.recv(BUF)
        data+=d; got+=len(d)
        progress(scr,6,got,size); scr.refresh()
    open(name,"wb").write(f.decrypt(data))
    c.close()
    scr.addstr(8,2,"Hotovo")
    scr.getch()

def lan_send(scr):
    curses.echo()
    scr.clear()
    scr.addstr(2,2,"IP: "); ip=scr.getstr().decode()
    scr.addstr(3,2,"Heslo: "); p=scr.getstr().decode()
    scr.addstr(4,2,"Soubor: "); path=scr.getstr().decode()
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
        progress(scr,6,min(sent,len(enc)),len(enc)); scr.refresh()
    s.close()
    scr.addstr(8,2,"Odesláno")
    scr.getch()

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
        if i+1<h-10:
            scr.addstr(i+1,2,l[:w-4])

def draw_graph(scr, y, label, percent):
    bar = int(percent / 5)
    scr.addstr(y,2,f"{label}: [{'#'*bar}{' '*(20-bar)}] {percent}%")

def status_bar(scr):
    h,w=scr.getmaxyx()
    ram=psutil.virtual_memory()
    cpu=psutil.cpu_percent()
    osn=f"{platform.system()} {platform.release()}"
    txt=f" OS:{osn} | CPU:{cpu}% | RAM:{ram.used//1024//1024}/{ram.total//1024//1024}MB "
    scr.addstr(h-2,1,txt[:w-2],curses.A_REVERSE)

def tui(scr):
    global CURRENT_REPO
    curses.curs_set(0)
    while True:
        scr.clear(); scr.border()
        draw_logo(scr)

        cpu = int(psutil.cpu_percent())
        ram = int(psutil.virtual_memory().percent)

        draw_graph(scr,10,"CPU",cpu)
        draw_graph(scr,11,"RAM",ram)

        status_bar(scr)

        scr.addstr(13,2,"1 Repos")
        scr.addstr(14,2,"2 Select repo")
        scr.addstr(15,2,"3 Shell")
        scr.addstr(16,2,"4 LAN")
        scr.addstr(17,2,"0 Exit")
        scr.refresh()

        scr.timeout(1000)
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
            scr.addstr(2,2,"Repo name: ")
            r=scr.getstr().decode()
            if r in list_repos(): CURRENT_REPO=r
            curses.noecho()
        elif k==ord("3"):
            shell_mode()
        elif k==ord("4"):
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
    auto_clone_repos()

    u=dedcat_update_check()
    if u>0:
        print(f"DED CAT update {u}")
        input("ENTER")
        dedcat_update()

    input("ENTER")
    curses.wrapper(tui)

if __name__=="__main__":
    main()

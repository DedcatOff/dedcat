#!/usr/bin/env python3
import os, sys, subprocess, platform, time, curses, socket

REPO_DIR = "repos"
CURRENT_REPO = None
LAN_PORT = 50505
BUF = 4096

AUTO_REPOS = [
    "https://github.com/RetroXploit/DDoS-Ripper.git",
]

LOGO = r"""
 _____     ______     _____     ______     ______     ______  
/\  __-.  /\  ___\   /\  __-.  /\  ___\   /\  __ \   /\__  _\ 
\ \ \/\ \ \ \  __\   \ \ \/\ \ \ \ \____  \ \  __ \  \/_/\ \/ 
 \ \____-  \ \_____\  \ \____-  \ \_____\  \ \_\ \_\    \ \_\ 
  \/____/   \/_____/   \/____/   \/_____/   \/_/\/_/     \/_/ 
"""

def run_root(cmd):
    subprocess.run(cmd, shell=True)

def run_user(cmd, cwd=None):
    user = os.environ.get("SUDO_USER")
    if user:
        subprocess.run(["sudo", "-u", user, "bash", "-c", cmd], cwd=cwd)
    else:
        subprocess.run(cmd, shell=True, cwd=cwd)

def pause():
    input("\nENTER")

def system_update():
    if os.path.exists("/data/data/com.termux"):
        run_root("pkg update -y && pkg upgrade -y")
    else:
        run_root("apt update && apt upgrade -y")

def dedcat_update():
    if not os.path.isdir(".git"):
        return
    run_user("git fetch origin")
    run_user("git reset --hard origin/main")

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
        run_user(f"git config --global --add safe.directory {os.path.abspath(path)}")

def list_repos():
    if not os.path.isdir(REPO_DIR):
        return []
    return os.listdir(REPO_DIR)

def shell_mode(stdscr):
    curses.endwin()
    while True:
        cmd = input("dedcat$ ")
        if cmd.strip() in ("exit", "shelloff"):
            break
        run_user(cmd)
    stdscr.clear()

def lan_menu(stdscr):
    stdscr.clear()
    stdscr.addstr(1,2,"LAN")
    stdscr.addstr(3,4,"1 - čekat")
    stdscr.addstr(4,4,"2 - odeslat")
    stdscr.addstr(6,4,"libovolná klávesa zpět")
    stdscr.refresh()
    k = stdscr.getch()
    if k == ord("1"):
        curses.endwin()
        s = socket.socket()
        s.bind(("", LAN_PORT))
        s.listen(1)
        print("čekám...")
        c,_ = s.accept()
        print("připojeno")
        c.close()
        s.close()
        input("ENTER")
        stdscr.clear()
    if k == ord("2"):
        curses.endwin()
        ip = input("IP: ")
        s = socket.socket()
        s.connect((ip, LAN_PORT))
        s.close()
        input("ENTER")
        stdscr.clear()

def draw(stdscr):
    h,w = stdscr.getmaxyx()
    stdscr.addstr(1,2,LOGO[:w-4])
    stdscr.addstr(h-2,2,f"OS: {platform.system()} | Repo: {CURRENT_REPO or 'žádné'}")

def tui(stdscr):
    global CURRENT_REPO
    curses.curs_set(0)
    stdscr.nodelay(False)
    while True:
        stdscr.clear()
        draw(stdscr)
        stdscr.addstr(12,4,"1 - repozitáře")
        stdscr.addstr(13,4,"2 - shell")
        stdscr.addstr(14,4,"3 - LAN")
        stdscr.addstr(15,4,"0 - konec")
        stdscr.refresh()
        k = stdscr.getch()
        if k == ord("0"):
            break
        if k == ord("1"):
            stdscr.clear()
            repos = list_repos()
            for i,r in enumerate(repos):
                stdscr.addstr(2+i,4,f"{i+1} - {r}")
            stdscr.addstr(2+len(repos)+2,4,"ENTER zpět")
            stdscr.refresh()
            sel = stdscr.getch()
            if ord("1") <= sel <= ord(str(len(repos))):
                CURRENT_REPO = repos[int(chr(sel))-1]
        if k == ord("2"):
            shell_mode(stdscr)
        if k == ord("3"):
            lan_menu(stdscr)

def main():
    if os.geteuid() != 0:
        print("spusť přes sudo")
        sys.exit(1)
    system_update()
    dedcat_update()
    auto_clone_update()
    pause()
    curses.wrapper(tui)

if __name__ == "__main__":
    main()

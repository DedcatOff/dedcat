#!/usr/bin/env python3
import os, sys, subprocess, socket, threading, time, platform

# ================== KONFIG ==================

REPO_DIR = "repos"
CURRENT_REPO = None

DISCOVERY_PORT = 45454
TRANSFER_PORT = 45455
BUF = 4096

AUTO_REPOS = [
    "https://github.com/htr-tech/zphisher.git",
    "https://github.com/RetroXploit/DDoS-Ripper.git",
]

DEDCAT_REPO = "https://github.com/DedcatOff/dedcat"

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

# ================== UTIL ==================

def c(t, col): return f"\033[{col}m{t}\033[0m"
def clear(): os.system("clear")
def run(cmd, cwd=None): subprocess.run(cmd, shell=True, cwd=cwd)

# ================== HEADER ==================

def get_ram():
    try:
        mem = {}
        with open("/proc/meminfo") as f:
            for l in f:
                k,v = l.split(":")
                mem[k] = int(v.strip().split()[0])
        total = mem["MemTotal"]
        avail = mem.get("MemAvailable", mem["MemFree"])
        used = total - avail
        return f"{used//1024}/{total//1024} MB ({int(used/total*100)}%)"
    except:
        return "N/A"

def get_os():
    return f"{platform.system()} {platform.release()}"

def header():
    w = os.get_terminal_size().columns
    line = f" RAM: {get_ram()} │ OS: {get_os()} "
    print(c(line.ljust(w, "─"), "90"))

# ================== UPDATE ==================

def system_update():
    if "termux" in platform.platform().lower():
        run("pkg update -y && pkg upgrade -y")
    else:
        run("apt update -y && apt upgrade -y")

def self_update():
    if os.path.isdir(".git"):
        print(c("[DED CAT] self-update...", "33"))
        run("git pull")

# ================== UI ==================

def show():
    clear()
    header()
    print(c(LOGO, "36"))
    print(c(f"Aktivní repo: {CURRENT_REPO if CURRENT_REPO else 'žádné'}\n", "35"))

def menu():
    print(c("""
[1] Vypsat repozitáře
[2] Přidat repo
[5] Vybrat repo
[8] Shell mód
[9] LAN file transfer
[0] Konec
""", "36"))

# ================== REPOS ==================

def ensure_repos():
    os.makedirs(REPO_DIR, exist_ok=True)

def auto_clone():
    ensure_repos()
    for u in AUTO_REPOS:
        n = u.split("/")[-1].replace(".git","")
        p = f"{REPO_DIR}/{n}"
        if not os.path.isdir(p):
            run(f"git clone {u}", cwd=REPO_DIR)
        else:
            run("git pull", cwd=p)

def list_repos():
    ensure_repos()
    for r in os.listdir(REPO_DIR):
        print("-", r)

def select_repo():
    global CURRENT_REPO
    list_repos()
    r = input("Repo: ")
    if os.path.isdir(f"{REPO_DIR}/{r}"):
        CURRENT_REPO = r

# ================== SHELL ==================

def shell_mode():
    rc = "/tmp/dedcatrc"
    with open(rc,"w") as f:
        f.write("shelloff(){ exit; }\n")
    subprocess.run(
        ["bash","--rcfile",rc,"-i"],
        cwd=f"{REPO_DIR}/{CURRENT_REPO}" if CURRENT_REPO else None
    )
    os.remove(rc)

# ================== PROGRESS ==================

def progress(done,total):
    pct = int(done/total*100)
    print(f"\r[{pct:3}%] {done//1024//1024}/{total//1024//1024} MB",
          end="",flush=True)

# ================== LAN ==================

def lan_receiver():
    name = input("Session name: ")
    pwd = input("Password: ")

    def beacon():
        s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
        while True:
            s.sendto(f"DEDCAT:{name}".encode(),('<broadcast>',DISCOVERY_PORT))
            time.sleep(2)

    threading.Thread(target=beacon,daemon=True).start()

    srv = socket.socket()
    srv.bind(("",TRANSFER_PORT))
    srv.listen(1)
    print(c("[WAITING] příchozí přenos...", "32"))

    conn,_ = srv.accept()
    if conn.recv(1024).decode() != pwd:
        conn.close(); return

    fname = conn.recv(1024).decode()
    size = int(conn.recv(1024).decode())
    rec = 0

    with open(fname,"wb") as f:
        while rec < size:
            d = conn.recv(BUF)
            if not d: break
            f.write(d)
            rec += len(d)
            progress(rec,size)

    print("\n"+c("[RECEIVED]", "32"))
    conn.close()

def send_file(ip,pwd,path):
    size = os.path.getsize(path)
    s = socket.socket()
    s.connect((ip,TRANSFER_PORT))
    s.send(pwd.encode()); time.sleep(0.2)
    s.send(os.path.basename(path).encode()); time.sleep(0.2)
    s.send(str(size).encode()); time.sleep(0.2)

    sent = 0
    with open(path,"rb") as f:
        while d := f.read(BUF):
            s.send(d)
            sent += len(d)
            progress(sent,size)

    print("\n"+c("[SENT]", "32"))
    s.close()

def lan_sender():
    sessions = {}
    ip = None
    pwd = None

    def discover():
        s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.bind(("",DISCOVERY_PORT))
        while True:
            d,a = s.recvfrom(1024)
            if d.startswith(b"DEDCAT:"):
                sessions[d.decode().split(":")[1]] = a[0]

    threading.Thread(target=discover,daemon=True).start()

    print(c("[LAN SEND MODE] čekám na session...", "33"))

    while True:
        print("\nSessions:")
        for s in sessions: print(" -",s)

        cmd = input("(lan)> ").strip()
        if cmd=="exit": break

        if cmd.startswith("connect "):
            n = cmd.split(" ",1)[1]
            if n in sessions:
                ip = sessions[n]
                print("[OK] connected")
            else:
                print("[ERR] nenalezeno")

        elif cmd.startswith("pass "):
            pwd = cmd.split(" ",1)[1]
            print("[OK] password set")

        elif cmd.startswith("upload "):
            if not ip or not pwd:
                print("[ERR] nejdřív connect + pass")
            else:
                send_file(ip,pwd,cmd.split(" ",1)[1])

        else:
            print("příkazy: connect | pass | upload | exit")

def lan():
    m = input("[1] příchozí | [2] odchozí: ")
    if m=="1": lan_receiver()
    else: lan_sender()

# ================== MAIN ==================

def main():
    system_update()
    self_update()
    auto_clone()

    while True:
        show()
        menu()
        c = input("dedcat> ")
        if c=="1": list_repos()
        elif c=="2": auto_clone()
        elif c=="5": select_repo()
        elif c=="8": shell_mode()
        elif c=="9": lan()
        elif c=="0": break

if __name__=="__main__":
    main()

#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
import socket

# ================= KONFIG =================

REPO_DIR = "repos"
CURRENT_REPO = None
SHELL_MODE = False

AUTO_REPOS = [
    "https://github.com/RetroXploit/DDoS-Ripper.git",
]

LAN_PORT = 50505
BUFFER = 4096

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
                           QQ QQQQ          Q^QQ ;Q QQ          QQQQQQ                              
                          QQQQQQ              .QQ:QQ/       !Q]   QQQYQ                             
                         xQQQQQ      Y>QQQQ    `QQQQ QQQQ  QQQ.    QQ<QQ                            
                         QQQQi      QQQQQQQQ)   Q+Q    -QQ'QQ      QQQQQ                            
                           Q       Q  Q _Q Q,Q   Q'      /1 Q        QQ Q                           
                         QQQQQ     QQ QQQQ QQx  |QQv   QQQ QQQQQ   QQQQQQ                           
                        QQQQQQQ    QQ QQ QQQQ   QQQQ} QQQ     QQ  ^Q QQ;QQ                          
                        QQl_Ql"x      QQzQQJ   QQQQCQQ          +  QfJQ1QQ                          
                         QQ.QQ[QQ            QQ,Q Q_ Qt Q-  [ QQQQQQQQQQQQ                          
                        QQQQQQQQQQQQ      QQ QQ QQ}QQQQQQQQ(    QQQ QQ <                            
                          QQzQXQQCJ  |Q c     QQQ  QQ      QQ'QQ   t      <Q                        
                              ;QQiQ|   .QcQQQQX  Q   QQQQQQQQQQQQQ       QQQQ   QQ                  
                                    QQ^QQ QQlQQ.Q   :QQQQQzQQQQQ:Q{     Q+QQ{   QQQ,^"QQQQQQQ       
      QQQQQ               C QQ QQ'Q 1QQ>QQQQQQQQQQ  Q:QQ"QQ:QQ]QcQ     QQQQQQQ   XQx{QQQQQQXQQ      
       tQQQQQ>QQ     Q.QQ'QQ+QQfQQQ  QQQQQQQQQQQQQ  QQxQQQQQQQQQQQ    .QQ>QQlQ      ;QiQ   J|c      
        Q:QQ_Q.QQ;l   QYQQQQQQQQQQQ  QQQJQQf Q,Qv`t |Qc}QQ<           [^Q  QvQ      QQvQ            
         QQQIQQnQQQQ  [QQQQQ>QQrQQQn  lQQrQ ^xQQtQQ QQQQQQ           QQQQ  QQQ     QQQQQ            
          QQQQQQQQQQQ  QQQQQQQQ+      `QQiQ  ]Q(QQQ QQQQQ           QQQ   Q QQ     QQ:Q             
           QQQQQQQtQQ|  ,QQ~QQ        QjQQQQ  QQQQ( QiQQ;          QQQ-   QQ Q     _QQ>             
            Q'X  :Q.[Q   lQQQQl        'QQ'Q  QQ Q: QQJQQ' X^QQQ  QQQQzQQ}QQ:Q    QcQQ,             
            _Q]QQ {QQQQQ  QQQQQ  QQQQ  QQQQQ  [Q/{" CQQrQQQQQ|Q   ]x Q ^ `QQ Q    Q,QQ              
             QQ/Q  QQQ/QQ QQIQQ<cQQ(QQ QQnQQ  QQ_QQ  QQQQQQQQIQQ QxQQQ    QQ}Q   QQQQ,              
              Q QQ  Q QQ '  Qv Q+,Q!|Q  Q:QQQ Qr QQ   QQQQQQQ<Q QQ`Qt     ' :    ^"c(`              
               [QtI  >QQ.Q  QQ.QQiQQ    QQQ|Q cQQ>:  -  ]Q_<Q"  .Q1QQ     Q :n  ,Q;<Q               
                !_ !  iQ 1  ~ ~Q .      `  Q  Q  Q       QQQ               Q<+  QQQCQ               
                 Q QQ IQ QQ  z QQ        Q Q- Q< Q                                                  
                  l)Q  QQ QQ  Q}iQ/      ' Qi Q                                                     
                   Q^`     ">  t  Q  Q     Q  Q                                                     
                    + Q }QQ QQ  Q  Q  Q                                                             
                                '  '+ .                                                             
                      Q  Q  Q     Q                                                                 
                       Q +Y `_                                                                      
                        .,  [                                                                       
                         .Q  

                free the world !
"""

# ================= UTIL =================

def c(t, col): return f"\033[{col}m{t}\033[0m"
def clear(): os.system("clear")

def run(cmd, cwd=None):
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    subprocess.run(cmd, shell=True, cwd=cwd, env=env,
                   stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)

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
            m = f.read()
        total = int([x for x in m.splitlines() if "MemTotal" in x][0].split()[1])
        free = int([x for x in m.splitlines() if "MemAvailable" in x][0].split()[1])
        return f"{(total-free)//1024}MB / {total//1024}MB"
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
[5] Vybrat aktivní repo
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
            run(f"git clone --depth 1 {url}", cwd=REPO_DIR)
        else:
            print(c(f"[UPDATE] {name}", "34"))
            run("git pull --ff-only", cwd=path)

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

# ================= LAN =================

def lan_menu():
    print("[1] Příjem\n[2] Odeslání")
    input("> (zatím placeholder)")

# ================= MAIN =================

def main():
    require_sudo()

    # 🔥 AUTOMATICKY PŘI STARTU
    system_update()
    auto_clone_update()

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

#!/usr/bin/env python3
import os, sys, subprocess, platform, time, socket, threading, hashlib, base64, curses
from cryptography.fernet import Fernet

REPO_DIR = "repos"
AUTO_REPOS = ["https://github.com/palahsu/DDoS-Ripper.git"]
LAN_PORT = 50505
BROADCAST_PORT = 50506
BUF = 4096

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
"""

def run_root(cmd):
    subprocess.run(cmd, shell=True)

def run_user(cmd, cwd=None):
    user = os.environ.get("SUDO_USER")
    subprocess.run(f"sudo -u {user} {cmd}" if user else cmd, shell=True, cwd=cwd)

def system_update():
    if os.path.exists("/data/data/com.termux"):
        run_root("pkg update -y && pkg upgrade -y")
    else:
        run_root("apt update && apt upgrade -y")

def dedcat_update_check():
    if not os.path.isdir(".git"):
        return 0
    subprocess.run("git fetch origin", shell=True)
    return int(subprocess.check_output("git rev-list HEAD...origin/main --count", shell=True))

def dedcat_update():
    run_root("git reset --hard origin/main")

def make_key(p):
    return base64.urlsafe_b64encode(hashlib.sha256(p.encode()).digest())

def discover():
    found = set()
    def listen():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("", BROADCAST_PORT))
        while True:
            d,a = s.recvfrom(128)
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
    scr.addstr(10,2,"Heslo: ")
    p = scr.getstr().decode()
    curses.noecho()
    f = Fernet(make_key(p))
    s = socket.socket()
    s.bind(("", LAN_PORT))
    s.listen(1)
    c,_ = s.accept()
    size = int(c.recv(32))
    name = c.recv(256).decode()
    data = b""
    while len(data) < size:
        data += c.recv(BUF)
    open(name,"wb").write(f.decrypt(data))
    c.close()
    scr.addstr(12,2,"Hotovo")

def lan_send(scr):
    curses.echo()
    scr.addstr(10,2,"IP: ")
    ip = scr.getstr().decode()
    scr.addstr(11,2,"Heslo: ")
    p = scr.getstr().decode()
    scr.addstr(12,2,"Soubor: ")
    path = scr.getstr().decode()
    curses.noecho()
    f = Fernet(make_key(p))
    raw = open(path,"rb").read()
    enc = f.encrypt(raw)
    s = socket.socket()
    s.connect((ip,LAN_PORT))
    s.send(str(len(enc)).encode().ljust(32))
    s.send(os.path.basename(path).encode().ljust(256))
    s.send(enc)
    s.close()
    scr.addstr(14,2,"Odesláno")

def tui(scr):
    curses.curs_set(0)
    while True:
        scr.clear()
        scr.border()
        scr.addstr(1,2,LOGO)
        scr.addstr(18,2,"1 LAN RECEIVE")
        scr.addstr(19,2,"2 LAN SEND")
        scr.addstr(20,2,"3 DISCOVER")
        scr.addstr(21,2,"0 EXIT")
        k = scr.getch()
        if k == ord("1"):
            lan_recv(scr); scr.getch()
        if k == ord("2"):
            lan_send(scr); scr.getch()
        if k == ord("3"):
            y=23
            for ip in discover():
                scr.addstr(y,2,ip); y+=1
            scr.getch()
        if k == ord("0"):
            break

def main():
    if os.geteuid()!=0:
        print("sudo required"); sys.exit(1)
    system_update()
    u = dedcat_update_check()
    if u>0:
        print(f"{u} updates"); input("ENTER"); dedcat_update()
    input("ENTER")
    curses.wrapper(tui)

if __name__ == "__main__":
    main()

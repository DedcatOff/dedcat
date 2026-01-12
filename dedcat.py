#!/usr/bin/env python3
import os
import sys
import subprocess

# ================== KONFIGURACE ==================

REPO_DIR = "repos"
INSTALL_FLAG = ".dedcat_installed"
CURRENT_REPO = None
SHELL_MODE = False

AUTO_REPOS = [
    "https://github.com/R3DHULK/wifi-hacking.git",
    "https://github.com/aircrack-ng/aircrack-ng",
    "https://github.com/htr-tech/zphisher.git",
    "https://github.com/RetroXploit/DDoS-Ripper.git",
]

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

def color(t, c): return f"\033[{c}m{t}\033[0m"
def clear(): os.system("clear")
def pause(): input(color("\n[ENTER] pokračuj...", "90"))

def run(cmd, cwd=None):
    subprocess.run(cmd, shell=True, cwd=cwd)

def require_sudo():
    if os.geteuid() != 0:
        print(color("Spusť Dedcat pomocí sudo!", "31"))
        sys.exit(1)

# ================== UI ==================

def show_logo():
    clear()
    print(color(LOGO, "36"))
    print(color(
        f"Aktivní repo: {CURRENT_REPO if CURRENT_REPO else 'žádné'} | Shell mód: {'ON' if SHELL_MODE else 'OFF'}\n",
        "35"
    ))

def menu():
    print(color("""
[1] Vypsat repozitáře
[2] Přidat repo RUČNĚ (clone)
[3] Aktualizovat repozitář
[4] Aktualizovat VŠECHNY repozitáře
[5] Vybrat aktivní repo
[6] Smazat repozitář
[7] System update & upgrade
[8] Shell mód (bash)
[0] Konec
""", "36"))

# ================== REPOS ==================

def ensure_repo_dir():
    os.makedirs(REPO_DIR, exist_ok=True)

def repo_name_from_url(url):
    return url.split("/")[-1].replace(".git", "")

def auto_clone_and_update():
    ensure_repo_dir()
    for url in AUTO_REPOS:
        name = repo_name_from_url(url)
        path = f"{REPO_DIR}/{name}"

        if not os.path.isdir(path):
            print(color(f"[CLONE] {name}", "33"))
            run(f"git clone {url}", cwd=REPO_DIR)
        else:
            print(color(f"[UPDATE] {name}", "34"))
            run("git pull", cwd=path)

def list_repos():
    ensure_repo_dir()
    repos = os.listdir(REPO_DIR)
    if not repos:
        print(color("Žádné repozitáře.", "90"))
    for r in repos:
        print(color(f"- {r}", "32"))

def clone_repo_manual():
    ensure_repo_dir()
    url = input(color("GitHub URL: ", "36"))
    run(f"git clone {url}", cwd=REPO_DIR)

def update_repo():
    list_repos()
    repo = input(color("Repo název: ", "36"))
    path = f"{REPO_DIR}/{repo}"
    if os.path.isdir(path):
        run("git pull", cwd=path)
    else:
        print(color("Repo neexistuje!", "31"))

def update_all_repos():
    ensure_repo_dir()
    for r in os.listdir(REPO_DIR):
        path = f"{REPO_DIR}/{r}"
        if os.path.isdir(path):
            print(color(f"→ {r}", "34"))
            run("git pull", cwd=path)

def select_repo():
    global CURRENT_REPO
    list_repos()
    repo = input(color("Repo název: ", "36"))
    if os.path.isdir(f"{REPO_DIR}/{repo}"):
        CURRENT_REPO = repo
    else:
        print(color("Repo neexistuje!", "31"))

def delete_repo():
    list_repos()
    repo = input(color("Smazat repo: ", "31"))
    path = f"{REPO_DIR}/{repo}"
    if os.path.isdir(path):
        run(f"rm -rf {path}")

# ================== SHELL MODE ==================

def shell_loop():
    global SHELL_MODE
    SHELL_MODE = True

    print(color("\n[SHELL MODE] napiš 'shelloff' pro návrat\n", "33"))

    rcfile = "/tmp/dedcat_bashrc"

    with open(rcfile, "w") as f:
        f.write("""
shelloff() {
    exit
}
""")

    try:
        if CURRENT_REPO:
            subprocess.run(
                ["bash", "--rcfile", rcfile, "-i"],
                cwd=f"{REPO_DIR}/{CURRENT_REPO}"
            )
        else:
            subprocess.run(
                ["bash", "--rcfile", rcfile, "-i"]
            )
    finally:
        SHELL_MODE = False
        if os.path.exists(rcfile):
            os.remove(rcfile)

# ================== SYSTEM ==================

def first_run():
    return not os.path.exists(INSTALL_FLAG)

def mark_installed():
    open(INSTALL_FLAG, "w").close()

def install_dependencies():
    run("apt update")
    run("apt install -y python3 git")

def system_update():
    run("apt update && apt upgrade -y")

# ================== MAIN ==================

def main():
    require_sudo()

    if first_run():
        show_logo()
        install_dependencies()
        mark_installed()
        pause()

    auto_clone_and_update()
    pause()

    while True:
        show_logo()
        menu()
        cmd = input(color("dedcat> ", "32"))

        if cmd == "1": list_repos()
        elif cmd == "2": clone_repo_manual()
        elif cmd == "3": update_repo()
        elif cmd == "4": update_all_repos()
        elif cmd == "5": select_repo()
        elif cmd == "6": delete_repo()
        elif cmd == "7": system_update()
        elif cmd == "8": shell_loop()
        elif cmd == "0": break
        else:
            print(color("Neplatná volba!", "31"))

        pause()

if __name__ == "__main__":
    main()

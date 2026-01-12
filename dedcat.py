#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
import time

REPO_DIR = "repos"

AUTO_REPOS = [
    # SEM SI BUDEŠ PŘIDÁVAT DALŠÍ REPOS
    "https://github.com/palahsu/DDoS-Ripper.git",
]

LOGO = r"""
████▄  ██████ ████▄  ▄█████ ▄████▄ ██████ 
██  ██ ██▄▄   ██  ██ ██     ██▄▄██   ██   
████▀  ██▄▄▄▄ ████▀  ▀█████ ██  ██   ██ 
           free the world !
"""

def blue(t):
    return f"\033[34m{t}\033[0m"

def clear():
    os.system("clear")

def pause():
    input("\n[ENTER] pokračuj...")

def run(cmd, cwd=None):
    subprocess.run(cmd, shell=True, cwd=cwd)

def run_user(cmd, cwd=None):
    user = os.environ.get("SUDO_USER")
    if user:
        subprocess.run(f"sudo -u {user} {cmd}", shell=True, cwd=cwd)
    else:
        subprocess.run(cmd, shell=True, cwd=cwd)

def header():
    clear()
    print(blue(LOGO))
    print(blue(f"OS: {platform.system()} {platform.release()}"))
    print(blue("=" * 60))

def system_update():
    print("[SYSTEM] update & upgrade")
    if os.path.exists("/data/data/com.termux"):
        run("pkg update -y && pkg upgrade -y")
    else:
        run("apt update && apt upgrade -y")

def dedcat_update():
    if not os.path.isdir(".git"):
        return
    print("[DED CAT] checking updates...")
    run_user("git fetch origin")
    run_user("git reset --hard origin/main")

def ensure_repos():
    if not os.path.isdir(REPO_DIR):
        run_user(f"mkdir -p {REPO_DIR}")

def repo_name(url):
    return url.split("/")[-1].replace(".git", "")

def auto_clone_update():
    ensure_repos()
    for url in AUTO_REPOS:
        name = repo_name(url)
        path = f"{REPO_DIR}/{name}"

        if not os.path.isdir(path):
            print(f"[CLONE] {name}")
            run_user(f"git clone {url}", cwd=REPO_DIR)
        else:
            print(f"[UPDATE] {name}")
            run_user("git pull", cwd=path)

def list_repos():
    ensure_repos()
    repos = os.listdir(REPO_DIR)
    if not repos:
        print("Žádné repozitáře")
        return
    for r in repos:
        print("-", r)

def shell_mode():
    print("\n[SHELL MODE]")
    print("Odchod: napiš 'exit'\n")

    user = os.environ.get("SUDO_USER")
    if user:
        os.execvp("sudo", ["sudo", "-u", user, "bash"])
    else:
        os.execvp("bash", ["bash"])

def menu():
    print("""
[1] Vypsat repozitáře
[2] Update repozitářů
[3] Shell mód (normální bash)
[0] Konec
""")

def main():
    if os.geteuid() != 0:
        print("Spusť přes sudo")
        sys.exit(1)

    header()
    system_update()
    pause()

    header()
    dedcat_update()
    pause()

    header()
    auto_clone_update()
    pause()

    while True:
        header()
        menu()
        c = input("dedcat> ")

        if c == "1":
            list_repos()
            pause()
        elif c == "2":
            auto_clone_update()
            pause()
        elif c == "3":
            shell_mode()
        elif c == "0":
            break

if __name__ == "__main__":
    main()

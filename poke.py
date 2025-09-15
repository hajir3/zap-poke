#!/usr/bin/env python3
import os, sys, json, socket, threading, platform, subprocess, shutil
from pathlib import Path

CONFIG_PATH = os.path.expanduser("~/.config/zap-poke/config.json")
PORT = 9999

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {"friends": {}}
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

def cmd_init():
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    save_config({"friends": {}})
    print("zap-poke initialisiert...")

    system = platform.system()
    user_home = str(Path.home())

    if system == "Linux":
        user = os.getenv("USER")
        service_path = Path(f"{user_home}/.config/systemd/user/zap-poke.service")
        if not service_path.exists():
            service = f"""[Unit]
                        Description=zap-poke listener
                        After=network.target

                        [Service]
                        ExecStart=/usr/bin/python3 {user_home}/.oh-my-zsh/custom/plugins/zap-poke/poke.py listen
                        Restart=on-failure

                        [Install]
                        WantedBy=default.target
                        """
            service_path.parent.mkdir(parents=True, exist_ok=True)
            service_path.write_text(service)
            os.system("systemctl --user daemon-reexec")
            os.system("systemctl --user enable zap-poke")
            os.system("systemctl --user start zap-poke")
            print("poke listener via systemd eingerichtet.")

    elif system == "Darwin":
        plist_path = Path(user_home) / "Library/LaunchAgents/com.zap.poke.plist"
        plist_dir = plist_path.parent
        plist_dir.mkdir(parents=True, exist_ok=True)

        plist = f"""<?xml version="1.0" encoding="UTF-8"?>
                <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" 
                "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                <plist version="1.0">
                <dict>
                <key>Label</key>
                <string>com.zap.poke</string>
                <key>ProgramArguments</key>
                <array>
                    <string>/usr/bin/python3</string>
                    <string>{user_home}/.oh-my-zsh/custom/plugins/zap-poke/poke.py</string>
                    <string>listen</string>
                </array>
                <key>RunAtLoad</key>
                <true/>
                </dict>
                </plist>
                """

        plist_path.write_text(plist)
        os.system(f"launchctl unload {plist_path} >/dev/null 2>&1") 
        os.system(f"launchctl load {plist_path}")
        print("poke listener via launchd eingerichtet.")


    elif system == "Windows":
        python = sys.executable.replace("\\", "\\\\")
        poke_path = os.path.abspath(__file__).replace("\\", "\\\\")
        vbs_path = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\zap-poke-listen.vbs")

        if not os.path.exists(vbs_path):
            with open(vbs_path, "w") as f:
                f.write(f'Set WshShell = CreateObject("WScript.Shell")\n')
                f.write(f'WshShell.Run chr(34) & "{python}" & chr(34) & " {poke_path} listen", 0\n')
            print("poke listener zum Windows-Autostart hinzugefügt.")
        else:
            print("poke listener ist bereits im Windows-Autostart registriert.")
    else:
        print("Autostart für dieses System nicht unterstützt.")

def cmd_add(name, ip):
    cfg = load_config()
    cfg["friends"][name] = ip
    save_config(cfg)
    print(f"Kontakt '{name}' hinzugefügt.")

def cmd_list():
    cfg = load_config()
    for name, ip in cfg["friends"].items():
        print(f"{name}: {ip}")

def cmd_remove(name):
    cfg = load_config()
    if name in cfg["friends"]:
        del cfg["friends"][name]
        save_config(cfg)
        print(f"'{name}' entfernt.")
    else:
        print("Kontakt nicht gefunden.")

def cmd_send(name, msg):
    cfg = load_config()
    ip = cfg["friends"].get(name)
    if not ip:
        print(f"Kontakt '{name}' nicht gefunden.")
        return
    try:
        with socket.create_connection((ip, PORT), timeout=5) as s:
            s.sendall(msg.encode())
        print(f"Nachricht an '{name}' gesendet.")
    except Exception as e:
        print(f"Fehler: {e}")

def show_message(msg, sender_ip):
    import shlex
    message = f"POKE von {sender_ip}:\n\n{msg}"
    system = platform.system()

    if system == "Linux":
        # Use shlex.quote for proper shell escaping
        escaped_message = shlex.quote(message)
        if shutil.which("gnome-terminal"):
            subprocess.Popen(f"gnome-terminal -- bash -c 'echo {escaped_message}; read -p \"Enter...\"'", shell=True)
        elif shutil.which("xterm"):
            subprocess.Popen(f"xterm -hold -e bash -c 'echo {escaped_message}'", shell=True)
        else:
            print(f"(Kein Terminal gefunden) Nachricht:\n{message}")
    elif system == "Darwin":
        # Escape quotes for AppleScript and shell
        escaped_message = shlex.quote(message)
        script = f'do script "echo {escaped_message}; read -n 1 -s"'
        subprocess.Popen(f'osascript -e \'tell application "Terminal" to {script}\'', shell=True)
    elif system == "Windows":
        # Escape quotes for PowerShell
        escaped_message = message.replace("'", "''").replace('"', '""')
        powershell_command = f'powershell -NoExit -Command "Write-Host \'{escaped_message}\'"'
        subprocess.Popen(f'start cmd /k "{powershell_command}"', shell=True)
    else:
        print(message)

def cmd_listen():
    def handler(conn, addr):
        msg = conn.recv(1024).decode()
        show_message(msg, addr[0])

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("0.0.0.0", PORT))
        s.listen()
        print(f"Warte auf Pokes auf Port {PORT}...")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handler, args=(conn, addr)).start()

def cmd_share():
    name = os.getenv("USER") or "anonymous"
    ip = os.popen("tailscale ip | head -n1").read().strip()
    print(json.dumps({"name": name, "ip": ip}))

def cmd_import(data):
    try:
        entry = json.loads(data)
        cmd_add(entry["name"], entry["ip"])
    except:
        print("Import fehlgeschlagen.")

def cmd_help():
    print("""
            poke - CLI Tool zum Senden von Pokes über Tailscale
            Verfügbare Befehle:

            poke init
                Initialisiert Konfiguration und aktiviert Autostart (plattformabhängig)

            poke listen
                Startet den Listener, der eingehende Nachrichten empfängt

            poke share
                Gibt deine Tailscale-IP + Benutzername als JSON-String aus

            poke import "kompletten output von poke share"
                Importiert einen Kontakt aus einem JSON-String

            poke add <name> <ip>
                Fügt einen Kontakt mit Name und IP hinzu

            poke list
                Zeigt alle gespeicherten Kontakte

            poke remove <name>
                Entfernt einen Kontakt aus der Liste

            poke send <name> <nachricht>
                Sendet eine Nachricht an den angegebenen Kontakt

            poke help  oder  poke -h
                Zeigt diese Hilfeübersicht an
            """)


def main():
    if len(sys.argv) == 1:
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]
    
    if cmd in ("-h", "help"):
        cmd_help()
        return

    try:
        if cmd == "init" and len(args) == 0:
            cmd_init()
        elif cmd == "add" and len(args) == 2:
            cmd_add(args[0], args[1])
        elif cmd == "list" and len(args) == 0:
            cmd_list()
        elif cmd == "remove" and len(args) == 1:
            cmd_remove(args[0])
        elif cmd == "send" and len(args) >= 2:
            cmd_send(args[0], " ".join(args[1:]))
        elif cmd == "listen" and len(args) == 0:
            cmd_listen()
        elif cmd == "share" and len(args) == 0:
            cmd_share()
        elif cmd == "import" and len(args) == 1:
            cmd_import(args[0])
        else:
            print("Unbekannter oder unvollständiger Befehl.")
    except Exception as e:
        print(f"Fehler: {e}")

if __name__ == "__main__":
    main()

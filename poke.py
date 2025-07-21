import os, sys, json, socket, threading

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
    print("zap-poke initialisiert.")

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

def cmd_listen():
    def handler(conn, addr):
        msg = conn.recv(1024).decode()
        print(f"\n*** POKE von {addr[0]} ***\n{msg}\n")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("0.0.0.0", PORT))
        s.listen()
        print(f"Warte auf Pokes auf Port {PORT}...")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handler, args=(conn, addr)).start()

def cmd_share():
    cfg = load_config()
    name = os.getenv("USER") or "anonymous"
    ip = os.popen("tailscale ip | head -n1").read().strip()
    print(json.dumps({"name": name, "ip": ip}))

def cmd_import(data):
    try:
        entry = json.loads(data)
        cmd_add(entry["name"], entry["ip"])
    except:
        print("Import fehlgeschlagen.")

def main():
    if len(sys.argv) < 2:
        print("Befehle: init, add, list, remove, send, listen, share, import")
        return
    cmd = sys.argv[1]
    args = sys.argv[2:]

    # Dictionary mapping commands to their handlers
    commands = {
        "init": lambda: cmd_init() if len(args) == 0 else None,
        "add": lambda: cmd_add(args[0], args[1]) if len(args) == 2 else None,
        "list": lambda: cmd_list() if len(args) == 0 else None,
        "remove": lambda: cmd_remove(args[0]) if len(args) == 1 else None,
        "send": lambda: cmd_send(args[0], " ".join(args[1:])) if len(args) >= 2 else None,
        "listen": lambda: cmd_listen() if len(args) == 0 else None,
        "share": lambda: cmd_share() if len(args) == 0 else None,
        "import": lambda: cmd_import(args[0]) if len(args) == 1 else None,
    }
    
    if cmd in commands:
        result = commands[cmd]()
        if result is None:  # Command exists but wrong number of args
            print("Unbekannter oder unvollständiger Befehl.")
    else:
        print("Unbekannter oder unvollständiger Befehl.")

if __name__ == "__main__":
    main()

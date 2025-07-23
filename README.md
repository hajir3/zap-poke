
# zap-poke

**zap-poke** ist ein minimalistisches CLI-Tool, mit dem du Freunden über das Terminal kleine Nachrichten („Pokes“) schicken kannst – direkt über eine Tailscale-Verbindung. Es ist als Plugin für Oh My Zsh nutzbar.

---

## 🔧 Voraussetzungen

- https://tailscale.com muss auf beiden Geräten installiert und verbunden sein.
- Oh My Zsh muss installiert sein.
- Die Geräte müssen über Tailscale erreichbar sein (z. B. 100.x.x.x IP).

---

## 🚀 Installation

git clone https://github.com/dein-user/zap-poke.git ~/.oh-my-zsh/custom/plugins/zap-poke

Dann in deiner ~/.zshrc:

plugins=(... zap-poke)
source ~/.zshrc

Jetzt ist der Befehl `poke` im Terminal verfügbar.

---

## 🛠️ Einrichtung (einmalig pro Gerät)

1. Tailscale installieren

   - Linux (Manjaro):sudo pacman -Sy tailscale
   - macOS:brew install tailscale
   - Windows:
     Lade den Installer von: https://tailscale.com/download
2. Tailscale starten und anmeldensudo tailscale up
3. zap-poke initialisierenpoke init
4. poke-Server starten (Nachrichten empfangen)
   poke listen

---

## 🤝 Verbindung mit einem Freund aufbauen

Variante A: Automatisch (empfohlen)

poke share

# gibt JSON aus, z. B.

Freund fügt dich hinzu:
poke import '{"name": "alice", "ip": "100.101.102.103"}'

Variante B: Manuell

poke add alice 100.101.102.103

---

## 💬 Befehle im Überblick

poke init                 -> Erstellt Konfigurationsdatei
poke add `<name>` `<ip>`     -> Kontakt hinzufügen
poke list                -> Alle Kontakte anzeigen
poke remove `<name>`       -> Kontakt entfernen
poke send `<name>` `<msg>`   -> Nachricht an Kontakt senden
poke listen              -> Empfangsserver starten (Nachrichten empfangen)
poke share               -> Eigene IP + Name als JSON ausgeben
poke import '`<json>`'     -> Kontakt aus JSON importieren

---

## 📌 Beispiel

poke add bob 100.105.104.103
poke send bob "Hey! Bist du da?"

---

## ⚠️ Hinweis

- poke listen muss auf dem Zielgerät laufen, damit Nachrichten empfangen werden.
- Nachrichten sind nicht verschlüsselt – nur über die sichere Tailscale-Verbindung geschützt.

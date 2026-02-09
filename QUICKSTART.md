# Control Center X Ultra - Quick Start Guide

## 🚀 Installation in 3 Schritten

### Schritt 1: Dateien auf VPS hochladen

```bash
# SSH Verbindung
ssh root@YOUR_VPS_IP

# Verzeichnis erstellen
mkdir -p /root/ccx-setup && cd /root/ccx-setup

# Dateien hochladen (von Ihrem PC mit SCP)
scp -r ticketbot-webpanel-main root@YOUR_VPS_IP:/root/ccx-setup/
```

### Schritt 2: Installation ausführen

```bash
cd /root/ccx-setup/ticketbot-webpanel-main/deployment

# Script ausführbar machen
chmod +x install_v2.sh post_install_setup.sh troubleshoot.sh

# Basis-Installation
bash install_v2.sh

# Post-Installation (kopiert Dateien, baut Frontend)
bash post_install_setup.sh
```

### Schritt 3: Konfigurieren & Testen

```bash
# 1. Discord Bot Token eintragen
nano /opt/ccx-ultra/web/.env
nano /opt/ccx-ultra/bot/config.env

# 2. Services neu starten
supervisorctl restart all

# 3. Testen
bash /opt/ccx-ultra/deployment/troubleshoot.sh
```

**Login:** https://ticket.armesa.de  
**Credentials:** admin / admin123

---

## ⚡ Schnelle Problembehebung

### Problem: "404 Not Found" beim Login

```bash
# 1. Backend Status prüfen
supervisorctl status

# 2. Backend neu starten
supervisorctl restart ccx-webpanel

# 3. Logs prüfen
tail -f /opt/ccx-ultra/logs/webpanel.err.log

# 4. Troubleshoot Script ausführen
bash /opt/ccx-ultra/deployment/troubleshoot.sh
```

### Problem: Services starten nicht

```bash
# Alle Logs ansehen
tail -f /opt/ccx-ultra/logs/*.log

# Dependencies installieren
source /opt/ccx-ultra/venv/bin/activate
pip install -r /opt/ccx-ultra/web/requirements.txt

# Services neu starten
supervisorctl restart all
```

---

## 📋 Wichtige Befehle

```bash
# Services verwalten
supervisorctl status
supervisorctl restart all
supervisorctl restart ccx-webpanel

# Logs ansehen
tail -f /opt/ccx-ultra/logs/webpanel.err.log
tail -f /opt/ccx-ultra/logs/bot.err.log

# System Check
/opt/ccx-ultra/healthcheck.sh

# Troubleshooting
bash /root/ccx-setup/ticketbot-webpanel-main/deployment/troubleshoot.sh

# Backup
/opt/ccx-ultra/backup.sh
```

---

## 📁 Verzeichnisstruktur

```
/opt/ccx-ultra/
├── web/
│   ├── server.py              # Backend Code
│   ├── .env                   # Backend Config
│   └── static/                # Frontend Build
├── bot/
│   ├── bot.py                 # Bot Code
│   └── config.env             # Bot Config
├── venv/                      # Python Virtual Environment
├── logs/                      # Service Logs
├── backups/                   # Automatische Backups
├── healthcheck.sh             # System Health Check
└── backup.sh                  # Backup Script
```

---

## 🔑 Discord Bot Setup

1. **Developer Portal:** https://discord.com/developers/applications
2. **Bot erstellen** → Token kopieren
3. **Privileged Intents aktivieren:**
   - ✅ PRESENCE INTENT
   - ✅ SERVER MEMBERS INTENT
   - ✅ MESSAGE CONTENT INTENT
4. **Bot einladen** mit Administrator Permission
5. **Discord IDs kopieren:**
   - Server ID (Rechtsklick auf Server → Copy ID)
   - Support Rollen IDs
   - Channel IDs für Tickets/Logs

---

## 🎯 Post-Installation Checklist

- [ ] Domain zeigt auf VPS (DNS A Record)
- [ ] SSL Zertifikat aktiv (https funktioniert)
- [ ] Services laufen (`supervisorctl status`)
- [ ] Backend API antwortet (`curl http://localhost:8001/api/health`)
- [ ] Frontend erreichbar (`https://ticket.armesa.de`)
- [ ] Login funktioniert (admin/admin123)
- [ ] Discord Bot Token konfiguriert
- [ ] Bot ist online im Discord Server
- [ ] Ticket Panel erstellt (`/ticket-panel` im Discord)

---

## 📞 Hilfe benötigt?

1. **Troubleshooting Script ausführen:**
   ```bash
   bash /root/ccx-setup/ticketbot-webpanel-main/deployment/troubleshoot.sh
   ```

2. **Vollständige Anleitung lesen:**
   ```bash
   cat /root/ccx-setup/ticketbot-webpanel-main/INSTALLATION_GUIDE.md
   ```

3. **Logs prüfen:**
   ```bash
   ls -lh /opt/ccx-ultra/logs/
   tail -f /opt/ccx-ultra/logs/webpanel.err.log
   ```

---

## 🔄 Updates

```bash
# Code aktualisieren
cd /root/ccx-setup/ticketbot-webpanel-main
# ... neue Dateien kopieren ...

# Backend aktualisieren
cp backend/server.py /opt/ccx-ultra/web/
supervisorctl restart ccx-webpanel

# Bot aktualisieren
cp bot/bot.py /opt/ccx-ultra/bot/
supervisorctl restart ccx-bot

# Frontend aktualisieren
cd frontend
yarn build
cp -r build/* /opt/ccx-ultra/web/static/
```

---

**Control Center X Ultra v2.0**  
Enterprise Discord Ticket System

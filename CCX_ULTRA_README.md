# Control Center X Ultra - Korrigiertes Installations-Paket

## 📦 Was ist enthalten?

Dieses Paket enthält eine **vollständig korrigierte Version** Ihres Discord Ticket Systems mit:

✅ **Verbessertes Installations-Script** (`install_v2.sh`)  
✅ **Automatisches Post-Installation Setup** (`post_install_setup.sh`)  
✅ **Troubleshooting Tool** (`troubleshoot.sh`)  
✅ **Vollständige Dokumentation** (INSTALLATION_GUIDE.md)  
✅ **Quick Start Guide** (QUICKSTART.md)

---

## 🐛 Behobene Probleme

### Hauptproblem: "404 Not Found" beim Login

**Ursache identifiziert:**
1. ❌ Backend läuft nicht oder auf falschem Port
2. ❌ Nginx Reverse Proxy leitet `/api/` nicht korrekt weiter
3. ❌ Frontend Build fehlt oder ist falsch konfiguriert
4. ❌ Fehlende oder falsche Konfiguration

**Lösung implementiert:**
1. ✅ Verbessertes Install-Script mit Status-Checks
2. ✅ Korrekte Nginx Konfiguration mit `/api/` Proxy
3. ✅ Automatisches Frontend Build & Deployment
4. ✅ Validierung aller Services vor Start
5. ✅ Umfassendes Troubleshooting Tool

---

## 🚀 Installation auf Ihrem VPS

### Download & Extraktion

```bash
# Auf Ihrem VPS
cd /root
mkdir ccx-setup && cd ccx-setup

# Datei hochladen (von Ihrem PC)
scp ccx-ultra-fixed-20260209.tar.gz root@YOUR_VPS_IP:/root/ccx-setup/

# Auf VPS extrahieren
tar -xzf ccx-ultra-fixed-20260209.tar.gz
cd ccx-fixed
```

### Schnell-Installation (3 Befehle)

```bash
# 1. Basis-Installation (10-15 Minuten)
cd deployment
bash install_v2.sh

# 2. Dateien kopieren & Frontend bauen (5-10 Minuten)
bash post_install_setup.sh

# 3. Konfiguration anpassen
nano /opt/ccx-ultra/web/.env          # Discord Bot Token eintragen
nano /opt/ccx-ultra/bot/config.env    # Discord Bot Token eintragen

# Services neu starten
supervisorctl restart all

# Testen
bash troubleshoot.sh
```

**Fertig!** Öffnen Sie: `https://ticket.armesa.de/login`

---

## 📋 Was die Scripts machen

### `install_v2.sh` - Basis-Installation
- ✅ System-Updates & Dependencies
- ✅ MongoDB 7.0 Installation
- ✅ Redis Installation
- ✅ Python Virtual Environment
- ✅ Nginx Konfiguration mit korrektem Reverse Proxy
- ✅ SSL Zertifikat (Certbot)
- ✅ Supervisor Services
- ✅ Firewall Setup
- ✅ Automatische Backups
- ✅ Health Check Script

### `post_install_setup.sh` - Dateien & Build
- ✅ Backend Dateien kopieren
- ✅ Bot Dateien kopieren
- ✅ Python Dependencies installieren
- ✅ Node.js & Yarn installieren
- ✅ Frontend bauen (yarn build)
- ✅ Frontend zu Nginx kopieren
- ✅ Services starten

### `troubleshoot.sh` - Problemdiagnose
- ✅ System Checks (Verzeichnisse, Dateien)
- ✅ Service Status (MongoDB, Redis, Nginx, Supervisor)
- ✅ Port Checks (8001, 27017, 80, 443)
- ✅ DNS & SSL Validierung
- ✅ Backend API Test
- ✅ Konfigurations-Validierung
- ✅ Log-Analyse
- ✅ Ressourcen-Übersicht
- ✅ Lösungsvorschläge für häufige Probleme

---

## 🔍 Fehlerbehebung

### Falls das Login immer noch nicht funktioniert:

```bash
# 1. Troubleshoot Script ausführen
cd /root/ccx-setup/ccx-fixed/deployment
bash troubleshoot.sh

# 2. Backend Logs prüfen
tail -f /opt/ccx-ultra/logs/webpanel.err.log

# 3. Backend manuell testen
cd /opt/ccx-ultra/web
source /opt/ccx-ultra/venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8001

# In neuem Terminal:
curl http://localhost:8001/api/health
# Sollte zurückgeben: {"status":"ok","service":"Control Center X Ultra"}

# 4. Nginx Test
nginx -t
systemctl status nginx

# 5. Services neu starten
supervisorctl restart all
```

### Häufigste Fehlerquellen:

1. **Backend läuft nicht:**
   ```bash
   supervisorctl status ccx-webpanel
   tail -f /opt/ccx-ultra/logs/webpanel.err.log
   ```

2. **Discord Bot Token fehlt:**
   ```bash
   grep DISCORD_BOT_TOKEN /opt/ccx-ultra/web/.env
   # Sollte NICHT "YOUR_BOT_TOKEN_HERE" sein
   ```

3. **Frontend nicht gebaut:**
   ```bash
   ls /opt/ccx-ultra/web/static/index.html
   # Sollte existieren
   ```

4. **Nginx leitet nicht weiter:**
   ```bash
   grep proxy_pass /etc/nginx/sites-enabled/ticket.armesa.de
   # Sollte sein: proxy_pass http://127.0.0.1:8001/api/;
   ```

---

## 📚 Dokumentation

Das Paket enthält umfassende Dokumentation:

- **QUICKSTART.md** - Schnellstart in 3 Schritten
- **INSTALLATION_GUIDE.md** - Vollständige Installations-Anleitung (11KB)
  - Detaillierte Schritt-für-Schritt Anleitung
  - Problemlösungen
  - Nützliche Befehle
  - Monitoring & Sicherheit
  
- **deployment/README.md** - Deployment-spezifische Infos

---

## 🎯 Nach der Installation

### 1. System testen

```bash
# Health Check
/opt/ccx-ultra/healthcheck.sh

# API Test
curl http://localhost:8001/api/health

# Browser Test
https://ticket.armesa.de/login
```

### 2. Erstes Login

**URL:** https://ticket.armesa.de/login  
**Username:** `admin`  
**Password:** `admin123`

⚠️ **WICHTIG:** Passwort nach dem ersten Login ändern!

### 3. Discord Bot aktivieren

```bash
# Nach Konfiguration von config.env:
supervisorctl start ccx-bot

# Status prüfen
supervisorctl status ccx-bot
tail -f /opt/ccx-ultra/logs/bot.err.log
```

### 4. Ticket Panel erstellen

Im Discord Server den Slash Command ausführen:
```
/ticket-panel
```

---

## 📊 Service Übersicht

Nach erfolgreicher Installation:

| Service | Port | Status Command | Log Location |
|---------|------|----------------|--------------|
| MongoDB | 27017 | `systemctl status mongod` | `/var/log/mongodb/` |
| Redis | 6379 | `systemctl status redis-server` | `/var/log/redis/` |
| Nginx | 80, 443 | `systemctl status nginx` | `/var/log/nginx/` |
| Backend | 8001 | `supervisorctl status ccx-webpanel` | `/opt/ccx-ultra/logs/webpanel.*` |
| Bot | - | `supervisorctl status ccx-bot` | `/opt/ccx-ultra/logs/bot.*` |

---

## 🔐 Sicherheit

Das Setup enthält:

✅ UFW Firewall (nur SSH, HTTP, HTTPS)  
✅ SSL/HTTPS mit Let's Encrypt  
✅ Security Headers in Nginx  
✅ Rate Limiting  
✅ JWT Token Authentication  
✅ Bcrypt Password Hashing  
✅ Automatische Backups (täglich 03:00 Uhr)

---

## 🆘 Support

### Bei Problemen:

1. **Troubleshoot Script ausführen:**
   ```bash
   bash /root/ccx-setup/ccx-fixed/deployment/troubleshoot.sh
   ```

2. **Logs prüfen:**
   ```bash
   tail -f /opt/ccx-ultra/logs/*.log
   ```

3. **System Status:**
   ```bash
   /opt/ccx-ultra/healthcheck.sh
   ```

4. **Services neu starten:**
   ```bash
   supervisorctl restart all
   ```

### Wichtige Dateien:

- Konfiguration: `/opt/ccx-ultra/web/.env`
- Bot Config: `/opt/ccx-ultra/bot/config.env`
- Nginx Config: `/etc/nginx/sites-available/ticket.armesa.de`
- Supervisor: `/etc/supervisor/conf.d/ccx-*.conf`
- Logs: `/opt/ccx-ultra/logs/`

---

## ✨ Neue Features in dieser Version

- 🔧 Automatische Systemprüfung vor Installation
- 🚀 Post-Installation Script für automatisches Setup
- 🔍 Umfassendes Troubleshooting Tool
- 📊 Health Check Script
- 💾 Automatisches Backup System
- 📝 Erweiterte Logging & Fehlerdiagnose
- ⚡ Bessere Fehlerbehandlung in allen Scripts
- 📚 Vollständige deutsche Dokumentation

---

## 📞 Weitere Hilfe

Alle Anleitungen sind enthalten:

```bash
# Quick Start (kurz)
cat QUICKSTART.md

# Vollständige Anleitung (detailliert)
cat INSTALLATION_GUIDE.md

# Deployment Details
cat deployment/README.md
```

---

**Control Center X Ultra v2.0**  
*Enterprise Discord Ticket System - Korrigierte Version*  

✅ Problem identifiziert  
✅ Lösung implementiert  
✅ Umfassend getestet  
✅ Vollständig dokumentiert  

Viel Erfolg bei der Installation! 🚀

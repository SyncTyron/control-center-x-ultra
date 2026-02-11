# 🚀 Deployment Guide - Control Center X Ultra Updates

## 📁 Datei-Mapping (Von `/app` zu Ihrem Server)

### **Bot-Dateien:**
```
/app/bot/bot.py  →  /opt/ccx-ultra/bot/bot.py
```

### **Backend-Dateien:**
```
/app/web/server.py  →  /opt/ccx-ultra/web/server.py
```

### **Frontend-Dateien:**
```
/app/frontend/src/components/TicketDetail.js  →  /opt/ccx-ultra-source/frontend/src/components/TicketDetail.js
/app/frontend/src/styles/TicketDetail.css     →  /opt/ccx-ultra-source/frontend/src/styles/TicketDetail.css
/app/frontend/src/components/TicketList.js    →  /opt/ccx-ultra-source/frontend/src/components/TicketList.js
/app/frontend/src/styles/TicketList.css       →  /opt/ccx-ultra-source/frontend/src/styles/TicketList.css
```

---

## ✨ **Was wurde geändert:**

### **Bot (bot.py):**
1. ✅ Modal öffnet sich automatisch nach Prioritäts-Auswahl (kein "Continue" Button mehr)
2. ✅ Channel-Namen: `{sprache}-ticket-{priorität}-{nummer}` (z.B. `de-ticket-high-0001`)
3. ✅ Bot-Antworten löschen sich nach 10 Sekunden automatisch
4. ✅ Close Button löscht Discord-Channel nach 5 Sekunden
5. ✅ Alle Ticket-Nachrichten werden in DB gespeichert für Live-Chat

### **Backend (server.py):**
1. ✅ `/bot/event` Endpoint aktualisiert `claimed_by` und `status` in DB
2. ✅ `/bot/message` Endpoint speichert Discord-Nachrichten
3. ✅ `/api/tickets/{id}/messages` Endpoint für Live-Chat

### **Frontend (TicketDetail.js + .css):**
1. ✅ Live-Chat zeigt Discord-Nachrichten in Ticket-Detail-Ansicht
2. ✅ "Angenommen von" Badge in Ticket-Header
3. ✅ Auto-Refresh alle 5 Sekunden für neue Nachrichten

### **Frontend (TicketList.js + .css):**
1. ✅ "Angenommen von" wird in Ticket-Liste angezeigt

---

## 🔄 **Deployment-Schritte auf Ihrem VPS:**

### **1. Services stoppen**
```bash
sudo supervisorctl stop ccx-bot ccx-webpanel
```

### **2. Backup erstellen**
```bash
cp /opt/ccx-ultra/bot/bot.py /opt/ccx-ultra/bot/bot.py.backup
cp /opt/ccx-ultra/web/server.py /opt/ccx-ultra/web/server.py.backup
```

### **3. Neue Dateien hochladen**
Laden Sie die Dateien von `/app` via Git oder SFTP hoch und ersetzen Sie:
- `/opt/ccx-ultra/bot/bot.py`
- `/opt/ccx-ultra/web/server.py`
- Frontend-Dateien in `/opt/ccx-ultra-source/frontend/src/`

### **4. Frontend neu builden**
```bash
cd /opt/ccx-ultra-source/frontend
yarn build
cp -r build/* /opt/ccx-ultra/web/static/
```

### **5. Services neu starten**
```bash
sudo supervisorctl start ccx-webpanel
sleep 3
sudo supervisorctl start ccx-bot
```

### **6. Status prüfen**
```bash
sudo supervisorctl status
tail -30 /opt/ccx-ultra/logs/bot.err.log
tail -20 /opt/ccx-ultra/logs/webpanel.err.log
```

---

## ✅ **Testing-Checkliste:**

### **Discord:**
- [ ] `/ticket-panel` funktioniert
- [ ] Priorität-Dropdown → Modal öffnet sich automatisch
- [ ] Channel-Name: `de-ticket-high-0001` Format
- [ ] "Claim" Button funktioniert
- [ ] "Close" Button löscht Channel nach 5 Sekunden
- [ ] Nachrichten im Ticket werden gespeichert

### **Web-Panel:**
- [ ] Tickets werden angezeigt
- [ ] Ticket-Detail zeigt Live-Chat
- [ ] "Angenommen von" Badge sichtbar
- [ ] Support Stats zeigt Daten

---

## 🆘 **Bei Problemen:**

```bash
# Bot-Logs
tail -50 /opt/ccx-ultra/logs/bot.err.log

# Backend-Logs
tail -50 /opt/ccx-ultra/logs/webpanel.err.log

# Services neu starten
sudo supervisorctl restart ccx-bot ccx-webpanel
```

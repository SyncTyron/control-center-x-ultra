from fastapi import FastAPI, APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
import json
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security: JWT_SECRET must be set in environment - no fallback for production
JWT_SECRET = os.environ.get('JWT_SECRET')
if not JWT_SECRET:
    raise ValueError("JWT_SECRET environment variable is required!")

DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN', '')
SUPPORT_ROLE_IDS = os.environ.get('SUPPORT_ROLE_IDS', '').split(',')

app = FastAPI()
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# SSE event queues
sse_clients: list = []

# --- Pydantic Models ---
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str
    user: dict

class TicketUpdate(BaseModel):
    notes: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None

class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str = "viewer"

class BotTicketCreate(BaseModel):
    channel_id: str
    guild_id: str
    user_id: str
    username: str
    subject: str
    type: str = "general"
    lang: str = "de"
    priority: str = "medium"
    description: str = ""

class BotEventCreate(BaseModel):
    event_type: str
    data: dict

# --- Auth Helpers ---
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, username: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(request: Request) -> dict:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = auth.split(" ", 1)[1]
    return decode_token(token)

async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin required")
    return user

async def require_support(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") not in ("admin", "support"):
        raise HTTPException(status_code=403, detail="Support role required")
    return user

# --- SSE Helper ---
async def push_event(event_type: str, data: dict):
    event_data = {
        "id": str(uuid.uuid4()),
        "event_type": event_type,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.live_events.insert_one({**event_data})
    dead = []
    for q in sse_clients:
        try:
            await q.put(event_data)
        except Exception:
            dead.append(q)
    for q in dead:
        sse_clients.remove(q)

async def audit_log(action: str, user: str, target_ticket: str = None, details: str = ""):
    doc = {
        "id": str(uuid.uuid4()),
        "action": action,
        "user": user,
        "target_ticket": target_ticket,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.audit_log.insert_one(doc)

# --- Auth Routes ---
@api_router.post("/auth/login")
async def login(req: LoginRequest):
    user = await db.panel_users.find_one({"username": req.username}, {"_id": 0})
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(user["id"], user["username"], user["role"])
    await audit_log("login", user["username"])
    return {
        "token": token,
        "user": {"id": user["id"], "username": user["username"], "role": user["role"]}
    }

@api_router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    db_user = await db.panel_users.find_one({"id": user["sub"]}, {"_id": 0, "password_hash": 0})
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# --- KPI Route ---
@api_router.get("/kpi")
async def get_kpi(user: dict = Depends(get_current_user)):
    total = await db.tickets.count_documents({})
    open_count = await db.tickets.count_documents({"status": {"$in": ["open", "claimed", "escalated"]}})
    closed_today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0).isoformat()
    closed_today = await db.tickets.count_documents({"status": "closed", "closed_at": {"$gte": closed_today_start}})
    escalated = await db.tickets.count_documents({"status": "escalated"})
    sla_breached = await db.tickets.count_documents({"sla_breached": True, "status": {"$ne": "closed"}})

    pipeline = [
        {"$match": {"first_response_at": {"$ne": None}, "claimed_at": {"$ne": None}}},
        {"$project": {"response_minutes": {"$divide": [{"$subtract": [{"$toDate": "$first_response_at"}, {"$toDate": "$claimed_at"}]}, 60000]}}},
        {"$group": {"_id": None, "avg": {"$avg": "$response_minutes"}}}
    ]
    avg_response = await db.tickets.aggregate(pipeline).to_list(1)
    avg_resp_time = round(avg_response[0]["avg"], 1) if avg_response and avg_response[0].get("avg") else 0

    return {
        "total_tickets": total,
        "open_tickets": open_count,
        "closed_today": closed_today,
        "escalated": escalated,
        "sla_breached": sla_breached,
        "avg_response_time_min": avg_resp_time
    }

# --- Ticket Routes ---
@api_router.get("/tickets")
async def get_tickets(
    user: dict = Depends(get_current_user),
    status: Optional[str] = None,
    priority: Optional[str] = None,
    lang: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    page: int = 1,
    limit: int = 50
):
    query = {}
    if status:
        query["status"] = status
    if priority:
        query["priority"] = priority
    if lang:
        query["lang"] = lang
    if search:
        query["$or"] = [
            {"subject": {"$regex": search, "$options": "i"}},
            {"username": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"id": {"$regex": search, "$options": "i"}}
        ]

    sort_dir = -1 if sort_order == "desc" else 1
    skip = (page - 1) * limit
    total = await db.tickets.count_documents(query)
    tickets = await db.tickets.find(query, {"_id": 0}).sort(sort_by, sort_dir).skip(skip).limit(limit).to_list(limit)
    return {"tickets": tickets, "total": total, "page": page, "pages": (total + limit - 1) // limit if limit else 1}

@api_router.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str, user: dict = Depends(get_current_user)):
    ticket = await db.tickets.find_one({"id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    messages = await db.ticket_messages.find({"ticket_id": ticket_id}, {"_id": 0}).sort("timestamp", 1).to_list(500)
    return {"ticket": ticket, "messages": messages}

@api_router.put("/tickets/{ticket_id}/claim")
async def claim_ticket(ticket_id: str, user: dict = Depends(require_support)):
    ticket = await db.tickets.find_one({"id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if ticket.get("claimed_by") and ticket["status"] == "claimed":
        raise HTTPException(status_code=400, detail="Already claimed")
    now = datetime.now(timezone.utc).isoformat()
    await db.tickets.update_one({"id": ticket_id}, {"$set": {
        "claimed_by": user["username"],
        "claimed_at": now,
        "status": "claimed",
        "first_response_at": now if not ticket.get("first_response_at") else ticket["first_response_at"]
    }})
    await audit_log("ticket_claim", user["username"], ticket_id)
    await push_event("ticket_claim", {"ticket_id": ticket_id, "claimed_by": user["username"], "subject": ticket.get("subject", "")})
    return {"status": "claimed", "claimed_by": user["username"]}

@api_router.put("/tickets/{ticket_id}/close")
async def close_ticket(ticket_id: str, user: dict = Depends(require_support)):
    ticket = await db.tickets.find_one({"id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    now = datetime.now(timezone.utc).isoformat()
    await db.tickets.update_one({"id": ticket_id}, {"$set": {
        "status": "closed",
        "closed_at": now,
        "closed_by": user["username"]
    }})
    await audit_log("ticket_close", user["username"], ticket_id)
    await push_event("ticket_close", {"ticket_id": ticket_id, "closed_by": user["username"], "subject": ticket.get("subject", "")})
    return {"status": "closed"}

@api_router.put("/tickets/{ticket_id}/reopen")
async def reopen_ticket(ticket_id: str, user: dict = Depends(require_support)):
    ticket = await db.tickets.find_one({"id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    await db.tickets.update_one({"id": ticket_id}, {"$set": {
        "status": "open",
        "closed_at": None,
        "closed_by": None
    }})
    await audit_log("ticket_reopen", user["username"], ticket_id)
    return {"status": "reopened"}

@api_router.put("/tickets/{ticket_id}/notes")
async def update_notes(ticket_id: str, update: TicketUpdate, user: dict = Depends(require_support)):
    ticket = await db.tickets.find_one({"id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    set_fields = {}
    if update.notes is not None:
        set_fields["notes"] = update.notes
    if update.priority is not None:
        set_fields["priority"] = update.priority
    if update.status is not None:
        set_fields["status"] = update.status
    if set_fields:
        await db.tickets.update_one({"id": ticket_id}, {"$set": set_fields})
        await audit_log("ticket_update", user["username"], ticket_id, json.dumps(set_fields))
        if update.notes is not None:
            await push_event("notes_update", {"ticket_id": ticket_id, "user": user["username"]})
    return {"status": "updated"}

@api_router.put("/tickets/{ticket_id}/escalate")
async def escalate_ticket(ticket_id: str, user: dict = Depends(require_support)):
    ticket = await db.tickets.find_one({"id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    await db.tickets.update_one({"id": ticket_id}, {"$set": {
        "status": "escalated",
        "escalation_flag": True,
        "priority": "critical"
    }})
    await audit_log("ticket_escalate", user["username"], ticket_id)
    await push_event("escalation", {"ticket_id": ticket_id, "escalated_by": user["username"], "subject": ticket.get("subject", "")})
    return {"status": "escalated"}

# --- Search Route ---
@api_router.get("/search")
async def search_tickets(q: str = Query(""), user: dict = Depends(get_current_user)):
    if not q:
        return {"results": []}
    query = {"$or": [
        {"subject": {"$regex": q, "$options": "i"}},
        {"username": {"$regex": q, "$options": "i"}},
        {"description": {"$regex": q, "$options": "i"}},
        {"id": {"$regex": q, "$options": "i"}}
    ]}
    results = await db.tickets.find(query, {"_id": 0}).limit(20).to_list(20)
    return {"results": results}

# --- Support Stats ---
@api_router.get("/support_stats")
async def get_support_stats(user: dict = Depends(get_current_user)):
    pipeline = [
        {"$match": {"claimed_by": {"$ne": None}}},
        {"$group": {
            "_id": "$claimed_by",
            "total_tickets": {"$sum": 1},
            "closed_tickets": {"$sum": {"$cond": [{"$eq": ["$status", "closed"]}, 1, 0]}},
            "escalations": {"$sum": {"$cond": [{"$eq": ["$escalation_flag", True]}, 1, 0]}},
            "sla_breaches": {"$sum": {"$cond": [{"$eq": ["$sla_breached", True]}, 1, 0]}},
        }}
    ]
    stats = await db.tickets.aggregate(pipeline).to_list(100)
    result = []
    for s in stats:
        score = max(0, 100 - (s["escalations"] * 10) - (s["sla_breaches"] * 15))
        result.append({
            "supporter": s["_id"],
            "total_tickets": s["total_tickets"],
            "closed_tickets": s["closed_tickets"],
            "escalations": s["escalations"],
            "sla_breaches": s["sla_breaches"],
            "score": score
        })
    result.sort(key=lambda x: x["score"], reverse=True)
    return {"stats": result}

# --- SLA Route ---
@api_router.get("/sla")
async def get_sla(user: dict = Depends(get_current_user)):
    total = await db.tickets.count_documents({})
    breached = await db.tickets.count_documents({"sla_breached": True})
    compliance = round(((total - breached) / total * 100), 1) if total > 0 else 100
    pipeline_by_priority = [
        {"$group": {
            "_id": "$priority",
            "total": {"$sum": 1},
            "breached": {"$sum": {"$cond": [{"$eq": ["$sla_breached", True]}, 1, 0]}}
        }}
    ]
    by_priority = await db.tickets.aggregate(pipeline_by_priority).to_list(10)
    priority_data = {}
    for p in by_priority:
        t = p["total"]
        b = p["breached"]
        priority_data[p["_id"]] = {"total": t, "breached": b, "compliance": round(((t - b) / t * 100), 1) if t > 0 else 100}
    pipeline_by_day = [
        {"$group": {
            "_id": {"$substr": ["$created_at", 0, 10]},
            "total": {"$sum": 1},
            "breached": {"$sum": {"$cond": [{"$eq": ["$sla_breached", True]}, 1, 0]}}
        }},
        {"$sort": {"_id": 1}},
        {"$limit": 30}
    ]
    by_day = await db.tickets.aggregate(pipeline_by_day).to_list(30)
    daily = [{"date": d["_id"], "total": d["total"], "breached": d["breached"]} for d in by_day]
    return {"compliance": compliance, "total": total, "breached": breached, "by_priority": priority_data, "daily": daily}

# --- SSE Events ---
@api_router.get("/events")
async def sse_stream(request: Request):
    queue = asyncio.Queue()
    sse_clients.append(queue)

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'event_type': 'heartbeat', 'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"
        finally:
            if queue in sse_clients:
                sse_clients.remove(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no"
    })

# --- Recent Events (for initial load) ---
@api_router.get("/recent_events")
async def get_recent_events(user: dict = Depends(get_current_user)):
    events = await db.live_events.find({}, {"_id": 0}).sort("timestamp", -1).limit(50).to_list(50)
    return {"events": events}

# --- Bot Webhook Routes ---
@api_router.post("/bot/ticket")
async def bot_create_ticket(ticket: BotTicketCreate, request: Request):
    bot_token = request.headers.get("X-Bot-Token", "")
    if bot_token != DISCORD_BOT_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid bot token")
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": str(uuid.uuid4()),
        "channel_id": ticket.channel_id,
        "guild_id": ticket.guild_id,
        "user_id": ticket.user_id,
        "username": ticket.username,
        "subject": ticket.subject,
        "type": ticket.type,
        "lang": ticket.lang,
        "priority": ticket.priority,
        "description": ticket.description,
        "status": "open",
        "created_at": now,
        "claimed_by": None,
        "claimed_at": None,
        "first_response_at": None,
        "closed_at": None,
        "closed_by": None,
        "notes": "",
        "escalation_flag": False,
        "sla_breached": False,
        "transcript_path": None
    }
    await db.tickets.insert_one(doc)
    del doc["_id"]
    await push_event("ticket_open", {"ticket_id": doc["id"], "username": ticket.username, "subject": ticket.subject, "priority": ticket.priority})
    await audit_log("ticket_create", f"bot:{ticket.username}", doc["id"], f"Subject: {ticket.subject}")
    return {"ticket_id": doc["id"], "status": "created"}

@api_router.post("/bot/event")
async def bot_push_event(event: BotEventCreate, request: Request):
    bot_token = request.headers.get("X-Bot-Token", "")
    if bot_token != DISCORD_BOT_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid bot token")
    await push_event(event.event_type, event.data)
    return {"status": "ok"}

# --- Audit Log ---
@api_router.get("/audit_log")
async def get_audit_log(user: dict = Depends(get_current_user), page: int = 1, limit: int = 100):
    skip = (page - 1) * limit
    total = await db.audit_log.count_documents({})
    logs = await db.audit_log.find({}, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
    return {"logs": logs, "total": total}

# --- Admin Routes ---
@api_router.get("/admin/users")
async def list_users(user: dict = Depends(require_admin)):
    users = await db.panel_users.find({}, {"_id": 0, "password_hash": 0}).to_list(100)
    return {"users": users}

@api_router.post("/admin/users")
async def create_user(req: CreateUserRequest, user: dict = Depends(require_admin)):
    existing = await db.panel_users.find_one({"username": req.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    doc = {
        "id": str(uuid.uuid4()),
        "username": req.username,
        "password_hash": hash_password(req.password),
        "role": req.role,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.panel_users.insert_one(doc)
    await audit_log("user_create", user["username"], details=f"Created user: {req.username} ({req.role})")
    return {"id": doc["id"], "username": req.username, "role": req.role}

@api_router.delete("/admin/users/{user_id}")
async def delete_user(user_id: str, user: dict = Depends(require_admin)):
    result = await db.panel_users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    await audit_log("user_delete", user["username"], details=f"Deleted user: {user_id}")
    return {"status": "deleted"}

# --- Analytics: Tickets per day for charts ---
@api_router.get("/analytics/volume")
async def get_volume(user: dict = Depends(get_current_user), days: int = 30):
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    pipeline = [
        {"$match": {"created_at": {"$gte": cutoff}}},
        {"$group": {
            "_id": {"$substr": ["$created_at", 0, 10]},
            "opened": {"$sum": 1},
            "closed": {"$sum": {"$cond": [{"$eq": ["$status", "closed"]}, 1, 0]}}
        }},
        {"$sort": {"_id": 1}}
    ]
    data = await db.tickets.aggregate(pipeline).to_list(60)
    return {"volume": [{"date": d["_id"], "opened": d["opened"], "closed": d["closed"]} for d in data]}

@api_router.get("/analytics/priority_distribution")
async def get_priority_dist(user: dict = Depends(get_current_user)):
    pipeline = [
        {"$group": {"_id": "$priority", "count": {"$sum": 1}}}
    ]
    data = await db.tickets.aggregate(pipeline).to_list(10)
    return {"distribution": [{"priority": d["_id"], "count": d["count"]} for d in data]}

@api_router.get("/analytics/type_distribution")
async def get_type_dist(user: dict = Depends(get_current_user)):
    pipeline = [
        {"$group": {"_id": "$type", "count": {"$sum": 1}}}
    ]
    data = await db.tickets.aggregate(pipeline).to_list(20)
    return {"distribution": [{"type": d["_id"], "count": d["count"]} for d in data]}

# --- Health ---
@api_router.get("/health")
async def health():
    return {"status": "ok", "service": "Control Center X Ultra"}

# --- PDF Download ---
@api_router.get("/docs/download")
async def download_docs():
    pdf_path = ROOT_DIR / "static" / "ccx-ultra-anleitung.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(
        path=str(pdf_path),
        filename="CCX-Ultra-Anleitung.pdf",
        media_type="application/pdf"
    )

# --- Include Router ---
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Startup: Seed Data ---
@app.on_event("startup")
async def startup():
    # Create indexes
    await db.tickets.create_index("id", unique=True)
    await db.tickets.create_index("status")
    await db.tickets.create_index("priority")
    await db.tickets.create_index("created_at")
    await db.panel_users.create_index("username", unique=True)
    await db.audit_log.create_index("timestamp")
    await db.live_events.create_index("timestamp")

    # Create default admin if not exists
    admin = await db.panel_users.find_one({"username": "admin"})
    if not admin:
        try:
            await db.panel_users.insert_one({
                "id": str(uuid.uuid4()),
                "username": "admin",
                "password_hash": hash_password("admin123"),
                "role": "admin",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info("Default admin user created (admin/admin123)")

    # Seed demo tickets if empty
    count = await db.tickets.count_documents({})
    if count == 0:
        await seed_demo_data()
        logger.info("Demo data seeded")

async def seed_demo_data():
    import random
    types = ["general", "technical", "billing", "bug_report", "feature_request"]
    priorities = ["low", "medium", "high", "critical"]
    subjects_de = [
        "Server Verbindungsproblem", "Rolle fehlt nach Update", "Bot reagiert nicht",
        "Berechtigungen falsch konfiguriert", "Channel nicht sichtbar",
        "Voice Chat Probleme", "Emoji Upload fehlgeschlagen", "Webhook Fehler",
        "Auto-Mod zu aggressiv", "Willkommensnachricht fehlt",
        "Ranking System defekt", "Musikbot spielt nicht", "Backup anfordern",
        "Neuen Channel beantragen", "Spam Bot melden",
        "Nitro Booster Rolle fehlt", "Event Planung Hilfe", "API Zugang anfordern"
    ]
    subjects_en = [
        "Cannot join voice channel", "Missing permissions after update",
        "Bot not responding to commands", "Role sync issue",
        "Channel visibility problem", "Webhook integration broken",
        "Auto-moderation false positive", "Welcome message not sending",
        "Leveling system bug", "Music bot audio glitch",
        "Request server backup", "New channel request", "Report spam bot",
        "Nitro booster role missing", "Event planning help", "API access request"
    ]
    supporters = ["ModeratorMax", "SupportSara", "AdminAlex", "HelperHanna", None, None]
    statuses = ["open", "claimed", "closed", "escalated"]

    now = datetime.now(timezone.utc)
    tickets = []
    for i in range(45):
        lang = random.choice(["de", "en"])
        subjects = subjects_de if lang == "de" else subjects_en
        status = random.choices(statuses, weights=[25, 20, 45, 10])[0]
        priority = random.choice(priorities)
        supporter = random.choice(supporters) if status != "open" else None
        created = now - timedelta(days=random.randint(0, 29), hours=random.randint(0, 23), minutes=random.randint(0, 59))
        created_str = created.isoformat()
        claimed_at = (created + timedelta(minutes=random.randint(2, 120))).isoformat() if supporter else None
        first_resp = (created + timedelta(minutes=random.randint(3, 180))).isoformat() if supporter else None
        closed_at = (created + timedelta(hours=random.randint(1, 72))).isoformat() if status == "closed" else None

        tickets.append({
            "id": str(uuid.uuid4()),
            "channel_id": f"ticket-{1000 + i}",
            "guild_id": "1407623359365120090",
            "user_id": str(random.randint(100000000000000000, 999999999999999999)),
            "username": random.choice(["UserAlpha", "BetaTester", "GammaGamer", "DeltaDev", "EpsilonEng", "ZetaZone", "EtaEdit", "ThetaTech"]),
            "subject": random.choice(subjects),
            "type": random.choice(types),
            "lang": lang,
            "priority": priority,
            "description": f"Demo ticket description #{i+1}",
            "status": status,
            "created_at": created_str,
            "claimed_by": supporter,
            "claimed_at": claimed_at,
            "first_response_at": first_resp,
            "closed_at": closed_at,
            "closed_by": supporter if status == "closed" else None,
            "notes": random.choice(["", "", "", "Needs follow-up", "Waiting for user response", "Escalated to senior"]),
            "escalation_flag": status == "escalated",
            "sla_breached": random.random() < 0.15,
            "transcript_path": None
        })

    if tickets:
        await db.tickets.insert_many(tickets)

    # Seed some events
    event_types = ["ticket_open", "ticket_claim", "ticket_close", "escalation"]
    events = []
    for i in range(20):
        events.append({
            "id": str(uuid.uuid4()),
            "event_type": random.choice(event_types),
            "data": {"ticket_id": tickets[i % len(tickets)]["id"], "username": tickets[i % len(tickets)]["username"], "subject": tickets[i % len(tickets)]["subject"]},
            "timestamp": (now - timedelta(minutes=random.randint(1, 600))).isoformat()
        })
    if events:
        await db.live_events.insert_many(events)

    # Create demo support user
    await db.panel_users.insert_one({
        "id": str(uuid.uuid4()),
        "username": "support",
        "password_hash": hash_password("support123"),
        "role": "support",
        "created_at": datetime.now(timezone.utc).isoformat()
    })

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

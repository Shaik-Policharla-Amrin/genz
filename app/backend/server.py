from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
from passlib.context import CryptContext
from emergentintegrations.llm.chat import LlmChat, UserMessage
import json
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

JWT_SECRET = os.environ.get('JWT_SECRET')
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
JWT_EXPIRATION = int(os.environ.get('JWT_EXPIRATION_HOURS', 24))
EMERGENT_KEY = os.environ.get('EMERGENT_LLM_KEY')

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    name: str
    created_at: str

class Task(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    status: str = "pending"
    due_date: Optional[str] = None
    created_at: str

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[str] = None

class Note(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    title: str
    content: str
    created_at: str
    updated_at: str

class NoteCreate(BaseModel):
    title: str
    content: str

class Event(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    title: str
    description: Optional[str] = None
    start_time: str
    end_time: str
    created_at: str

class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: str
    end_time: str

class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    agent_used: str
    actions_taken: List[str] = []

class AgentLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    agent_type: str
    action: str
    result: str
    timestamp: str

def create_token(user_id: str, email: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@api_router.get("/")
async def root():
    return {"message": "GenZ AI Multi-Agent System", "status": "online"}

@api_router.post("/auth/register")
async def register(user: UserRegister):
    existing = await db.users.find_one({"email": user.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    hashed_pw = pwd_context.hash(user.password)
    user_doc = {
        "id": user_id,
        "email": user.email,
        "password_hash": hashed_pw,
        "name": user.name,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    
    token = create_token(user_id, user.email)
    return {"token": token, "user": {"id": user_id, "email": user.email, "name": user.name}}

@api_router.post("/auth/login")
async def login(user: UserLogin):
    user_doc = await db.users.find_one({"email": user.email}, {"_id": 0})
    if not user_doc or not pwd_context.verify(user.password, user_doc["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user_doc["id"], user_doc["email"])
    return {"token": token, "user": {"id": user_doc["id"], "email": user_doc["email"], "name": user_doc["name"]}}

@api_router.get("/tasks", response_model=List[Task])
async def get_tasks(user_id: str = Depends(get_current_user)):
    tasks = await db.tasks.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    return tasks

@api_router.post("/tasks", response_model=Task)
async def create_task(task: TaskCreate, user_id: str = Depends(get_current_user)):
    task_id = str(uuid.uuid4())
    priority = await detect_priority(task.title, task.description or "")
    task_doc = {
        "id": task_id,
        "user_id": user_id,
        "title": task.title,
        "description": task.description,
        "priority": priority,
        "status": "pending",
        "due_date": task.due_date,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.tasks.insert_one(task_doc)
    return task_doc

@api_router.patch("/tasks/{task_id}")
async def update_task(task_id: str, updates: Dict[str, Any], user_id: str = Depends(get_current_user)):
    result = await db.tasks.update_one(
        {"id": task_id, "user_id": user_id},
        {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True}

@api_router.delete("/tasks/{task_id}")
async def delete_task(task_id: str, user_id: str = Depends(get_current_user)):
    result = await db.tasks.delete_one({"id": task_id, "user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True}

@api_router.get("/notes", response_model=List[Note])
async def get_notes(user_id: str = Depends(get_current_user)):
    notes = await db.notes.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    return notes

@api_router.post("/notes", response_model=Note)
async def create_note(note: NoteCreate, user_id: str = Depends(get_current_user)):
    note_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    note_doc = {
        "id": note_id,
        "user_id": user_id,
        "title": note.title,
        "content": note.content,
        "created_at": now,
        "updated_at": now
    }
    await db.notes.insert_one(note_doc)
    return note_doc

@api_router.patch("/notes/{note_id}")
async def update_note(note_id: str, updates: Dict[str, Any], user_id: str = Depends(get_current_user)):
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.notes.update_one(
        {"id": note_id, "user_id": user_id},
        {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"success": True}

@api_router.delete("/notes/{note_id}")
async def delete_note(note_id: str, user_id: str = Depends(get_current_user)):
    result = await db.notes.delete_one({"id": note_id, "user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"success": True}

@api_router.get("/events", response_model=List[Event])
async def get_events(user_id: str = Depends(get_current_user)):
    events = await db.events.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    return events

@api_router.post("/events", response_model=Event)
async def create_event(event: EventCreate, user_id: str = Depends(get_current_user)):
    event_id = str(uuid.uuid4())
    event_doc = {
        "id": event_id,
        "user_id": user_id,
        "title": event.title,
        "description": event.description,
        "start_time": event.start_time,
        "end_time": event.end_time,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.events.insert_one(event_doc)
    return event_doc

@api_router.delete("/events/{event_id}")
async def delete_event(event_id: str, user_id: str = Depends(get_current_user)):
    result = await db.events.delete_one({"id": event_id, "user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"success": True}

@api_router.get("/agent-logs", response_model=List[AgentLog])
async def get_agent_logs(user_id: str = Depends(get_current_user)):
    logs = await db.agent_logs.find({"user_id": user_id}, {"_id": 0}).sort("timestamp", -1).limit(50).to_list(50)
    return logs

async def log_agent_activity(user_id: str, agent_type: str, action: str, result: str):
    log_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "agent_type": agent_type,
        "action": action,
        "result": result,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.agent_logs.insert_one(log_doc)

async def detect_priority(title: str, description: str) -> str:
    urgent_keywords = ["urgent", "asap", "critical", "important", "deadline", "emergency"]
    low_keywords = ["someday", "maybe", "later", "optional", "nice to have"]
    
    text = (title + " " + description).lower()
    
    if any(word in text for word in urgent_keywords):
        return "high"
    elif any(word in text for word in low_keywords):
        return "low"
    return "medium"

async def task_agent(user_id: str, query: str) -> Dict[str, Any]:
    tasks = await db.tasks.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    
    chat = LlmChat(
        api_key=EMERGENT_KEY,
        session_id=f"task_agent_{user_id}",
        system_message="You are a task management agent. Analyze tasks and provide insights about priorities, overdue items, and suggestions."
    ).with_model("openai", "gpt-4o")
    
    context = f"User has {len(tasks)} tasks. Tasks: {json.dumps(tasks[:10])}"
    message = UserMessage(text=f"{context}\n\nUser query: {query}")
    response = await chat.send_message(message)
    
    await log_agent_activity(user_id, "task_agent", query, response)
    return {"response": response, "tasks_analyzed": len(tasks)}

async def schedule_agent(user_id: str, query: str) -> Dict[str, Any]:
    events = await db.events.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    tasks = await db.tasks.find({"user_id": user_id, "status": "pending"}, {"_id": 0}).to_list(100)
    
    chat = LlmChat(
        api_key=EMERGENT_KEY,
        session_id=f"schedule_agent_{user_id}",
        system_message="You are a scheduling and daily planning agent. Create daily plans, suggest time blocks, and provide reminders."
    ).with_model("openai", "gpt-4o")
    
    context = f"User has {len(events)} events and {len(tasks)} pending tasks. Events: {json.dumps(events[:5])}. Tasks: {json.dumps(tasks[:5])}"
    message = UserMessage(text=f"{context}\n\nUser query: {query}")
    response = await chat.send_message(message)
    
    await log_agent_activity(user_id, "schedule_agent", query, response)
    return {"response": response, "events_count": len(events)}

async def notes_agent(user_id: str, query: str) -> Dict[str, Any]:
    notes = await db.notes.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    
    chat = LlmChat(
        api_key=EMERGENT_KEY,
        session_id=f"notes_agent_{user_id}",
        system_message="You are a notes analysis agent. Summarize notes, extract key insights, and help organize information."
    ).with_model("openai", "gpt-4o")
    
    context = f"User has {len(notes)} notes. Notes: {json.dumps(notes[:10])}"
    message = UserMessage(text=f"{context}\n\nUser query: {query}")
    response = await chat.send_message(message)
    
    await log_agent_activity(user_id, "notes_agent", query, response)
    return {"response": response, "notes_count": len(notes)}

async def coordinator_agent(user_id: str, user_query: str) -> ChatResponse:
    query_lower = user_query.lower()
    actions = []
    
    if any(word in query_lower for word in ["task", "todo", "priority", "deadline"]):
        result = await task_agent(user_id, user_query)
        actions.append("task_agent")
        return ChatResponse(response=result["response"], agent_used="task_agent", actions_taken=actions)
    
    elif any(word in query_lower for word in ["schedule", "calendar", "event", "plan", "reminder", "daily", "today", "tomorrow"]):
        result = await schedule_agent(user_id, user_query)
        actions.append("schedule_agent")
        return ChatResponse(response=result["response"], agent_used="schedule_agent", actions_taken=actions)
    
    elif any(word in query_lower for word in ["note", "summarize", "summary", "information"]):
        result = await notes_agent(user_id, user_query)
        actions.append("notes_agent")
        return ChatResponse(response=result["response"], agent_used="notes_agent", actions_taken=actions)
    
    elif "next" in query_lower or "should i do" in query_lower:
        tasks = await db.tasks.find({"user_id": user_id, "status": "pending"}, {"_id": 0}).sort("created_at", 1).to_list(100)
        events = await db.events.find({"user_id": user_id}, {"_id": 0}).to_list(100)
        
        chat = LlmChat(
            api_key=EMERGENT_KEY,
            session_id=f"coordinator_{user_id}",
            system_message="You are a productivity coordinator. Help users decide what to work on next based on their tasks and schedule."
        ).with_model("openai", "gpt-4o")
        
        context = f"Tasks: {json.dumps(tasks[:10])}. Events: {json.dumps(events[:5])}"
        message = UserMessage(text=f"{context}\n\nUser query: {user_query}")
        response = await chat.send_message(message)
        
        await log_agent_activity(user_id, "coordinator_agent", user_query, response)
        actions.append("coordinator_agent")
        return ChatResponse(response=response, agent_used="coordinator_agent", actions_taken=actions)
    
    else:
        chat = LlmChat(
            api_key=EMERGENT_KEY,
            session_id=f"general_{user_id}",
            system_message="You are a helpful AI assistant for productivity and task management."
        ).with_model("openai", "gpt-4o")
        
        message = UserMessage(text=user_query)
        response = await chat.send_message(message)
        
        await log_agent_activity(user_id, "general_agent", user_query, response)
        return ChatResponse(response=response, agent_used="general_agent", actions_taken=["general_agent"])

@api_router.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage, user_id: str = Depends(get_current_user)):
    response = await coordinator_agent(user_id, message.message)
    return response

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
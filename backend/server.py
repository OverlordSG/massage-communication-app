from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import json
import uuid
import os
from datetime import datetime
import asyncio
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI(title="Massage Communication API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/massage_app")
client = AsyncIOMotorClient(MONGO_URL)
db = client.massage_app

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str, user_type: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = {}
        self.active_connections[session_id][user_type] = websocket
        
    def disconnect(self, session_id: str, user_type: str):
        if session_id in self.active_connections:
            self.active_connections[session_id].pop(user_type, None)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
    
    async def send_personal_message(self, message: str, session_id: str, user_type: str):
        if session_id in self.active_connections and user_type in self.active_connections[session_id]:
            await self.active_connections[session_id][user_type].send_text(message)
    
    async def broadcast_to_session(self, message: str, session_id: str, exclude_user: str = None):
        if session_id in self.active_connections:
            for user_type, websocket in self.active_connections[session_id].items():
                if user_type != exclude_user:
                    await websocket.send_text(message)

manager = ConnectionManager()

# Pydantic models
class Session(BaseModel):
    client_name: str
    
class SessionResponse(BaseModel):
    id: str
    client_name: str
    pressure: str = "medium"
    speed: str = "medium"
    depth: str = "medium"
    focus_zones: List[str] = []
    ignore_zones: List[str] = []
    created_at: datetime
    updated_at: datetime

class Preferences(BaseModel):
    pressure: Optional[str] = None
    speed: Optional[str] = None
    depth: Optional[str] = None
    focus_zones: Optional[List[str]] = None
    ignore_zones: Optional[List[str]] = None

class LiveFeedback(BaseModel):
    type: str
    zone: Optional[str] = None
    message: Optional[str] = None

@app.get("/")
async def root():
    return {"message": "Massage Communication API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.post("/api/sessions", response_model=SessionResponse)
async def create_session(session: Session):
    session_id = str(uuid.uuid4())
    session_data = {
        "id": session_id,
        "client_name": session.client_name,
        "pressure": "medium",
        "speed": "medium", 
        "depth": "medium",
        "focus_zones": [],
        "ignore_zones": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    await db.sessions.insert_one(session_data)
    return SessionResponse(**session_data)

@app.get("/api/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    session = await db.sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse(**session)

@app.put("/api/sessions/{session_id}/preferences")
async def update_preferences(session_id: str, preferences: Preferences):
    session = await db.sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    update_data = {"updated_at": datetime.utcnow()}
    if preferences.pressure is not None:
        update_data["pressure"] = preferences.pressure
    if preferences.speed is not None:
        update_data["speed"] = preferences.speed
    if preferences.depth is not None:
        update_data["depth"] = preferences.depth
    if preferences.focus_zones is not None:
        update_data["focus_zones"] = preferences.focus_zones
    if preferences.ignore_zones is not None:
        update_data["ignore_zones"] = preferences.ignore_zones
    
    await db.sessions.update_one({"id": session_id}, {"$set": update_data})
    
    # Broadcast update to all connected users
    await manager.broadcast_to_session(
        json.dumps({"type": "preferences_updated", "data": update_data}),
        session_id
    )
    
    return {"message": "Preferences updated successfully"}

@app.websocket("/api/ws/{session_id}/{user_type}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, user_type: str):
    await manager.connect(websocket, session_id, user_type)
    
    # Send initial session data
    try:
        session = await db.sessions.find_one({"id": session_id})
        if session:
            session["_id"] = str(session["_id"])
            await manager.send_personal_message(
                json.dumps({"type": "session_data", "data": session}),
                session_id,
                user_type
            )
    except Exception as e:
        print(f"Error sending initial data: {e}")
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "live_feedback":
                # Broadcast feedback to other users
                await manager.broadcast_to_session(
                    json.dumps(message),
                    session_id,
                    exclude_user=user_type
                )
            elif message.get("type") == "preferences_update":
                # Update preferences in database
                await db.sessions.update_one(
                    {"id": session_id},
                    {"$set": {**message.get("data", {}), "updated_at": datetime.utcnow()}}
                )
                # Broadcast to other users
                await manager.broadcast_to_session(
                    json.dumps(message),
                    session_id,
                    exclude_user=user_type
                )
            else:
                # Broadcast any other message
                await manager.broadcast_to_session(
                    json.dumps(message),
                    session_id,
                    exclude_user=user_type
                )
                
    except WebSocketDisconnect:
        manager.disconnect(session_id, user_type)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(session_id, user_type)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

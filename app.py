import os
import json
import uuid
import base64
import asyncio
import re
from pathlib import Path
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, HTTPException, Request, Response, UploadFile, File, Form
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import database
import ai_service
import web_search_service
import subprocess
import threading
import requests

def auto_start_ollama_if_needed():
    """Ensures Ollama is running in background without requiring user intervention."""
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=1)
        if r.status_code == 200:
            return
    except Exception:
        pass

    candidates = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe",
        Path("C:/Program Files/Ollama/ollama.exe"),
        "ollama"
    ]
    for c in candidates:
        try:
            if isinstance(c, Path) and not c.exists():
                continue
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
            subprocess.Popen([str(c), "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags)
            break
        except Exception:
            continue

try:
    threading.Thread(target=auto_start_ollama_if_needed, daemon=True).start()
except Exception:
    pass

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
UPLOADS_DIR = STATIC_DIR / "uploads"
AVATARS_DIR = UPLOADS_DIR / "avatars"
CHAT_DIR = UPLOADS_DIR / "chat"

AVATARS_DIR.mkdir(parents=True, exist_ok=True)
CHAT_DIR.mkdir(parents=True, exist_ok=True)

# Initialize database
database.init_db()

app = FastAPI(title="CharAI Local", description="Character.ai clone with image upload and multimodal vision support")

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def root():
    return FileResponse(STATIC_DIR / "index.html")

# Pydantic schemas
class RegisterRequest(BaseModel):
    username: str
    password: str
    display_name: Optional[str] = ""

class LoginRequest(BaseModel):
    username: str
    password: str

class ProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    avatar: Optional[str] = None
    new_password: Optional[str] = None

class CharacterCreate(BaseModel):
    id: Optional[str] = None
    name: str
    title: Optional[str] = ""
    tagline: Optional[str] = ""
    greeting: Optional[str] = ""
    persona: Optional[str] = ""
    example_dialogue: Optional[str] = ""
    avatar: Optional[str] = "/static/avatars/default.svg"
    is_nsfw: Optional[int] = 0

class ProfileSearchRequest(BaseModel):
    query: str

class CreateChatRequest(BaseModel):
    title: Optional[str] = None
    include_greeting: Optional[bool] = True

class SendMessageRequest(BaseModel):
    content: str
    image_url: Optional[str] = ""

class MessageEditRequest(BaseModel):
    content: str

class SwipeRequest(BaseModel):
    index: int

class SyncMessagesRequest(BaseModel):
    messages: List[Dict[str, Any]]

class SettingsUpdate(BaseModel):
    settings: Dict[str, Any]

class Base64UploadRequest(BaseModel):
    data: str
    category: Optional[str] = "chat"
    filename: Optional[str] = "image.png"

# Auth Helper
def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    auth = request.headers.get("Authorization", "")
    token = None
    if auth.startswith("Bearer "):
        token = auth[7:].strip()
    elif "charai_token" in request.cookies:
        token = request.cookies.get("charai_token")
    if token:
        return database.get_user_by_token(token)
    return None

# Auth Endpoints
@app.post("/api/auth/register")
def register(req: RegisterRequest, response: Response):
    try:
        user = database.create_user(req.username, req.password, display_name=req.display_name or "")
        token = database.create_session(user["id"])
        response.set_cookie(key="charai_token", value=token, httponly=False, samesite="lax", max_age=86400 * 30)
        return {"status": "ok", "token": token, "user": user}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/login")
def login(req: LoginRequest, response: Response):
    user = database.verify_user(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Benutzername oder Passwort ist falsch.")
    token = database.create_session(user["id"])
    response.set_cookie(key="charai_token", value=token, httponly=False, samesite="lax", max_age=86400 * 30)
    return {"status": "ok", "token": token, "user": user}

@app.post("/api/auth/logout")
def logout(request: Request, response: Response):
    auth = request.headers.get("Authorization", "")
    token = None
    if auth.startswith("Bearer "):
        token = auth[7:].strip()
    elif "charai_token" in request.cookies:
        token = request.cookies.get("charai_token")
    if token:
        database.delete_session(token)
    response.delete_cookie(key="charai_token")
    return {"status": "logged_out"}

@app.get("/api/auth/me")
def get_me(request: Request):
    user = get_current_user(request)
    return {"user": user}

@app.put("/api/auth/profile")
def update_profile(req: ProfileUpdateRequest, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Nicht angemeldet")
    updated = database.update_user_profile(
        user["id"],
        display_name=req.display_name,
        avatar=req.avatar,
        new_password=req.new_password
    )
    return {"status": "ok", "user": updated}

# Image Upload Endpoints (Multipart & Base64)
@app.post("/api/upload/file")
async def upload_file_multipart(file: UploadFile = File(...), category: str = Form("chat")):
    target_dir = AVATARS_DIR if category == "avatar" else CHAT_DIR
    ext = Path(file.filename or "image.png").suffix.lower()
    if not ext or ext not in (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"):
        ext = ".png"

    filename = f"{uuid.uuid4()}{ext}"
    dest = target_dir / filename

    content = await file.read()
    dest.write_bytes(content)

    rel_sub = "avatars" if category == "avatar" else "chat"
    return {"url": f"/static/uploads/{rel_sub}/{filename}"}

@app.post("/api/upload")
async def upload_file_base64(req: Base64UploadRequest):
    data_str = req.data
    target_dir = AVATARS_DIR if req.category == "avatar" else CHAT_DIR

    # Parse data:image/png;base64,...
    ext = ".png"
    if "data:" in data_str and ";base64," in data_str:
        header, b64_body = data_str.split(";base64,", 1)
        mime = header.split("data:")[1].lower()
        if "jpeg" in mime or "jpg" in mime: ext = ".jpg"
        elif "webp" in mime: ext = ".webp"
        elif "gif" in mime: ext = ".gif"
        elif "svg" in mime: ext = ".svg"
    else:
        b64_body = data_str

    try:
        raw_bytes = base64.b64decode(b64_body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 payload: {e}")

    filename = f"{uuid.uuid4()}{ext}"
    dest = target_dir / filename
    dest.write_bytes(raw_bytes)

    rel_sub = "avatars" if req.category == "avatar" else "chat"
    return {"url": f"/static/uploads/{rel_sub}/{filename}"}

# Search & Auto-Profile Endpoint
@app.post("/api/characters/search-profile")
def search_profile(req: ProfileSearchRequest, request: Request):
    q = req.query.strip()
    if not q:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    user = get_current_user(request)
    user_id = user["id"] if user else None
    settings = database.get_all_settings(user_id=user_id)
    profile = web_search_service.auto_generate_character_profile(q, settings)
    return profile

# Character endpoints
@app.get("/api/characters")
def list_characters(request: Request):
    user = get_current_user(request)
    user_id = user["id"] if user else None
    return database.get_all_characters(user_id=user_id)

@app.get("/api/characters/{char_id}")
def get_character(char_id: str):
    char = database.get_character_by_id(char_id)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    return char

@app.post("/api/characters")
def create_or_update_character(char: CharacterCreate, request: Request):
    user = get_current_user(request)
    user_id = user["id"] if user else None
    saved = database.save_character(char.model_dump(), user_id=user_id)
    return saved

@app.delete("/api/characters")
def delete_all_characters(request: Request):
    user = get_current_user(request)
    user_id = user["id"] if user else None
    database.delete_all_characters(user_id=user_id)
    return {"status": "all_characters_deleted"}

@app.delete("/api/characters/{char_id}")
def delete_character(char_id: str):
    success = database.delete_character(char_id)
    if not success:
        raise HTTPException(status_code=404, detail="Character not found")
    return {"status": "deleted"}

@app.get("/api/characters/{char_id}/export")
def export_character(char_id: str):
    char = database.get_character_by_id(char_id)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    
    card = {
        "spec": "chara_card_v2",
        "spec_version": "2.0",
        "data": {
            "name": char["name"],
            "description": char.get("persona", ""),
            "personality": char.get("title", ""),
            "scenario": char.get("tagline", ""),
            "first_mes": char.get("greeting", ""),
            "mes_example": char.get("example_dialogue", ""),
            "avatar": char.get("avatar", ""),
            "is_nsfw": bool(char.get("is_nsfw")),
            "creator_notes": "Exported from CharAI Local"
        }
    }
    safe_name = "".join(c for c in char["name"].lower().replace(" ", "_") if c.isalnum() or c == "_")
    return JSONResponse(
        content=card,
        headers={"Content-Disposition": f'attachment; filename="{safe_name}.json"'}
    )

@app.post("/api/characters/import")
async def import_character(req: Request):
    try:
        data = await req.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON format")

    if "data" in data and isinstance(data["data"], dict):
        inner = data["data"]
        char_data = {
            "name": inner.get("name", "Neuer Charakter"),
            "title": inner.get("personality", ""),
            "tagline": inner.get("scenario", "")[:120],
            "persona": inner.get("description", ""),
            "greeting": inner.get("first_mes", "Hallo!"),
            "example_dialogue": inner.get("mes_example", ""),
            "avatar": inner.get("avatar") or "/static/avatars/default.svg",
            "is_nsfw": 1 if inner.get("is_nsfw") else 0
        }
    else:
        char_data = {
            "name": data.get("name", "Neuer Charakter"),
            "title": data.get("title", ""),
            "tagline": data.get("tagline", ""),
            "persona": data.get("persona", data.get("description", "")),
            "greeting": data.get("greeting", data.get("first_mes", "Hallo!")),
            "example_dialogue": data.get("example_dialogue", data.get("mes_example", "")),
            "avatar": data.get("avatar", "/static/avatars/default.svg"),
            "is_nsfw": 1 if data.get("is_nsfw") else 0
        }

    user = get_current_user(req)
    user_id = user["id"] if user else None
    saved = database.save_character(char_data, user_id=user_id)
    return saved

# Chat session endpoints
@app.get("/api/characters/{char_id}/chats")
def list_chats(char_id: str, request: Request):
    user = get_current_user(request)
    user_id = user["id"] if user else None
    return database.get_chats_for_character(char_id, user_id=user_id)

@app.get("/api/characters/{char_id}/active-chat")
def get_active_chat(char_id: str, request: Request):
    user = get_current_user(request)
    user_id = user["id"] if user else None
    return database.get_or_create_active_chat(char_id, user_id=user_id)

@app.post("/api/characters/{char_id}/chats")
def create_chat(char_id: str, request: Request, req: Optional[CreateChatRequest] = None):
    title = req.title if req else None
    include_greeting = req.include_greeting if req and req.include_greeting is not None else True
    user = get_current_user(request)
    user_id = user["id"] if user else None
    return database.create_new_chat(char_id, title=title, include_greeting=include_greeting, user_id=user_id)

@app.delete("/api/chats/{chat_id}")
def delete_chat(chat_id: str, request: Request):
    user = get_current_user(request)
    user_id = user["id"] if user else None
    chat = database.get_chat_by_id(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    if chat.get("user_id") and chat["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Keine Berechtigung zum Löschen dieses Chats.")
    success = database.delete_chat(chat_id)
    return {"status": "deleted"}

@app.get("/api/chats/{chat_id}/messages")
def list_messages(chat_id: str, request: Request):
    user = get_current_user(request)
    user_id = user["id"] if user else None
    chat = database.get_chat_by_id(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    if chat.get("user_id") and chat["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Kein Zugriff auf diesen privaten Chat.")
    return database.get_messages(chat_id)

@app.post("/api/chats/{chat_id}/sync")
def sync_chat_messages(chat_id: str, req: SyncMessagesRequest, request: Request):
    user = get_current_user(request)
    user_id = user["id"] if user else None
    chat = database.get_chat_by_id(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    if chat.get("user_id") and chat["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Kein Zugriff auf diesen privaten Chat.")
    count = database.sync_messages(chat_id, req.messages)
    return {"status": "synced", "inserted": count}

def clean_ai_text(text: str, char_name: str = "") -> str:
    cleaned = text.strip()
    cleaned = re.sub(r'^(?:assistant|AI)\s*[:\n\-]+\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'^(?:assistant|AI)\b\s*', '', cleaned, flags=re.IGNORECASE)
    if char_name:
        cleaned = re.sub(rf'^{re.escape(char_name)}\s*[:\n\-]+\s*', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(rf'^{re.escape(char_name)}\b\s*', '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()

# Chat stream endpoints
@app.post("/api/chats/{chat_id}/message")
def send_message(chat_id: str, payload: SendMessageRequest, request: Request):
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chats WHERE id = ?", (chat_id,))
    chat = cursor.fetchone()
    conn.close()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    user = get_current_user(request)
    user_id = user["id"] if user else None
    if chat["user_id"] and chat["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Kein Zugriff auf diesen privaten Chat.")

    character = database.get_character_by_id(chat["character_id"])
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    user_text = payload.content.strip()
    image_url = payload.image_url.strip() if payload.image_url else ""

    if not user_text and not image_url:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    user_msg = database.add_message(chat_id, "user", user_text, image_url=image_url)
    history = database.get_messages(chat_id)
    settings = database.get_all_settings(user_id=user_id)

    def event_stream():
        full_content = []
        try:
            for chunk in ai_service.stream_ai_response(character, history, settings):
                full_content.append(chunk)
                data_json = json.dumps({"type": "chunk", "content": chunk})
                yield f"data: {data_json}\n\n"
        except Exception as e:
            err_data = json.dumps({"type": "error", "content": str(e)})
            yield f"data: {err_data}\n\n"

        complete_text = "".join(full_content).strip()
        try:
            complete_text = clean_ai_text(complete_text, character.get("name", ""))
        except Exception:
            pass
        if not complete_text:
            complete_text = "*(Schweigt für einen Moment und lächelt verlegen)*"

        assistant_msg = database.add_message(chat_id, "assistant", complete_text, alternatives=[complete_text])
        done_json = json.dumps({
            "type": "done",
            "message": assistant_msg
        })
        yield f"data: {done_json}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.post("/api/chats/{chat_id}/continue")
def continue_chat(chat_id: str, request: Request):
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chats WHERE id = ?", (chat_id,))
    chat = cursor.fetchone()
    conn.close()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    user = get_current_user(request)
    user_id = user["id"] if user else None
    if chat["user_id"] and chat["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Kein Zugriff auf diesen privaten Chat.")

    character = database.get_character_by_id(chat["character_id"])
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    history = database.get_messages(chat_id)
    settings = database.get_all_settings(user_id=user_id)

    def event_stream():
        full_content = []
        try:
            for chunk in ai_service.stream_ai_continuation_response(character, history, settings):
                full_content.append(chunk)
                data_json = json.dumps({"type": "chunk", "content": chunk})
                yield f"data: {data_json}\n\n"
        except Exception as e:
            err_data = json.dumps({"type": "error", "content": str(e)})
            yield f"data: {err_data}\n\n"

        complete_text = "".join(full_content).strip()
        try:
            complete_text = clean_ai_text(complete_text, character.get("name", ""))
        except Exception:
            pass
        if not complete_text:
            complete_text = "*(Blickt dich mit ruhiger Neugier an und wartet ab)*"

        assistant_msg = database.add_message(chat_id, "assistant", complete_text, alternatives=[complete_text])
        done_json = json.dumps({
            "type": "done",
            "message": assistant_msg
        })
        yield f"data: {done_json}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.post("/api/chats/{chat_id}/regenerate")
def regenerate_response(chat_id: str, request: Request):
    messages = database.get_messages(chat_id)
    if not messages:
        raise HTTPException(status_code=400, detail="No messages to regenerate")

    last_msg = messages[-1]
    if last_msg["role"] != "assistant":
        raise HTTPException(status_code=400, detail="Last message is not from assistant")

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chats WHERE id = ?", (chat_id,))
    chat = cursor.fetchone()
    conn.close()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    user = get_current_user(request)
    user_id = user["id"] if user else None
    if chat["user_id"] and chat["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Kein Zugriff auf diesen privaten Chat.")

    character = database.get_character_by_id(chat["character_id"])
    settings = database.get_all_settings(user_id=user_id)
    history_without_last = messages[:-1]

    def event_stream():
        full_content = []
        try:
            for chunk in ai_service.stream_ai_response(character, history_without_last, settings, temperature=0.92):
                full_content.append(chunk)
                data_json = json.dumps({"type": "chunk", "content": chunk})
                yield f"data: {data_json}\n\n"
        except Exception as e:
            err_data = json.dumps({"type": "error", "content": str(e)})
            yield f"data: {err_data}\n\n"

        complete_text = "".join(full_content).strip()
        try:
            complete_text = clean_ai_text(complete_text, character.get("name", ""))
        except Exception:
            pass
        if not complete_text:
            complete_text = "*(Überlegt noch einmal gründlich nach)*"

        updated_msg = database.update_message_alternative(last_msg["id"], complete_text)
        done_json = json.dumps({
            "type": "done",
            "message": updated_msg
        })
        yield f"data: {done_json}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.post("/api/messages/{msg_id}/swipe")
def swipe_message(msg_id: str, req: SwipeRequest):
    try:
        updated = database.set_message_swipe_index(msg_id, req.index)
        return updated
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.put("/api/messages/{msg_id}")
def edit_message(msg_id: str, req: MessageEditRequest):
    try:
        updated = database.edit_message(msg_id, req.content)
        return updated
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.delete("/api/messages/{msg_id}")
def delete_message(msg_id: str):
    database.delete_message(msg_id)
    return {"status": "deleted"}

# Settings endpoints
@app.get("/api/settings")
def get_settings(request: Request):
    user = get_current_user(request)
    user_id = user["id"] if user else None
    return database.get_all_settings(user_id=user_id)

@app.post("/api/settings")
def update_settings(payload: SettingsUpdate, request: Request):
    user = get_current_user(request)
    user_id = user["id"] if user else None
    database.update_settings(payload.settings, user_id=user_id)
    return {"status": "saved", "settings": database.get_all_settings(user_id=user_id)}

if __name__ == "__main__":
    import uvicorn
    import webbrowser
    import threading

    port = int(os.environ.get("PORT", 8000))

    def open_browser():
        import time
        time.sleep(1.2)
        try:
            if "PORT" not in os.environ:
                webbrowser.open(f"http://127.0.0.1:{port}")
        except Exception:
            pass

    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)

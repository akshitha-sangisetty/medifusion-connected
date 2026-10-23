"""
app/socket_manager.py
Centralised Socket.IO server instance used by main.py and route handlers.
"""
import socketio
from app.api.auth.routes import get_user_from_token
from app.config import ALLOWED_ORIGINS
from app.core.database import SessionLocal

# Async Socket.IO server (ASGI-compatible)
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=ALLOWED_ORIGINS,
    logger=False,
    engineio_logger=False,
)


# ─────────────────────────────────────────
# Connection / Disconnection events
# ─────────────────────────────────────────
@sio.event
async def connect(sid, environ, auth):
    token = auth.get("token") if isinstance(auth, dict) else None
    if not token:
        raise ConnectionRefusedError("Authentication required")

    db = SessionLocal()
    try:
        user = get_user_from_token(token, db)
        await sio.save_session(sid, {"username": user.username, "role": user.role})
    except Exception:
        raise ConnectionRefusedError("Invalid authentication token")
    finally:
        db.close()


@sio.event
async def disconnect(sid):
    print(f"[Socket.IO] Client disconnected: {sid}")


# ─────────────────────────────────────────
# Room Management
# Patient calls this after login so they
# receive events targeted at their username.
# ─────────────────────────────────────────
@sio.event
async def join_patient_room(sid, data):
    """
    data = {"username": "harry"}
    Puts the socket into a room named after the patient
    so the doctor endpoint can emit directly to them.
    """
    session = await sio.get_session(sid)
    if not session or session.get("role") != "patient":
        return

    username = session["username"]
    await sio.enter_room(sid, f"patient_{username}")
    await sio.emit("room_joined", {"room": f"patient_{username}"}, to=sid)


@sio.event
async def join_doctor_room(sid, data):
    """
    data = {"doctor_id": 1}
    All doctors share a common room so the system can broadcast
    a new-case notification to every online doctor.
    """
    session = await sio.get_session(sid)
    if not session or session.get("role") != "doctor":
        return

    await sio.enter_room(sid, "doctors")
    await sio.emit("room_joined", {"room": "doctors"}, to=sid)

"""
app/socket_manager.py
Centralised Socket.IO server instance used by main.py and route handlers.
"""
import socketio

# Async Socket.IO server (ASGI-compatible)
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=False,
    engineio_logger=False,
)


# ─────────────────────────────────────────
# Connection / Disconnection events
# ─────────────────────────────────────────
@sio.event
async def connect(sid, environ, auth):
    print(f"[Socket.IO] Client connected: {sid}")


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
    username = data.get("username", "")
    if username:
        await sio.enter_room(sid, f"patient_{username}")
        await sio.emit("room_joined", {"room": f"patient_{username}"}, to=sid)
        print(f"[Socket.IO] {sid} joined room: patient_{username}")


@sio.event
async def join_doctor_room(sid, data):
    """
    data = {"doctor_id": 1}
    All doctors share a common room so the system can broadcast
    a new-case notification to every online doctor.
    """
    await sio.enter_room(sid, "doctors")
    await sio.emit("room_joined", {"room": "doctors"}, to=sid)
    print(f"[Socket.IO] {sid} joined doctors room")

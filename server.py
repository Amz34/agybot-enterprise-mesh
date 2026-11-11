"""
AgyBot Mesh - Unified FastAPI Gateway Server
Serves the mobile & desktop PWA, handles WebSocket screencast & voice,
and processes command executions directly on the host VM.
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from config import PORT, HOST, STATIC_DIR
from exec_engine import ExecutionEngine
from agy_agent import AgyGeminiAgent
from browser_engine import BrowserScreencastEngine
from voice_engine import VoiceEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AgyBotGateway")

app = FastAPI(title="AgyBot Sovereign Gateway", version="1.0.0")

# Mount Static Files (PWA, Assets, Manifest)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Subsystems
exec_engine = ExecutionEngine()
agy_agent = AgyGeminiAgent()
browser_engine = BrowserScreencastEngine()
voice_engine = VoiceEngine()

# Connected WebSocket Clients
connected_websockets = set()

@app.get("/", response_class=HTMLResponse)
async def serve_pwa_index():
    index_file = STATIC_DIR / "index.html"
    with open(index_file, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/api/health")
async def health_check():
    return {
        "status": "HEALTHY",
        "service": "AgyBot Sovereign Gateway",
        "connected_clients": len(connected_websockets),
        "telemetry": exec_engine.get_system_telemetry()
    }

@app.get("/api/telemetry")
async def get_telemetry():
    return exec_engine.get_system_telemetry()

@app.post("/api/exec")
async def execute_command(payload: Dict[str, Any]):
    cmd = payload.get("command", "")
    if not cmd:
        return JSONResponse({"error": "No command provided"}, status_code=400)
    result = await exec_engine.run_bash(cmd)
    return result

@app.post("/api/chat")
async def chat_endpoint(payload: Dict[str, Any]):
    msg = payload.get("message", "")
    context = exec_engine.get_system_telemetry()
    agent_res = await agy_agent.chat(msg, context=context)

    command_result = None
    if agent_res.get("suggested_commands"):
        # Auto-execute primary command
        primary_cmd = agent_res["suggested_commands"][0]
        command_result = await exec_engine.run_bash(primary_cmd)

    return {
        "response": agent_res["response"],
        "model": agent_res["model"],
        "command_result": command_result
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_websockets.add(websocket)
    session_id = f"sess_{id(websocket)}"
    voice_session = voice_engine.create_session(session_id, "PWA-WebRTC-WS")
    logger.info(f"Client connected to WebSocket: {session_id}")

    # Launch background screencast frame pusher
    async def push_screencast():
        try:
            while websocket in connected_websockets:
                frame_b64 = browser_engine.generate_simulated_frame()
                await websocket.send_text(json.dumps({
                    "type": "screencast_frame",
                    "frame": frame_b64
                }))
                await asyncio.sleep(1.0) # 1 FPS idle stream
        except Exception:
            pass

    screencast_task = asyncio.create_task(push_screencast())

    try:
        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)
            msg_type = data.get("type")

            if msg_type == "chat_message":
                user_msg = data.get("message", "")
                context = exec_engine.get_system_telemetry()
                agent_res = await agy_agent.chat(user_msg, context=context)

                cmd_res = None
                if agent_res.get("suggested_commands"):
                    cmd_res = await exec_engine.run_bash(agent_res["suggested_commands"][0])

                await websocket.send_text(json.dumps({
                    "type": "chat_response",
                    "response": agent_res["response"],
                    "command_result": cmd_res
                }))

            elif msg_type == "browser_navigate":
                target_url = data.get("url", "")
                await browser_engine.navigate(target_url)

            elif msg_type == "voice_chunk":
                audio_b64 = data.get("audio", "")
                res = voice_engine.process_incoming_audio_chunk(session_id, audio_b64)
                await websocket.send_text(json.dumps({
                    "type": "voice_ack",
                    "payload": res
                }))

    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {session_id}")
    finally:
        screencast_task.cancel()
        connected_websockets.discard(websocket)
        voice_engine.close_session(session_id)

if __name__ == "__main__":
    uvicorn.run("server:app", host=HOST, port=PORT, reload=False, log_level="info")

"""
Bi-Directional Audio & Voice Gateway Engine
Provides WebRTC / WebSocket audio streaming, dictation, and speech loops.
"""

import asyncio
import base64
import logging
import time
from typing import Dict, Any

logger = logging.getLogger("VoiceEngine")

class VoiceEngine:
    def __init__(self):
        self.active_sessions: Dict[str, Any] = {}

    def create_session(self, session_id: str, client_platform: str) -> Dict[str, Any]:
        """Creates a voice session for mobile or web client."""
        session = {
            "session_id": session_id,
            "platform": client_platform,
            "created_at": time.time(),
            "status": "CONNECTED",
            "audio_packets_received": 0,
            "audio_packets_sent": 0
        }
        self.active_sessions[session_id] = session
        logger.info(f"Voice session created: {session_id} [{client_platform}]")
        return session

    def process_incoming_audio_chunk(self, session_id: str, audio_base64: str) -> Dict[str, Any]:
        """Processes binary audio payload from mobile microphone."""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["audio_packets_received"] += 1

        # Calculate simulated energy / VAD
        data_len = len(audio_base64)
        return {
            "session_id": session_id,
            "status": "PROCESSED",
            "bytes_received": data_len,
            "vad_detected": data_len > 100
        }

    def close_session(self, session_id: str):
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info(f"Voice session closed: {session_id}")

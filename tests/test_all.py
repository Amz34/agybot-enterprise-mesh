"""
Automated Unit and Integration Tests for AgyBot Sovereign Mesh
"""

import unittest
import asyncio
from exec_engine import ExecutionEngine
from agy_agent import AgyGeminiAgent
from browser_engine import BrowserScreencastEngine
from voice_engine import VoiceEngine

class TestAgyBotMesh(unittest.IsolatedAsyncioTestCase):

    async def test_exec_engine_bash(self):
        engine = ExecutionEngine()
        result = await engine.run_bash("echo 'Hello AgyBot ARM64'")
        self.assertTrue(result["success"])
        self.assertEqual(result["exit_code"], 0)
        self.assertIn("Hello AgyBot ARM64", result["stdout"])

    def test_exec_engine_telemetry(self):
        engine = ExecutionEngine()
        telemetry = engine.get_system_telemetry()
        self.assertIn("architecture", telemetry)
        self.assertIn("cpu_cores", telemetry)
        self.assertGreater(telemetry["cpu_cores"], 0)

    async def test_agy_agent_chat(self):
        agent = AgyGeminiAgent()
        res = await agent.chat("Check system health")
        self.assertIn("response", res)
        self.assertTrue(len(res["suggested_commands"]) > 0)
        self.assertIn("uptime", res["suggested_commands"][0])

    def test_browser_screencast_frame(self):
        browser = BrowserScreencastEngine()
        frame = browser.generate_simulated_frame()
        self.assertTrue(len(frame) > 100)
        self.assertIsInstance(frame, str)

    def test_voice_session(self):
        voice = VoiceEngine()
        sess = voice.create_session("test_sess", "Mobile-Android")
        self.assertEqual(sess["status"], "CONNECTED")
        res = voice.process_incoming_audio_chunk("test_sess", "dGVzdGF1ZGlvYnl0ZXM=")
        self.assertEqual(res["status"], "PROCESSED")
        voice.close_session("test_sess")
        self.assertNotIn("test_sess", voice.active_sessions)

if __name__ == "__main__":
    unittest.main()

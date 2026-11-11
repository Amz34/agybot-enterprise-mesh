"""
Execution Engine: Host CLI, Terminal, File System & System Telemetry
Allows sovereign, permissioned command execution directly on the host VM.
"""

import asyncio
import os
import platform
import shutil
import time
from typing import Dict, Any, List
from config import WORKSPACE_ROOT, MAX_CLI_TIMEOUT_SECONDS

class ExecutionEngine:
    def __init__(self, workspace: str = str(WORKSPACE_ROOT)):
        self.workspace = workspace
        os.makedirs(self.workspace, exist_ok=True)

    async def run_bash(self, command: str, cwd: str = None) -> Dict[str, Any]:
        """Runs a bash command with timeout and environment propagation."""
        work_dir = cwd or self.workspace
        start = time.perf_counter()
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=work_dir,
                env=os.environ.copy()
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=MAX_CLI_TIMEOUT_SECONDS
            )
            elapsed = time.perf_counter() - start
            return {
                "success": process.returncode == 0,
                "exit_code": process.returncode,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "elapsed_sec": round(elapsed, 3),
                "cwd": work_dir
            }
        except asyncio.TimeoutError:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Command timed out after {MAX_CLI_TIMEOUT_SECONDS}s",
                "elapsed_sec": MAX_CLI_TIMEOUT_SECONDS,
                "cwd": work_dir
            }
        except Exception as e:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "elapsed_sec": 0,
                "cwd": work_dir
            }

    def list_files(self, relative_path: str = "") -> List[Dict[str, Any]]:
        """List files in the workspace directory."""
        target = os.path.join(self.workspace, relative_path)
        if not os.path.exists(target):
            return []
        items = []
        for entry in os.scandir(target):
            items.append({
                "name": entry.name,
                "is_dir": entry.is_dir(),
                "size": entry.stat().st_size if entry.is_file() else 0,
                "mtime": entry.stat().st_mtime
            })
        return sorted(items, key=lambda x: (not x["is_dir"], x["name"]))

    def get_system_telemetry(self) -> Dict[str, Any]:
        """System health and resource telemetry."""
        total, used, free = shutil.disk_usage("/")
        load_1, load_5, load_15 = os.getloadavg()
        return {
            "platform": platform.platform(),
            "architecture": platform.machine(),
            "cpu_cores": os.cpu_count(),
            "load_averages": [load_1, load_5, load_15],
            "disk_total_gb": round(total / (1024**3), 2),
            "disk_used_gb": round(used / (1024**3), 2),
            "disk_free_gb": round(free / (1024**3), 2),
            "disk_usage_pct": round((used / total) * 100, 1),
            "time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

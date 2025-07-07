# Agents/environment_check_agent.py

import subprocess
from agno.utils.log import log_info
from typing import List, Dict

class EnvironmentCheckAgent:
    """Checks for the existence of required command-line tools."""
    def check_dependencies(self, required_tools: List[str]) -> Dict[str, bool]:
        log_info(f"Running pre-flight check for tools: {required_tools}")
        status = {}
        for tool in required_tools:
            try:
                # Use 'which' on macOS/Linux and 'where' on Windows to find the tool
                check_command = "which" if subprocess.os.name != 'nt' else "where"
                subprocess.run([check_command, tool], check=True, capture_output=True)
                status[tool] = True
                log_info(f"  ✅ '{tool}' is installed.")
            except (subprocess.CalledProcessError, FileNotFoundError):
                status[tool] = False
                log_info(f"  ❌ '{tool}' is NOT installed.")
        return status
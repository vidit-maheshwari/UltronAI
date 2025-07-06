# Agents/environment_check_agent.py
# This agent's only job is to check if the required tools are available before the main task begins.

import subprocess
from agno.utils.log import log_info
from typing import List, Dict

class EnvironmentCheckAgent:
    def check_dependencies(self, required_tools: List[str]) -> Dict[str, bool]:
        """Checks if a list of command-line tools are available in the system's PATH."""
        log_info(f"Running pre-flight check for tools: {required_tools}")
        status = {}
        for tool in required_tools:
            try:
                # Use 'which' on Unix-like systems and 'where' on Windows
                check_command = "which" if not subprocess.os.name == 'nt' else "where"
                subprocess.run([check_command, tool], check=True, capture_output=True)
                status[tool] = True
                log_info(f"  ✅ '{tool}' is installed.")
            except (subprocess.CalledProcessError, FileNotFoundError):
                status[tool] = False
                log_info(f"  ❌ '{tool}' is NOT installed.")
        return status
from agno.agent import Agent
from agno.models.groq import Groq
from agno.storage.sqlite import SqliteStorage
from pathlib import Path
from dotenv import load_dotenv

# Import tool interfaces from other agents
from agno.tools.shell import ShellTools
from agno.tools.file import FileTools
from agno.tools import tool

import subprocess
import sys

load_dotenv()

class ExecutorAgentNode:
    def __init__(
        self,
        agent_id: str = "executor_agent",
        db_file: str = "agents.db",
        table_name: str = "executor_sessions",
        base_dir: Path = None,
    ):
        self.base_dir = base_dir or Path.cwd()
        self.storage = SqliteStorage(table_name=table_name, db_file=db_file)
        self.model = Groq(id="deepseek-r1-distill-llama-70b")

        # Delegate tools from other agents
        self.shell_tools = ShellTools(cwd=self.base_dir)
        self.file_tools = FileTools(base_dir=self.base_dir)

        # Optional: Local tool for running Python scripts
        @tool(show_result=True)
        def run_python_file(file_name: str, args: str = "") -> str:
            """Execute a Python file and return output."""
            try:
                file_path = self.base_dir / file_name
                if not file_path.exists():
                    return f"❌ File {file_name} does not exist"

                cmd = [sys.executable, str(file_path)]
                if args:
                    cmd.extend(args.split())

                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=60, cwd=self.base_dir
                )

                output = ""
                if result.stdout:
                    output += f"🟢 Output:\n{result.stdout}\n"
                if result.stderr:
                    output += f"🔴 Errors:\n{result.stderr}\n"
                output += f"Exit code: {result.returncode}"

                return output
            except subprocess.TimeoutExpired:
                return "⏰ Execution timed out (60s limit)"
            except Exception as e:
                return f"❌ Error executing {file_name}: {str(e)}"

        self.run_python_file = run_python_file

        self.agent = Agent(
            model=self.model,
            tools=[
                self.shell_tools,         # Delegated shell execution
                self.file_tools,          # Delegated file operations
                self.run_python_file      # Optional: native Python runner
            ],
            storage=self.storage,
            agent_id=self.agent_id,
            show_tool_calls=True,
            markdown=True,
            instructions="""
You are the execution lead of a developer team. You do NOT write new code or install packages.
You coordinate between different agents to:

1. Execute Python scripts
2. Run shell commands
3. Manage file creation, reading, writing, or deletion

Respond clearly with only what’s needed. Use tools to accomplish goals.
"""
        )

    def run(self, prompt: str, stream: bool = True) -> str:
        return self.agent.print_response(prompt, stream=stream)

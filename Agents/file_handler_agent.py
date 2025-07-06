# Agents/file_handler_agent.py

from agno.utils.log import log_info
from pathlib import Path
import dotenv
from typing import Dict, Any
import re
from shared_state import SharedState

dotenv.load_dotenv()

class FileAgentNode:
    """
    A deterministic file operations node. It does not use an LLM.
    It executes specific file tasks based on a simple command language.
    """
    def __init__(self):
        log_info("Initialized deterministic FileAgentNode.")

    def _create_project_directory(self, shared_state: 'SharedState') -> Dict[str, Any]:
        try:
            original_task = shared_state.original_task.lower()
            words = [word for word in original_task.split() if word.isalnum()]
            project_name = "-".join(words[:3]) if words else "new-project"
            
            base_projects_dir = Path.cwd() / "projects"
            base_projects_dir.mkdir(exist_ok=True)

            project_dir = base_projects_dir / project_name
            project_dir.mkdir(exist_ok=True)
            
            log_info(f"Project directory created at: {project_dir}")
            
            return {
                "status": "success",
                "output": f"Project directory '{project_name}' created.",
                "project_directory": project_dir,
            }
        except Exception as e:
            log_info(f"Error creating project directory: {e}")
            return {"status": "error", "error": str(e)}

    def _write_file(self, command: str, shared_state: 'SharedState') -> Dict[str, Any]:
        try:
            # Parse filename from a command like "SAVE CODE TO 'index.html'" or "CREATE EMPTY FILE 'index.html'"
            file_name_match = re.search(r"['\"]([\w\.\-]+)['\"]", command)
            if not file_name_match:
                return {"status": "error", "error": "Malformed write command. Could not find filename."}
            file_name = file_name_match.group(1)

            # If saving code, get it from state; otherwise, it's an empty file.
            code_to_write = shared_state.generated_code.get(file_name, "")
            if not code_to_write and "SAVE CODE" in command.upper():
                 log_info(f"Warning: No code found for '{file_name}' during SAVE operation.")

            if not shared_state.project_directory:
                # If no project directory, create one in the CWD
                project_dir = Path.cwd() / "projects" / "default-project"
                project_dir.mkdir(parents=True, exist_ok=True)
                shared_state.set_project_directory(project_dir)
                log_info(f"Project directory was not set, created default at {project_dir}")

            file_path = shared_state.project_directory / file_name
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code_to_write)

            log_info(f"Successfully wrote {len(code_to_write)} characters to {file_path}")
            return {
                "status": "success",
                "output": f"File '{file_name}' saved successfully.",
                "created_files": [str(file_path)]
            }
        except Exception as e:
            log_info(f"Error saving file: {e}")
            return {"status": "error", "error": str(e)}

    def run(self, command: str, shared_state: 'SharedState') -> Dict[str, Any]:
        """A simple router that calls the correct internal method based on our command language."""
        command_upper = command.strip().upper()
        try:
            if command_upper == "CREATE PROJECT STRUCTURE":
                log_info("File agent routing to: _create_project_directory")
                return self._create_project_directory(shared_state)
            
            elif command_upper.startswith("SAVE CODE TO") or command_upper.startswith("CREATE EMPTY FILE"):
                log_info(f"File agent routing to: _write_file for command: {command}")
                return self._write_file(command, shared_state)

            else:
                log_info(f"File agent received unhandled command: {command}")
                return {"status": "error", "error": f"File agent does not support the command: '{command}'"}
        except Exception as e:
            log_info(f"A critical error occurred in the FileAgentNode run method: {e}")
            return {"status": "error", "error": str(e)}
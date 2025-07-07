# shared_state.py

from typing import Dict, Any, List, Optional
from pathlib import Path

class SharedState:
    def __init__(self, original_task: str):
        self.original_task: str = original_task
        self.current_plan: List[Dict[str, Any]] = []
        self.project_directory: Optional[Path] = None
        self.created_files: List[str] = []
        self.generated_code: Dict[str, str] = {}
        self.last_execution_output: Optional[str] = None
        self.last_execution_error: Optional[str] = None
        self.current_status: str = "planning"
        self.history: List[str] = []
        # --- NEW FLAG ---
        self.is_existing_project: bool = False
        # --- NEW: Document content storage ---
        self.document_content: Optional[str] = None

    def update_status(self, new_status: str):
        self.current_status = new_status
        self.add_to_history(f"Status changed to: {new_status}")

    def update_plan(self, plan: List[Dict[str, Any]]):
        self.current_plan = plan
        self.add_to_history("Execution plan has been updated.")

    def add_created_file(self, file_path: str):
        if file_path not in self.created_files:
            self.created_files.append(file_path)
            self.add_to_history(f"File created: {file_path}")

    def add_generated_code(self, filename: str, code: str):
        self.generated_code[filename] = code
        self.add_to_history(f"Code generated for {filename}.")

    def set_project_directory(self, path: Path, from_prompt: bool = False):
        self.project_directory = path
        if from_prompt:
            self.is_existing_project = True
            self.add_to_history(f"Project directory set from prompt: {path}")
        else:
            self.add_to_history(f"Project directory set to: {path}")

    def log_execution_output(self, output: str, error: Optional[str] = None):
        self.last_execution_output = output
        self.last_execution_error = error
        if error:
            self.update_status("error")
            self.add_to_history(f"Execution resulted in an error: {error}")
        else:
            self.add_to_history(f"Execution successful. Output: {output[:100] if output else 'No output.'}...")

    def add_to_history(self, message: str):
        self.history.append(message)
    
    # --- NEW METHOD ---
    def set_document_content(self, content: str):
        """Stores the content of a read document."""
        self.document_content = content
        self.add_to_history(f"Document content loaded into memory ({len(content)} chars).")


    def get_full_context(self) -> Dict[str, Any]:
        """Returns the entire state as a dictionary for agents to use."""
        return {
            "original_task": self.original_task,
            "current_plan": self.current_plan,
            "project_directory": str(self.project_directory) if self.project_directory else None,
            "is_existing_project": self.is_existing_project,
            "created_files": self.created_files,
            "generated_code_keys": list(self.generated_code.keys()),
            # --- NEW: Add document content to the context for the planner ---
            "document_content": self.document_content,
            "last_execution_output": self.last_execution_output,
            "last_execution_error": self.last_execution_error,
            "current_status": self.current_status,
            "history": self.history
        }
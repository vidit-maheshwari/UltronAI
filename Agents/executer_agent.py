from agno.agent import Agent
from agno.models.groq import Groq
from agno.storage.sqlite import SqliteStorage as SqlAgentStorage
from agno.utils.log import log_info
from pathlib import Path
from dotenv import load_dotenv
import signal
import sys
import os
import platform

# Import specialized agents
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Agents.file_handler_agent import FileAgentNode
from Agents.shell_executer_agent import ShellAgentNode

import subprocess
import mimetypes
from agno.tools import tool
import shutil
import json
from typing import Dict, Any, Optional

load_dotenv()

class ExecutorAgentNode:
    def __init__(
        self,
        agent_id: str = "executor_agent",
        db_file: str = "agents.db",
        table_name: str = "executor_agent_memory",
        model_name: str = "deepseek-r1-distill-llama-70b",
        markdown: bool = True,
        base_dir: Optional[Path] = None
    ):
        self.storage = SqlAgentStorage(table_name=table_name, db_file=db_file)
        self.agent_id = agent_id
        self.base_dir = base_dir or Path.cwd()
        self.is_running = True

        # Set up signal handlers for graceful shutdown
        if platform.system() == 'Windows':
            signal.signal(signal.SIGINT, self._handle_shutdown)
        else:
            signal.signal(signal.SIGINT, self._handle_shutdown)
            signal.signal(signal.SIGTERM, self._handle_shutdown)

        # Initialize specialized agents
        self.file_agent = FileAgentNode(
            agent_id=f"{agent_id}_file",
            db_file=db_file,
            table_name=f"{table_name}_file",
            base_dir=self.base_dir
        )
        
        self.shell_agent = ShellAgentNode(
            agent_id="shell_executor",
            db_file=db_file,
            table_name="shell_agent_sessions"
        )

        # File operation tools
        @tool(show_result=True)
        def rename_file(old_name: str, new_name: str) -> str:
            """Rename a file from old_name to new_name."""
            try:
                old_path = self.base_dir / old_name
                new_path = self.base_dir / new_name
                
                if not old_path.exists():
                    return f"❌ File {old_name} does not exist in {self.base_dir}"
                
                if new_path.exists():
                    return f"❌ File {new_name} already exists in {self.base_dir}"
                
                shutil.move(str(old_path), str(new_path))
                return f"✅ Successfully renamed {old_name} to {new_name} in {self.base_dir}"
            except Exception as e:
                return f"❌ Error renaming file: {str(e)}"

        @tool(show_result=True)
        def execute_file(file_name: str, args: str = "") -> str:
            """Execute any type of file based on its extension and return output."""
            try:
                file_path = self.base_dir / file_name
                if not file_path.exists():
                    return f"❌ File {file_name} does not exist in {self.base_dir}"

                # Get file type
                mime_type, _ = mimetypes.guess_type(str(file_path))
                file_extension = file_path.suffix.lower()

                # Prepare command based on file type
                if file_extension == '.py':
                    cmd = [sys.executable, str(file_path)]
                elif file_extension == '.sh':
                    cmd = ['bash', str(file_path)]
                elif file_extension == '.js':
                    cmd = ['node', str(file_path)]
                elif file_extension == '.rb':
                    cmd = ['ruby', str(file_path)]
                elif file_extension == '.php':
                    cmd = ['php', str(file_path)]
                elif file_extension == '.java':
                    # Compile and run Java
                    class_name = file_path.stem
                    compile_cmd = ['javac', str(file_path)]
                    subprocess.run(compile_cmd, capture_output=True, text=True, cwd=self.base_dir)
                    cmd = ['java', class_name]
                elif file_extension == '.go':
                    # Build and run Go
                    build_cmd = ['go', 'build', str(file_path)]
                    subprocess.run(build_cmd, capture_output=True, text=True, cwd=self.base_dir)
                    cmd = [f'./{file_path.stem}']
                elif file_extension == '.rs':
                    # Build and run Rust
                    build_cmd = ['rustc', str(file_path)]
                    subprocess.run(build_cmd, capture_output=True, text=True, cwd=self.base_dir)
                    cmd = [f'./{file_path.stem}']
                else:
                    # For other file types, try to execute with appropriate program
                    if os.access(str(file_path), os.X_OK):
                        cmd = [str(file_path)]
                    else:
                        return f"❌ Cannot execute file type: {file_extension}"

                # Add arguments if provided
                if args:
                    cmd.extend(args.split())

                # Execute the command
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=60, cwd=self.base_dir
                )

                output = f"📂 Executing in: {self.base_dir}\n"
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

        @tool(show_result=True)
        def execute_code(code: str, language: str = "python") -> str:
            """Execute code directly in the specified language."""
            try:
                # Create temporary file
                temp_file = self.base_dir / f"temp_execution.{language}"
                
                # Write code to file
                with open(temp_file, 'w') as f:
                    f.write(code)
                
                # Execute the temporary file
                result = execute_file(str(temp_file))
                
                # Clean up
                temp_file.unlink()
                
                return result
            except Exception as e:
                return f"❌ Error executing code: {str(e)}"

        self.execute_file = execute_file
        self.execute_code = execute_code
        self.rename_file = rename_file

        self.agent = Agent(
            model=Groq(id=model_name),
            storage=self.storage,
            agent_id=self.agent_id,
            show_tool_calls=True,
            markdown=markdown,
            instructions="""You are the Executor Agent in a multi-agent system. Your job is to execute code and scripts.
            When executing code:
            1. Always verify the code is safe to run
            2. Handle any errors gracefully
            3. Save results to files when needed
            4. Report execution status and results
            
            Available operations:
            - execute_code: Run Python code
            - execute_script: Run shell scripts
            - save_results: Save execution results
            
            Always verify the execution environment and handle errors appropriately."""
        )

    def _handle_shutdown(self, signum, frame):
        """Handle graceful shutdown on Ctrl+C (Windows) or Cmd+C (Mac)."""
        print("\n🛑 Shutting down gracefully...")
        self.is_running = False
        # Clean up any temporary files
        temp_files = list(self.base_dir.glob("temp_execution.*"))
        for temp_file in temp_files:
            try:
                temp_file.unlink()
            except:
                pass
        print("✅ Cleanup complete. Goodbye!")
        sys.exit(0)

    def _analyze_task(self, prompt: str) -> list:
        """Analyze the task and break it down into smaller steps."""
        steps = []
        
        # Check for navigation needs
        if any(keyword in prompt.lower() for keyword in ['cd', 'navigate', 'go to', 'directory']):
            steps.append({
                'type': 'shell',
                'action': 'navigate',
                'description': 'Navigate to required directory'
            })
        
        # Check for listing needs
        if any(keyword in prompt.lower() for keyword in ['list', 'ls', 'show files', 'directory contents']):
            steps.append({
                'type': 'shell',
                'action': 'list',
                'description': 'List directory contents'
            })
        
        # Check for file operations
        if any(keyword in prompt.lower() for keyword in ['file', 'create', 'read', 'write', 'delete', 'save', 'content']):
            if 'rename' in prompt.lower():
                steps.append({
                    'type': 'file',
                    'action': 'rename',
                    'description': 'Rename file'
                })
            else:
                steps.append({
                    'type': 'file',
                    'action': 'operate',
                    'description': 'Perform file operation'
                })
        
        # Check for code execution
        if any(keyword in prompt.lower() for keyword in ['execute', 'run', 'code', 'script']):
            steps.append({
                'type': 'code',
                'action': 'execute',
                'description': 'Execute code'
            })
        
        return steps

    def run(self, prompt: str) -> Dict[str, Any]:
        """Execute code or script based on the prompt."""
        try:
            # Get response from the agent
            response = self.agent.run(prompt)
            
            # Extract content from response
            content = str(response)
            
            # Check if this is a save operation
            if "save" in prompt.lower() and "file" in prompt.lower():
                # Use file agent to save the content
                return self.file_agent.run(prompt)
            
            return {
                "status": "success",
                "message": "Operation completed",
                "content": content
            }
            
        except Exception as e:
            log_info(f"Error in run method: {str(e)}")
            return {
                "status": "error",
                "message": f"Error: {str(e)}",
                "content": ""
            }

    def execute_task(self, task: dict) -> dict:
        """
        Execute a task with structured input.
        
        Args:
            task (dict): A dictionary containing:
                - type: The type of task ('file', 'shell', 'code', etc.)
                - action: The specific action to perform
                - parameters: Any parameters needed for the action
                
        Returns:
            dict: The structured response from run()
        """
        try:
            # Convert task to prompt
            prompt = self._task_to_prompt(task)
            return self.run(prompt)
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error processing task: {str(e)}",
                "details": {"error_type": type(e).__name__},
                "tool_outputs": {}
            }

    def _task_to_prompt(self, task: dict) -> str:
        """Convert a structured task to a natural language prompt."""
        task_type = task.get('type', '')
        action = task.get('action', '')
        params = task.get('parameters', {})
        
        if task_type == 'shell':
            if action == 'navigate':
                return f"navigate to directory {params.get('directory')}"
            elif action == 'list':
                return f"list files in {params.get('directory', 'current directory')}"
            elif action == 'execute':
                return f"run the shell command: {params.get('command')}"
        elif task_type == 'file':
            if action == 'rename':
                return f"change the file name from {params.get('old_name')} to {params.get('new_name')}"
            elif action == 'create':
                return f"create file {params.get('file_name')} with content: {params.get('content', '')}"
            elif action == 'read':
                return f"read the contents of file {params.get('file_name')}"
            elif action == 'write':
                return f"write to file {params.get('file_name')} the content: {params.get('content', '')}"
        elif task_type == 'code':
            return f"execute this {params.get('language', 'python')} code: {params.get('code')}"
        
        return json.dumps(task)  # Fallback to JSON representation




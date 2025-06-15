from agno.agent import Agent
from agno.models.groq import Groq
from agno.storage.sqlite import SqliteStorage
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

load_dotenv()

class ExecutorAgentNode:
    def __init__(
        self,
        agent_id: str = "executor_agent",
        name: str = "Code Executor Agent",  # Add this parameter
        role: str = "Code Execution and Coordination Specialist",
        db_file: str = "agents.db",
        table_name: str = "executor_sessions",
        base_dir: Path = None,
    ):
        self.name = name  # Add this line
        self.role = role
        self.base_dir = base_dir or Path.cwd()
        self.storage = SqliteStorage(table_name=table_name, db_file=db_file)
        self.model = Groq(id="deepseek-r1-distill-llama-70b")
        self.agent_id = agent_id
        self.current_path = self.base_dir
        self.is_running = True

        # Set up signal handlers for graceful shutdown
        if platform.system() == 'Windows':
            signal.signal(signal.SIGINT, self._handle_shutdown)
        else:
            signal.signal(signal.SIGINT, self._handle_shutdown)
            signal.signal(signal.SIGTERM, self._handle_shutdown)

        # Initialize specialized agents
        self.file_agent = FileAgentNode(
            agent_id="file_handler",
            db_file=db_file,
            table_name="file_agent_sessions",
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
                old_path = self.current_path / old_name
                new_path = self.current_path / new_name
                
                if not old_path.exists():
                    return f"❌ File {old_name} does not exist in {self.current_path}"
                
                if new_path.exists():
                    return f"❌ File {new_name} already exists in {self.current_path}"
                
                shutil.move(str(old_path), str(new_path))
                return f"✅ Successfully renamed {old_name} to {new_name} in {self.current_path}"
            except Exception as e:
                return f"❌ Error renaming file: {str(e)}"

        @tool(show_result=True)
        def execute_file(file_name: str, args: str = "") -> str:
            """Execute any type of file based on its extension and return output."""
            try:
                file_path = self.current_path / file_name
                if not file_path.exists():
                    return f"❌ File {file_name} does not exist in {self.current_path}"

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
                    subprocess.run(compile_cmd, capture_output=True, text=True, cwd=self.current_path)
                    cmd = ['java', class_name]
                elif file_extension == '.go':
                    # Build and run Go
                    build_cmd = ['go', 'build', str(file_path)]
                    subprocess.run(build_cmd, capture_output=True, text=True, cwd=self.current_path)
                    cmd = [f'./{file_path.stem}']
                elif file_extension == '.rs':
                    # Build and run Rust
                    build_cmd = ['rustc', str(file_path)]
                    subprocess.run(build_cmd, capture_output=True, text=True, cwd=self.current_path)
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
                    cmd, capture_output=True, text=True, timeout=60, cwd=self.current_path
                )

                output = f"📂 Executing in: {self.current_path}\n"
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
                temp_file = self.current_path / f"temp_execution.{language}"
                
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
            model=self.model,
            tools=[
                self.execute_file,
                self.execute_code,
                self.rename_file
            ],
            storage=self.storage,
            agent_id=self.agent_id,
            show_tool_calls=True,
            markdown=True,
            instructions="""
You are a universal execution agent that coordinates between shell operations and file operations. You can:

1. Shell Operations (via shell_agent):
   - Navigate directories (cd)
   - List files and directories (ls)
   - Execute shell commands
   - Check current directory (pwd)
   - Create/remove directories
   - Run system commands

2. File Operations (via file_agent):
   - Create new files
   - Read file contents
   - Write/modify file contents
   - Delete files
   - Rename files (via rename_file tool)
   - Check file existence
   - Get file information

3. Code Execution:
   - Execute Python files
   - Execute shell scripts
   - Execute other language files
   - Run code snippets directly

When handling tasks:
1. First, analyze the task and break it down into smaller steps
2. For each step:
   - Show the current working directory
   - Execute the operation
   - Verify the result
   - Move to the next step

3. For navigation and listing:
   - Use shell_agent for cd, ls, pwd commands
   - Always show current directory before and after navigation
   - Example: "navigate to directory X" or "list files in current directory"

4. For file operations:
   - Use file_agent for create/read/write/delete
   - Use rename_file tool specifically for renaming
   - Always show the full path of files being operated on
   - Example: "create file X with content Y" or "read file X"

5. For combined operations:
   - First navigate to correct directory using shell_agent
   - Then perform file operations using file_agent
   - Show progress for each step
   - Example: "go to directory X and create file Y"

IMPORTANT RULES:
- Always show current directory before operations
- Break down complex tasks into steps
- Show progress for each step
- Use appropriate agent for each operation type
- Chain operations logically (navigate → list → operate)
- Provide clear status messages for each step
- Handle errors gracefully with specific messages

Example workflow:
1. Show current directory
2. Navigation: "cd to directory X"
3. Show new directory
4. Listing: "list files in current directory"
5. File operation: "create file Y with content Z"
6. Verification: "read file Y to confirm content"

Keep responses clear and focused on the current operation.
"""
        )

    def _handle_shutdown(self, signum, frame):
        """Handle graceful shutdown on Ctrl+C (Windows) or Cmd+C (Mac)."""
        print("\n🛑 Shutting down gracefully...")
        self.is_running = False
        # Clean up any temporary files
        temp_files = list(self.current_path.glob("temp_execution.*"))
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

    def run(self, prompt: str, stream: bool = True) -> dict:
        """
        Execute a task and return a structured response.
        
        Args:
            prompt (str): The task to execute
            stream (bool): Whether to stream the response
            
        Returns:
            dict: A structured response containing:
                - status: 'success' or 'error'
                - message: The main response message
                - details: Additional details or error information
                - tool_outputs: Outputs from any tools used
        """
        try:
            # Initialize response structure
            response = {
                "status": "success",
                "message": "",
                "details": {},
                "tool_outputs": {}
            }
            
            # Analyze task and break it down
            steps = self._analyze_task(prompt)
            if not steps:
                return {
                    "status": "error",
                    "message": "❌ Could not analyze task into steps",
                    "details": {"error_type": "TaskAnalysisError"},
                    "tool_outputs": {}
                }
            
            # Execute each step
            for i, step in enumerate(steps, 1):
                if not self.is_running:
                    return {
                        "status": "interrupted",
                        "message": "🛑 Task interrupted by user",
                        "details": {"step": i, "total_steps": len(steps)},
                        "tool_outputs": response["tool_outputs"]
                    }
                
                # Show current directory
                current_dir_msg = f"\n📂 Current directory: {self.current_path}\n"
                response["message"] += current_dir_msg
                
                # Execute step based on type
                if step['type'] == 'shell':
                    if step['action'] == 'navigate':
                        shell_response = self.shell_agent.run(prompt, stream=stream)
                        if shell_response:
                            # Update current path if navigation was successful
                            if 'cd' in shell_response.lower():
                                try:
                                    new_path = shell_response.split('cd')[1].strip()
                                    self.current_path = Path(new_path).resolve()
                                except:
                                    pass
                            response["tool_outputs"][f"step_{i}"] = shell_response
                            response["message"] += f"\nStep {i}: {step['description']}\n{shell_response}\n"
                    elif step['action'] == 'list':
                        shell_response = self.shell_agent.run("ls", stream=stream)
                        if shell_response:
                            response["tool_outputs"][f"step_{i}"] = shell_response
                            response["message"] += f"\nStep {i}: {step['description']}\n{shell_response}\n"
                
                elif step['type'] == 'file':
                    if step['action'] == 'rename':
                        main_response = self.agent.print_response(prompt, stream=stream)
                        if main_response:
                            response["message"] += f"\nStep {i}: {step['description']}\n{main_response}\n"
                    else:
                        file_response = self.file_agent.run(prompt, stream=stream)
                        if file_response:
                            response["tool_outputs"][f"step_{i}"] = file_response
                            response["message"] += f"\nStep {i}: {step['description']}\n{file_response}\n"
                
                elif step['type'] == 'code':
                    main_response = self.agent.print_response(prompt, stream=stream)
                    if main_response:
                        response["message"] += f"\nStep {i}: {step['description']}\n{main_response}\n"
            
            return response
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error executing task: {str(e)}",
                "details": {"error_type": type(e).__name__},
                "tool_outputs": {}
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




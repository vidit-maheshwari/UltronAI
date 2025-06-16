from agno.agent import Agent
from agno.tools.shell import ShellTools
from agno.storage.sqlite import SqliteStorage as SqlAgentStorage
from agno.models.groq import Groq
import dotenv
import os
import platform
import subprocess
from typing import Optional, Dict, Any, List
import json
from datetime import datetime
import shlex

dotenv.load_dotenv()

class ShellAgentNode:
    def __init__(
        self,
        agent_id: str = "shell_agent",
        db_file: str = "agents.db",
        table_name: str = "shell_sessions",
        model_id: str = "deepseek-r1-distill-llama-70b",
        show_tool_calls: bool = True,
        markdown: bool = True,
    ):
        # Setup persistent storage for agent sessions
        self.storage = SqlAgentStorage(table_name=table_name, db_file=db_file)
        self.agent_id = agent_id

        # Detect platform and shell
        self.platform_info = self._detect_platform()
        self.shell_info = self._detect_shell()

        # Initialize model
        self.model = Groq(id=model_id)

        # Initialize agent with ShellTools and persistent storage
        self.agent = Agent(
            model=self.model,
            tools=[ShellTools()],
            storage=self.storage,
            agent_id=self.agent_id,
            show_tool_calls=show_tool_calls,
            markdown=markdown,
            instructions=f"""You are a shell command execution agent running on {self.platform_info['system']} with {self.shell_info['shell']} shell.

Your capabilities include:

1. System Information:
   - Get system status and metrics
   - Check hardware information
   - Monitor resource usage
   - View system logs

2. File Operations:
   - List, create, delete files and directories
   - Search files and directories
   - Handle file permissions
   - Process file contents

3. Process Management:
   - Start, stop, and monitor processes
   - Check system resources
   - Manage background tasks
   - Handle process priorities

4. Network Operations:
   - Check network connectivity
   - Monitor network traffic
   - Configure network settings
   - Test network services

Platform-specific commands:
{self._get_platform_instructions()}

When responding:
1. Use appropriate commands for the current platform
2. Provide clear, formatted output
3. Handle errors gracefully
4. Include relevant context in responses"""
        )

    def _detect_platform(self) -> Dict[str, Any]:
        """Detect the current platform and its characteristics"""
        system = platform.system().lower()
        release = platform.release()
        version = platform.version()
        machine = platform.machine()
        
        return {
            "system": system,
            "release": release,
            "version": version,
            "machine": machine,
            "is_mac": system == "darwin",
            "is_linux": system == "linux",
            "is_windows": system == "windows"
        }

    def _detect_shell(self) -> Dict[str, Any]:
        """Detect the current shell and its characteristics"""
        shell = os.environ.get('SHELL', '')
        if not shell:
            if self.platform_info['is_windows']:
                shell = 'cmd.exe' if os.environ.get('COMSPEC') else 'powershell.exe'
            else:
                shell = '/bin/bash'  # Default to bash for Unix-like systems

        return {
            "shell": shell,
            "is_bash": 'bash' in shell.lower(),
            "is_zsh": 'zsh' in shell.lower(),
            "is_powershell": 'powershell' in shell.lower(),
            "is_cmd": 'cmd' in shell.lower()
        }

    def _get_platform_instructions(self) -> str:
        """Get platform-specific instructions for the agent"""
        instructions = []
        
        if self.platform_info['is_mac']:
            instructions.extend([
                "- Use 'system_profiler' for system information",
                "- Use 'top -l 1' for CPU usage",
                "- Use 'vm_stat' for memory stats",
                "- Use 'networksetup' for network info",
                "- Use 'diskutil' for disk operations"
            ])
        elif self.platform_info['is_linux']:
            instructions.extend([
                "- Use 'uname -a' for system info",
                "- Use 'top -bn1' for CPU usage",
                "- Use 'free -h' for memory stats",
                "- Use 'ip' for network info",
                "- Use 'df -h' for disk usage"
            ])
        elif self.platform_info['is_windows']:
            instructions.extend([
                "- Use 'systeminfo' for system info",
                "- Use 'wmic cpu get loadpercentage' for CPU usage",
                "- Use 'wmic OS get FreePhysicalMemory,TotalVisibleMemorySize' for memory",
                "- Use 'ipconfig' for network info",
                "- Use 'wmic logicaldisk get size,freespace,caption' for disk info"
            ])

        return "\n".join(instructions)

    def _execute_command(self, command: str) -> str:
        """Execute a shell command and return its output"""
        try:
            if self.platform_info['is_windows']:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    check=True
                )
            else:
                # For Unix-like systems
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    check=True
                )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr.strip()}"
        except Exception as e:
            return f"Error: {str(e)}"

    def _get_command_for_task(self, task: str) -> str:
        """Get the appropriate command for the given task"""
        task = task.lower()
        
        if "list" in task and ("file" in task or "directory" in task or "dir" in task):
            if self.platform_info['is_windows']:
                return "dir"
            return "ls -la"
            
        elif "system" in task and "info" in task:
            if self.platform_info['is_windows']:
                return "systeminfo"
            elif self.platform_info['is_mac']:
                return "system_profiler SPSoftwareDataType SPHardwareDataType"
            return "uname -a"
            
        elif "cpu" in task or "processor" in task:
            if self.platform_info['is_windows']:
                return "wmic cpu get loadpercentage"
            elif self.platform_info['is_mac']:
                return "top -l 1 | grep 'CPU usage'"
            return "top -bn1 | grep 'Cpu(s)'"
            
        elif "memory" in task or "ram" in task:
            if self.platform_info['is_windows']:
                return "wmic OS get FreePhysicalMemory,TotalVisibleMemorySize"
            elif self.platform_info['is_mac']:
                return "vm_stat"
            return "free -h"
            
        elif "disk" in task or "space" in task:
            if self.platform_info['is_windows']:
                return "wmic logicaldisk get size,freespace,caption"
            return "df -h"
            
        elif "network" in task or "ip" in task:
            if self.platform_info['is_windows']:
                return "ipconfig"
            return "ifconfig || ip addr"
            
        elif "process" in task or "running" in task:
            if self.platform_info['is_windows']:
                return "tasklist"
            return "ps aux"
            
        return task  # Return the task as is if no specific command is found

    def run(self, prompt: str, stream: bool = True) -> Dict[str, Any]:
        """Execute shell commands based on the prompt"""
        try:
            print(f"\n🔧 Shell Command Request: {prompt}")
            
            # Get the appropriate command for the task
            command = self._get_command_for_task(prompt)
            
            # Execute the command
            output = self._execute_command(command)
            
            # Format the response
            return {
                "status": "success",
                "message": "Command executed successfully",
                "content": output,
                "platform": self.platform_info['system'],
                "shell": self.shell_info['shell'],
                "timestamp": datetime.now().isoformat(),
                "command": command
            }
            
        except Exception as e:
            error_msg = f"Error executing shell command: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "status": "error",
                "message": error_msg,
                "content": "",
                "platform": self.platform_info['system'],
                "shell": self.shell_info['shell'],
                "timestamp": datetime.now().isoformat(),
                "command": command if 'command' in locals() else prompt
            }

# Usage example:
if __name__ == "__main__":
    try:
        shell_node = ShellAgentNode()
        
        # Example commands for different platforms
        example_commands = [
            "show system information",
            "check CPU usage",
            "show memory usage",
            "list network interfaces",
            "check disk space"
        ]
        
        # Execute a command and print the structured response
        response = shell_node.run("list all the files in the current directory")
        print("\n📊 Command Response:")
        print(f"Status: {response['status']}")
        print(f"Message: {response['message']}")
        print(f"Platform: {response['platform']}")
        print(f"Shell: {response['shell']}")
        print(f"Timestamp: {response['timestamp']}")
        print(f"Command: {response['command']}")
        print("\nCommand Output:")
        print(response['content'])
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

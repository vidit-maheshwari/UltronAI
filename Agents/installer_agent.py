# installer_agent.py
import subprocess
import sys
import os
from agno.storage.sqlite import SqliteStorage
from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools import tool
import dotenv

dotenv.load_dotenv()

# Ensure GROQ_API_KEY is set
if not os.getenv("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY environment variable is not set. Please set it in your .env file.")

class InstallerAgentNode:
    def __init__(self, agent_id="installer_agent", db_file="agents.db", table_name="installer_sessions"):
        self.storage = SqliteStorage(table_name=table_name, db_file=db_file)
        self.agent_id = agent_id
        
        @tool(show_result=True)
        def install_pip_package(package_name: str, version: str = None) -> str:
            """Install a Python package using pip"""
            try:
                cmd = [sys.executable, "-m", "pip", "install"]
                if version:
                    cmd.append(f"{package_name}=={version}")
                else:
                    cmd.append(package_name)
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    return f"✅ Successfully installed {package_name}"
                else:
                    return f"❌ Failed to install {package_name}: {result.stderr}"
            except subprocess.TimeoutExpired:
                return f"⏰ Installation of {package_name} timed out"
            except Exception as e:
                return f"❌ Error installing {package_name}: {str(e)}"

        @tool(show_result=True)
        def uninstall_pip_package(package_name: str) -> str:
            """Uninstall a Python package using pip"""
            try:
                cmd = [sys.executable, "-m", "pip", "uninstall", "-y", package_name]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    return f"✅ Successfully uninstalled {package_name}"
                else:
                    return f"❌ Failed to uninstall {package_name}: {result.stderr}"
            except subprocess.TimeoutExpired:
                return f"⏰ Uninstallation of {package_name} timed out"
            except Exception as e:
                return f"❌ Error uninstalling {package_name}: {str(e)}"

        @tool(show_result=True)
        def check_package_installed(package_name: str) -> str:
            """Check if a package is installed and return its version"""
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "show", package_name],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    # Parse the output to get version
                    for line in result.stdout.split('\n'):
                        if line.startswith('Version:'):
                            version = line.split(':', 1)[1].strip()
                            return f"✅ {package_name} is installed (version: {version})"
                    return f"✅ {package_name} is installed"
                else:
                    return f"❌ {package_name} is not installed"
            except Exception as e:
                return f"❌ Error checking {package_name}: {str(e)}"
        
        self.install_pip_package = install_pip_package
        self.uninstall_pip_package = uninstall_pip_package
        self.check_package_installed = check_package_installed
        
        try:
            self.model = Groq(id="deepseek-r1-distill-llama-70b")
            self.agent = Agent(
                model=self.model,
                tools=[self.install_pip_package, self.uninstall_pip_package, self.check_package_installed],
                storage=self.storage,
                agent_id=self.agent_id,
                show_tool_calls=True,
                markdown=True,
                instructions="""You are a package installer agent. Your job is to:
1. Install Python packages using pip
2. Uninstall Python packages using pip
3. Check if packages are already installed
4. Handle package dependencies

When asked to perform package management tasks:
- First check if the package is installed
- If asked to uninstall, actually perform the uninstallation
- If asked to install, actually perform the installation
- Always perform the requested actions rather than just giving instructions

Do NOT write code or run applications - other agents handle that.
Focus only on package management and installation."""
            )
        except Exception as e:
            print(f"Error initializing Groq model: {str(e)}")
            raise
    
    def run(self, prompt: str, stream: bool = True) -> str:
        try:
            return self.agent.print_response(prompt, stream=stream)
        except Exception as e:
            print(f"Error running agent: {str(e)}")
            raise

if __name__ == "__main__":
    try:
        node = InstallerAgentNode()
        print(node.run("check if cadquery is installed, if yes then uninstall it"))
    except Exception as e:
        print(f"Error: {str(e)}")

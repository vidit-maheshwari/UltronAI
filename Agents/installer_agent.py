# installer_agent.py
import subprocess
import sys
from agno.storage.sqlite import SqliteStorage
from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools import tool
import dotenv

dotenv.load_dotenv()

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
        
        # @tool(show_result=True)
        # def check_package_installed(package_name: str) -> str:
        #     """Check if a package is already installed"""
        #     try:
        #         result = subprocess.run(
        #             [sys.executable, "-m", "pip", "show", package_name],
        #             capture_output=True, text=True
        #         )
        #         if result.returncode == 0:
        #             return f"✅ {package_name} is already installed"
        #         else:
        #             return f"❌ {package_name} is not installed"
        #     except Exception as e:
        #         return f"❌ Error checking {package_name}: {str(e)}"
        
        # @tool(show_result=True)
        # def install_from_requirements(requirements_file: str = "requirements.txt") -> str:
        #     """Install packages from requirements.txt"""
        #     try:
        #         result = subprocess.run(
        #             [sys.executable, "-m", "pip", "install", "-r", requirements_file],
        #             capture_output=True, text=True, timeout=300
        #         )
        #         if result.returncode == 0:
        #             return f"✅ Successfully installed packages from {requirements_file}"
        #         else:
        #             return f"❌ Failed to install from {requirements_file}: {result.stderr}"
        #     except Exception as e:
        #         return f"❌ Error: {str(e)}"
        
        self.install_pip_package = install_pip_package
        # self.check_package_installed = check_package_installed
        # self.install_from_requirements = install_from_requirements
        
        self.model = Groq(id="deepseek-r1-distill-llama-70b")
        self.agent = Agent(
            model=self.model,
            tools=[self.install_pip_package],
            storage=self.storage,
            agent_id=self.agent_id,
            show_tool_calls=True,
            markdown=True,
            instructions="""You are a package installer agent. Your job is ONLY to:
1. Install Python packages using pip
2. Check if packages are already installed
3. Install from requirements files
4. Handle package dependencies

Do NOT write code or run applications - other agents handle that.
Focus only on package management and installation."""
        )
    
    def run(self, prompt: str, stream: bool = True) -> str:
        return self.agent.print_response(prompt, stream=stream)

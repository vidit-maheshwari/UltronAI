# coder_agent.py
from agno.storage.sqlite import SqliteStorage
from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.file import FileTools
from agno.tools import tool
from pathlib import Path
import dotenv
import os

dotenv.load_dotenv()

class CoderAgentNode:
    def __init__(self, agent_id="coder_agent", db_file="agents.db", table_name="coder_sessions", base_dir: Path = None):
        self.storage = SqliteStorage(table_name=table_name, db_file=db_file)
        self.agent_id = agent_id
        self.base_dir = base_dir or Path.cwd()
        self.file_tools = FileTools(base_dir=self.base_dir)
        
        @tool(show_result=True)
        def write_code_file(file_name: str, code: str, language: str = "python") -> str:
            """Write code to a file with proper extension"""
            try:
                extensions = {
                    "python": ".py", "javascript": ".js", "typescript": ".ts",
                    "java": ".java", "cpp": ".cpp", "c": ".c", "html": ".html",
                    "css": ".css", "sql": ".sql", "shell": ".sh", "json": ".json"
                }
                
                if not any(file_name.endswith(ext) for ext in extensions.values()):
                    file_name += extensions.get(language.lower(), ".py")
                
                file_path = self.base_dir / file_name
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(code)
                
                return f"✅ Code written to {file_name}"
            except Exception as e:
                return f"❌ Error: {str(e)}"
        
#         @tool(show_result=True)
#         def analyze_requirements(task_description: str) -> str:
#             """Analyze coding task and return requirements"""
#             analysis = f"""
# 📋 Task Analysis: {task_description}

# Based on the task, I'll need to:
# 1. Identify the programming language and framework
# 2. List required dependencies
# 3. Plan the code structure
# 4. Consider error handling and best practices

# This analysis will help other agents understand what needs to be done.
# """
#             return analysis
        
        self.write_code_file = write_code_file
        # self.analyze_requirements = analyze_requirements
        
        self.model = Groq(id="deepseek-r1-distill-llama-70b")
        self.agent = Agent(
            model=self.model,
            tools=[self.write_code_file],
            storage=self.storage,
            agent_id=self.agent_id,
            show_tool_calls=True,
            markdown=True,
            instructions="""You are a specialized coding agent. Your job is ONLY to:
1. Write clean, well-documented code
2. Create files with proper structure
3. Analyze coding requirements
4. Follow best practices

Do NOT try to install packages, run code, or handle errors - other agents will do that.
Focus only on writing quality code and saving it to files."""
        )
    
    def run(self, prompt: str, stream: bool = True) -> str:
        return self.agent.print_response(prompt, stream=stream)
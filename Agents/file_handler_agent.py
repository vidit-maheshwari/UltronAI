from agno.storage.sqlite import SqliteStorage
from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.file import FileTools
from agno.tools import tool
from pathlib import Path
import dotenv
import os

dotenv.load_dotenv()


class FileAgentNode:
    def __init__(
        self, 
        agent_id="file_agent", 
        name: str = "File Handler Agent",  # Add this parameter
        role: str = "File Operations Specialist",
        db_file="agents.db", 
        table_name="agent_sessions", 
        base_dir: Path = None
    ):
        self.name = name  # Add this line
        self.role = role
        # Create SqliteStorage for agent sessions
        self.storage = SqliteStorage(table_name=table_name, db_file=db_file)
        self.agent_id = agent_id

        self.file_tools = FileTools(base_dir=base_dir)

        @tool(show_result=True, stop_after_tool_call=True)
        def delete_file(file_name: str) -> str:
            file_path = self.file_tools.base_dir.joinpath(file_name)
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
                return f"Deleted file: {file_name}"
            return f"File {file_name} does not exist"

        self.delete_file = delete_file

        self.model = Groq(id="deepseek-r1-distill-llama-70b")

        self.agent = Agent(
            model=self.model,
            tools=[self.file_tools, self.delete_file],
            storage=self.storage,
            agent_id=self.agent_id,
            show_tool_calls=True,
            markdown=True,
        )

    def run(self, prompt: str, stream: bool = True) -> str:
        return self.agent.print_response(prompt, stream=stream)

# Usage
# node = FileAgentNode(base_dir=Path("/tmp"))
# print(node.run("Save the text 'Hello World' to a file named example.txt"))



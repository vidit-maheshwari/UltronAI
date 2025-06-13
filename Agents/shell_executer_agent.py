from agno.agent import Agent
from agno.tools.shell import ShellTools
from agno.storage.sqlite import SqliteStorage as SqlAgentStorage
from agno.models.groq import Groq
import dotenv
import os

dotenv.load_dotenv()


class ShellAgentNode:
    def __init__(
        self,
        agent_id: str = "default_shell_agent",
        db_file: str = "agents.db",
        table_name: str = "multi_agent_memory",
        model_id: str = "deepseek-r1-distill-llama-70b",
        show_tool_calls: bool = True,
        markdown: bool = True,
    ):
        # Setup persistent storage for agent sessions
        self.storage = SqlAgentStorage(table_name=table_name, db_file=db_file)
        self.agent_id = agent_id

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
        )

    def run(self, prompt: str, stream: bool = True) -> str:
        # Agent will handle memory/session internally
        return self.agent.print_response(prompt, stream=stream)


# Usage example:
# shell_node = ShellAgentNode(agent_id="shell_node_1")
# print(shell_node.run("List files in the current directory"))

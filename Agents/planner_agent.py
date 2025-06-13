from agno.agent import Agent
from agno.models.groq import Groq
from agno.storage.sqlite import SqliteStorage as SqlAgentStorage
from agno.utils.log import log_info
from typing import List, Dict, Any
import dotenv
import os

dotenv.load_dotenv()


class PlannerAgentNode:
    def __init__(
        self,
        agent_id: str = "planner_agent",
        db_file: str = "agents.db",
        table_name: str = "multi_agent_memory",
        model_name: str = "deepseek-r1-distill-llama-70b",
        markdown: bool = True,
    ):
        self.storage = SqlAgentStorage(table_name=table_name, db_file=db_file)
        self.agent_id = agent_id

        self.agent = Agent(
            model=Groq(id=model_name),
            storage=self.storage,
            agent_id=self.agent_id,
            show_tool_calls=False,
            markdown=markdown,
        )

    def plan(self, task: str) -> List[Dict[str, Any]]:
        """Plans a task by breaking it into subtasks with assigned agents."""
        planning_prompt = f"""
        You are the Planner Agent in a multi-agent system. Your job is to decompose the following task into a list of structured subtasks.
        Each subtask should have:
        - a description
        - the name of the specialized agent to handle it (choose from: file_agent, shell_agent, search_agent, research_agent, coder_agent, executor_agent, local_error_resolver, installer_agent)

        Task: {task}

        Format your output as a JSON list of subtasks:
        [
        {{
            "agent": "coder_agent",
            "description": "Generate a Python script to scrape a website"
        }},
        ...
        ]
        """

        # Use get_response instead of calling the Agent object
        response = self.agent.print_response(planning_prompt)

        try:
            subtasks = eval(response.content)  # You can also use `json.loads()` for safety
            return subtasks
        except Exception as e:
            log_info(f"Failed to parse plan: {e}")
            return []


    def execute_plan(self, subtasks: List[Dict[str, Any]], agents: Dict[str, Any]):
        for i, subtask in enumerate(subtasks, 1):
            agent_key = subtask["agent"]
            prompt = subtask["description"]

            log_info(f"\n🔧 Executing Subtask {i}: {prompt} with [{agent_key}]")
            if agent_key in agents:
                result = agents[agent_key].run(prompt)
                log_info(f"✅ Result: {result}")
            else:
                log_info(f"⚠️ Agent '{agent_key}' not found!")

# Agents/error_resolver.py

from agno.agent import Agent
from agno.models.groq import Groq
from agno.storage.sqlite import SqliteStorage
from agno.utils.log import log_info
import dotenv
import json
import re
from typing import Dict, Any, List
from shared_state import SharedState  # Import SharedState from shared_state.py

dotenv.load_dotenv()


class ErrorResolverAgentNode:
    def __init__(
        self,
        agent_id: str = "error_resolver_agent",
        db_file: str = "agents.db",
        table_name: str = "error_resolver_sessions",
    ):
        self.storage = SqliteStorage(table_name=table_name, db_file=db_file)
        self.agent_id = agent_id

        self.agent = Agent(
            model=Groq(id="deepseek-r1-distill-llama-70b"),
            storage=self.storage,
            agent_id=self.agent_id,
            show_tool_calls=False,
            instructions="""You are an expert AI Error Resolution Specialist. Your job is to analyze a failed task
            and create a new JSON array plan to fix the error, using a strict "Command Language".

            **Command Language Reference:**
            - `{"agent": "file_agent", "description": "CREATE EMPTY FILE 'filename.ext'"}`
            - `{"agent": "shell_agent", "description": "mkdir -p directory_name"}`
            - `{"agent": "shell_agent", "description": "executable_command_string"}`
            - `{"agent": "coder_agent", "description": "Generate code for 'filename.ext' that..."}`
            - `{"agent": "file_agent", "description": "SAVE CODE TO 'filename.ext'"}`

            **Analysis Logic:**
            - If a shell command like `wget` or `brew` fails with "command not found", check the OS and suggest an alternative (e.g., use `curl` instead of `wget`).
            - If a file operation fails because a directory doesn't exist, use the `shell_agent` with `mkdir -p` to create it.
            - If a command fails due to permissions, do not attempt to change permissions. Instead, create a plan with the agent `human_intervention` and describe the problem clearly.

            Your output MUST be ONLY a valid JSON array of subtasks. No other text.
            """
        )

    def _parse_fix_plan_from_response(self, response: str) -> List[Dict[str, Any]]:
        """Parses a JSON array of subtasks from the LLM's response."""
        try:
            match = re.search(r'\[\s*\{[\s\S]*?\}\s*\]', response, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return []
        except Exception as e:
            log_info(f"Error parsing fix plan: {e}")
            return []

    def run(self, shared_state: 'SharedState') -> List[Dict[str, Any]]:
        """
        Analyzes an error from the shared state and returns a new plan to fix it.
        """
        
        error_context_prompt = f"""
        An error has occurred. Analyze the situation and create a new plan to resolve it.

        **Error Context:**
        - **Original Task:** {shared_state.original_task}
        - **Last Error Message:** {shared_state.last_execution_error}
        - **Last Output:** {shared_state.last_execution_output}
        - **Project Directory:** {shared_state.project_directory}
        - **History (last 5 actions):**
        {"\n".join([f"  - {h}" for h in shared_state.history[-5:]])}

        **Your Task:**
        Based on the error, create a new plan as a JSON array to fix the problem.
        Return ONLY the JSON array.
        """

        try:
            log_info("Error Resolver Agent is creating a fix plan...")
            response = self.agent.run(error_context_prompt)
            
            # --- THIS IS THE FIX ---
            content = response.content if hasattr(response, 'content') else str(response)

            fix_plan = self._parse_fix_plan_from_response(content)

            if not fix_plan:
                log_info("Error resolver failed to generate a valid fix plan.")
                return [{"agent": "human_intervention", "description": "Automatic error resolution failed. Please review the state."}]
            
            log_info(f"Error resolver created a new plan with {len(fix_plan)} steps.")
            return fix_plan

        except Exception as e:
            log_info(f"A critical error occurred in the ErrorResolverAgentNode: {e}")
            return [{"agent": "human_intervention", "description": f"Critical failure in error resolver: {e}"}]
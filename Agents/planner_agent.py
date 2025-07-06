# Agents/planner_agent.py

from agno.agent import Agent
from agno.models.groq import Groq
from agno.storage.sqlite import SqliteStorage as SqlAgentStorage
from agno.utils.log import log_info
from typing import List, Dict, Any
import dotenv
import json
import re

dotenv.load_dotenv()


class PlannerAgentNode:
    def __init__(
        self,
        agent_id: str = "planner_agent",
        db_file: str = "agents.db",
        table_name: str = "multi_agent_memory",
        model_name: str = "deepseek-r1-distill-llama-70b",
    ):
        self.storage = SqlAgentStorage(table_name=table_name, db_file=db_file)
        self.agent_id = agent_id

        self.agent = Agent(
            model=Groq(id=model_name),
            storage=self.storage,
            agent_id=self.agent_id,
            show_tool_calls=False,
            instructions="""You are the master Planner Agent. Your job is to create a JSON array of subtasks.
            You MUST use the following strict "Command Language" for the 'description' field.

            **Command Language Reference:**

            1.  **To read an existing file's content into memory:**
                `{"agent": "file_agent", "description": "READ FILE 'filename.ext'"}`

            2.  **To create a new, empty file:**
                `{"agent": "file_agent", "description": "CREATE EMPTY FILE 'filename.ext'"}`

            3.  **To generate new code or modify existing code for a file:**
                `{"agent": "coder_agent", "description": "Generate code for 'filename.ext' that does..."}`
                (This agent will automatically receive the file's current content if it has been read).

            4.  **To save previously generated code to a file:**
                `{"agent": "file_agent", "description": "SAVE CODE TO 'filename.ext'"}`

            5.  **To run a shell command:**
                `{"agent": "shell_agent", "description": "executable_command_string"}`

            **CRITICAL WORKFLOW LOGIC:**
            - **If the task is to modify an existing project, your FIRST steps must be to use the `READ FILE` command for every file that needs to be changed.**
            - Only after reading the files can you call the `coder_agent` to modify the code.
            - If you are creating a new project, do not use `READ FILE`. Start by creating the files.
            - After ALL code is generated, create tasks to `SAVE CODE` for each modified file.
            - Finally, run any necessary shell commands for testing or execution.

            Your output MUST be ONLY the JSON array. No other text.
            """
        )
    def _parse_plan_from_response(self, response: str) -> List[Dict[str, Any]]:
        """A simplified parser to extract a JSON array from the LLM's response."""
        try:
            # Find the JSON array using a regular expression
            match = re.search(r'\[\s*\{[\s\S]*?\}\s*\]', response, re.DOTALL)
            if match:
                json_string = match.group(0)
                return json.loads(json_string)
            else:
                log_info("No valid JSON array found in the planner's response.")
                return []
        except json.JSONDecodeError as e:
            log_info(f"Error decoding JSON from planner response: {e}")
            return []
        except Exception as e:
            log_info(f"An unexpected error occurred while parsing the plan: {e}")
            return []

    def plan(self, current_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Creates a plan based on the current state of the system.
        
        Args:
            current_state (Dict[str, Any]): The full context from the SharedState object.

        Returns:
            List[Dict[str, Any]]: A list of subtasks.
        """
        
        planning_prompt = f"""
        Given the current state of the project, create the next set of subtasks.

        **Current Project State:**
        - **Original Task:** {current_state.get('original_task')}
        - **Current Status:** {current_state.get('current_status')}
        - **Project Directory:** {current_state.get('project_directory', 'Not created yet.')}
        - **Files Created:** {current_state.get('created_files', 'None')}
        - **Last Execution Error:** {current_state.get('last_execution_error', 'None')}
        - **Execution History:**
        {"\n".join([f"  - {h}" for h in current_state.get('history', [])[-5:]])}

        **Your Task:**
        Analyze the state and provide the next subtasks as a JSON array. Remember the workflow logic:
        1. Create project structure with `file_agent`.
        2. Generate code with `coder_agent`.
        3. Save code to files with `file_agent`.
        4. Install dependencies and run with `shell_agent`.

        Return ONLY the JSON array.
        """

        try:
            log_info("Planner agent is creating a plan...")
            
            response = self.agent.run(planning_prompt)
            
            # --- THIS IS THE FIX ---
            # Access the content of the RunResponse object via its .content attribute
            content = response.content if hasattr(response, 'content') else str(response)
            
            log_info(f"Raw response from planner LLM: {content[:300]}...")

            subtasks = self._parse_plan_from_response(content)
            
            if not subtasks:
                log_info("Planner failed to generate a valid plan.")
                return []

            log_info(f"Planner created a new plan with {len(subtasks)} steps.")
            return subtasks
                
        except Exception as e:
            log_info(f"A critical error occurred in the plan method: {e}")
            return []
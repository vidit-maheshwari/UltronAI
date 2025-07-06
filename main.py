# main.py

import json
from typing import Dict, Any, List
from pathlib import Path
import re

# agent imports
from Agents.prompt_refiner import PromptRefiner
from shared_state import SharedState
from Agents.environment_check_agent import EnvironmentCheckAgent
from Agents.human_intervention_agent import HumanInterventionAgent
from Agents.file_handler_agent import FileAgentNode
from Agents.shell_executer_agent import ShellAgentNode
from Agents.planner_agent import PlannerAgentNode
from Agents.coder_agent import CoderAgentNode
from Agents.web_search import WebSearchAgentNode
from Agents.error_resolver import ErrorResolverAgentNode


class MultiAgentSystem:
    def __init__(self):
        # ... (__init__ is the same)
        self.agents = {
            "file_agent": FileAgentNode(),
            "shell_agent": ShellAgentNode(),
            "coder_agent": CoderAgentNode(),
            "web_search_agent": WebSearchAgentNode(),
            "error_resolver_agent": ErrorResolverAgentNode(),
            "planner_agent": PlannerAgentNode(),
            "environment_check_agent": EnvironmentCheckAgent(),
            "human_intervention_agent": HumanInterventionAgent(),
        }
        self.prompt_refiner = PromptRefiner()


    def execute_task(self, task: str, required_tools: List[str] = None):
        # ... (initial part of the method is the same)
        refined_task = self.prompt_refiner.refine(task)
        print(f"Original task: '{task}'")
        print(f"Refined task: '{refined_task}'")
        print(f"🚀 Starting task execution...")

        if required_tools:
            env_status = self.agents["environment_check_agent"].check_dependencies(required_tools)
            missing_tools = [tool for tool, installed in env_status.items() if not installed]
            if missing_tools:
                problem = f"The following required tools are missing from your system: {', '.join(missing_tools)}. Please install them and try again."
                help_message = self.agents["human_intervention_agent"].request_help(problem)
                print(help_message)
                return

        shared_state = SharedState(original_task=refined_task)

        # --- NEW: CONTEXT PARSING ---
        # Check if the user specified an existing project path
        path_match = re.search(r"project at '([^']*)'", refined_task)
        if path_match:
            project_path = Path(path_match.group(1))
            if project_path.exists() and project_path.is_dir():
                shared_state.set_project_directory(project_path, from_prompt=True)
            else:
                print(f"⚠️ Warning: Provided path '{project_path}' does not exist. A new project will be created.")
        # --- END OF NEW LOGIC ---

        while shared_state.current_status not in ["completed", "failed"]:
            current_status = shared_state.current_status
            print(f"\nCurrent Status: {current_status.upper()}")

            try:
                if current_status == "planning":
                    plan = self.agents["planner_agent"].plan(shared_state.get_full_context())
                    
                    # --- THIS IS THE FIX ---
                    # Check if planning was successful before proceeding.
                    if not plan:
                        error_msg = "The Planner Agent failed to create a plan. This could be due to a connection issue or a complex task. Halting execution."
                        print(f"  -> ❌ {error_msg}")
                        shared_state.log_execution_output(None, error_msg)
                        shared_state.update_status("failed")
                        continue
                    # --- END OF FIX ---

                    shared_state.update_plan(plan)
                    shared_state.update_status("executing")

                elif current_status == "executing":
                    # ... (the rest of the loop is the same as the previous final version)
                    if not shared_state.current_plan:
                        shared_state.update_status("completed")
                        continue

                    subtask = shared_state.current_plan.pop(0)

                    if not isinstance(subtask, dict) or "agent" not in subtask or "description" not in subtask:
                        error_msg = f"Malformed subtask received: {subtask}. Halting execution."
                        print(f"  -> ❌ {error_msg}")
                        shared_state.log_execution_output(None, error_msg)
                        shared_state.update_status("failed")
                        continue

                    agent_key = subtask["agent"]
                    prompt = subtask["description"]

                    print(f"  -> Executing subtask: {prompt}")
                    print(f"  -> With Agent: {agent_key}")

                    if agent_key == "human_intervention":
                        problem = prompt
                        help_message = self.agents["human_intervention_agent"].request_help(problem)
                        print(help_message)
                        shared_state.update_status("failed")
                        continue

                    if agent_key in self.agents:
                        result = self.agents[agent_key].run(prompt, shared_state)
                        
                        if result.get("status") == "error":
                            shared_state.log_execution_output(
                                result.get("output"),
                                result.get("error", "Unknown error")
                            )
                        else:
                            if "project_directory" in result:
                                shared_state.set_project_directory(Path(result["project_directory"]))
                            if "created_files" in result:
                                for f in result["created_files"]:
                                    shared_state.add_created_file(f)
                            if "generated_code" in result and "filename" in result:
                                shared_state.add_generated_code(
                                    result["filename"],
                                    result["generated_code"]
                                )
                            shared_state.log_execution_output(result.get("output"))
                    else:
                        error_msg = f"Agent '{agent_key}' not found!"
                        shared_state.log_execution_output(None, error_msg)

                elif current_status == "error":
                    print("  -> An error occurred. Engaging Error Resolver Agent.")
                    fix_plan = self.agents["error_resolver_agent"].run(shared_state)
                    
                    shared_state.current_plan = fix_plan + shared_state.current_plan
                    shared_state.update_status("executing")

            except Exception as e:
                print(f"💥 A critical error occurred in the main loop: {e}")
                shared_state.update_status("failed")

        print("\n" + "="*50)
        print("✅ Task Execution Finished!")
        print(f"Final Status: {shared_state.current_status.upper()}")
        print("\nExecution History:")
        for item in shared_state.history:
            print(f"- {item}")
        print("="*50)

        # Return the final state
        return shared_state.get_full_context()

# --- Main Execution Block ---
if __name__ == "__main__":
    system = MultiAgentSystem()

    required_tools = ["curl"] 

    task = """
    Give me all news 
    """

    final_state = system.execute_task(task, required_tools=required_tools)

    print("\nFinal Shared State:")
    def json_default(o):
        if isinstance(o, Path):
            return str(o)
        raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

    print(json.dumps(final_state, indent=2, default=json_default))
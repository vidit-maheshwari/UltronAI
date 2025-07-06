# main.py

import json
from typing import Dict, Any, List
from pathlib import Path
import re
import time

# --- NEW: Rich Imports for beautiful terminal UI ---
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.spinner import Spinner

# --- (Other imports are the same) ---
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
        # --- NEW: Initialize Rich Console ---
        self.console = Console()

    def execute_task(self, task: str, required_tools: List[str] = None):
        """
        Executes a task using a dynamic, state-driven loop with a rich terminal UI.
        """
        # Initialize Rich Console
        self.console = Console()
        
        # Print initial task panel
        self.console.print(Panel(f"[bold cyan]Original Task:[/bold cyan]\n{task}", title="[bold green]🚀 Starting Task Execution[/bold green]", border_style="green"))
        
        # Refine and set up initial state
        refined_task = self.prompt_refiner.refine(task)
        shared_state = SharedState(original_task=refined_task)

        # Pre-flight Check for required tools
        if required_tools:
            self.console.print("[bold yellow]Running pre-flight environment check...[/bold yellow]")
            env_status = self.agents["environment_check_agent"].check_dependencies(required_tools)
            missing_tools = [tool for tool, installed in env_status.items() if not installed]
            if missing_tools:
                problem = f"The following required tools are missing from your system: {', '.join(missing_tools)}. Please install them and try again."
                help_message = self.agents["human_intervention_agent"].request_help(problem)
                self.console.print(Panel(help_message, title="[bold red]❌ Environment Check Failed[/bold red]", border_style="red"))
                return # Stop execution

        # Parse initial project directory from the task if provided
        path_match = re.search(r"project at '([^']*)'", refined_task)
        if path_match:
            project_path = Path(path_match.group(1))
            if project_path.exists() and project_path.is_dir():
                shared_state.set_project_directory(project_path, from_prompt=True)
                self.console.print(f"[bold green]Working on existing project at:[/] {project_path}")
            else:
                self.console.print(f"⚠️ [bold yellow]Warning:[/bold yellow] Provided path '{project_path}' does not exist. A new project will be created.")

        # Main execution loop with Rich Live display
        with Live(console=self.console, screen=False, auto_refresh=True, vertical_overflow="visible") as live:
            while shared_state.current_status not in ["completed", "failed"]:
                current_status = shared_state.current_status
                
                try:
                    if current_status == "planning":
                        live.update(Spinner("dots", text="[bold blue] 🧠 Planner agent is creating a plan...[/bold blue]"))
                        plan = self.agents["planner_agent"].plan(shared_state.get_full_context())
                        
                        if not plan:
                            error_msg = "The Planner Agent failed to create a plan. This could be due to a connection issue or a complex task. Halting execution."
                            live.update(Panel(f"[bold red]❌ {error_msg}[/bold red]", border_style="red"))
                            shared_state.log_execution_output(None, error_msg)
                            shared_state.update_status("failed")
                            continue

                        shared_state.update_plan(plan)
                        
                        table = Table(title="[bold bright_magenta]📋 Execution Plan[/bold bright_magenta]", show_header=True, header_style="bold magenta")
                        table.add_column("Step", style="dim", width=6)
                        table.add_column("Agent", style="cyan")
                        table.add_column("Task Description")
                        for i, p in enumerate(plan, 1):
                            table.add_row(str(i), p['agent'], p['description'])
                        self.console.print(table)

                        shared_state.update_status("executing")
                        time.sleep(1)

                    elif current_status == "executing":
                        if not shared_state.current_plan:
                            shared_state.update_status("completed")
                            continue

                        subtask = shared_state.current_plan.pop(0)

                        if not isinstance(subtask, dict) or "agent" not in subtask or "description" not in subtask:
                            error_msg = f"Malformed subtask received: {subtask}. Halting execution."
                            live.update(Panel(f"[bold red]❌ {error_msg}[/bold red]", border_style="red"))
                            shared_state.log_execution_output(None, error_msg)
                            shared_state.update_status("failed")
                            continue

                        agent_key = subtask["agent"]
                        prompt = subtask["description"]

                        live.update(Spinner("dots", text=f" [bold blue]🏃 {agent_key}[/bold blue] is executing: [i]'{prompt[:70]}...'[/i]"))

                        if agent_key == "human_intervention":
                            problem = prompt
                            help_message = self.agents["human_intervention_agent"].request_help(problem)
                            self.console.print(Panel(help_message, title="[bold red]❗ Human Intervention Required[/bold red]", border_style="red"))
                            shared_state.update_status("failed")
                            continue

                        if agent_key in self.agents:
                            result = self.agents[agent_key].run(prompt, shared_state)
                            
                            if result.get("status") == "error":
                                shared_state.log_execution_output(result.get("output"), result.get("error", "Unknown error"))
                            else:
                                if "project_directory" in result and result["project_directory"]:
                                    shared_state.set_project_directory(Path(result["project_directory"]))
                                if "created_files" in result:
                                    for f in result["created_files"]:
                                        shared_state.add_created_file(f)
                                if "generated_code" in result and "filename" in result:
                                    shared_state.add_generated_code(result["filename"], result["generated_code"])
                                shared_state.log_execution_output(result.get("output"))
                        else:
                            error_msg = f"Agent '{agent_key}' not found!"
                            shared_state.log_execution_output(None, error_msg)

                    elif current_status == "error":
                        live.update(Spinner("dots", text="[bold red]🔧 An error occurred. Engaging Error Resolver Agent...[/bold red]"))
                        fix_plan = self.agents["error_resolver_agent"].run(shared_state)
                        
                        if fix_plan and fix_plan[0]['agent'] != 'human_intervention':
                            self.console.print("[bold orange3]🛠️ New Fix Plan Generated:[/bold orange3]")
                            table = Table(show_header=True, header_style="bold orange3")
                            table.add_column("Step", style="dim", width=6)
                            table.add_column("Agent", style="cyan")
                            table.add_column("Task Description")
                            for i, p in enumerate(fix_plan, 1):
                                table.add_row(str(i), p.get('agent', 'N/A'), p.get('description', 'N/A'))
                            self.console.print(table)
                        
                        shared_state.current_plan = fix_plan + shared_state.current_plan
                        shared_state.update_status("executing")

                except Exception as e:
                    self.console.print(f"💥 [bold red]A critical error occurred in the main loop: {e}[/bold red]")
                    shared_state.update_status("failed")

        self.console.print(Panel(f"[bold green]✅ Task Execution Finished! Final Status: {shared_state.current_status.upper()}[/bold green]", title="[bold green]Completion[/bold green]", border_style="green"))
        return shared_state.get_full_context()

# --- Main Execution Block ---
if __name__ == "__main__":
    system = MultiAgentSystem()

    # Define the task and any command-line tools it might need
    required_tools = ["curl"] 

    task = """
    give me today's new headlines with 50 words summary.
    Save the headlines to a file named 'headlines.txt' in the project folder.
    use web agent to search for the latest news.
    """

    final_state = system.execute_task(task, required_tools=required_tools)

    print("\nFinal Shared State:")
    def json_default(o):
        if isinstance(o, Path):
            return str(o)
        raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

    print(json.dumps(final_state, indent=2, default=json_default))
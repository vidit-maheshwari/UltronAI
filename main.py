# main.py

import json
from typing import Dict, Any, List
from pathlib import Path
import re
import time

# Utility and State Imports
from Agents.prompt_refiner import PromptRefiner
from shared_state import SharedState
from Agents.environment_check_agent import EnvironmentCheckAgent
from Agents.human_intervention_agent import HumanInterventionAgent
from Agents.document_reader_agent import DocumentReaderAgent

# Agent Imports
from Agents.file_handler_agent import FileAgentNode
from Agents.shell_executer_agent import ShellAgentNode
from Agents.planner_agent import PlannerAgentNode
from Agents.coder_agent import CoderAgentNode
from Agents.web_search import WebSearchAgentNode
from Agents.error_resolver import ErrorResolverAgentNode

# Rich for UI
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.spinner import Spinner
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.layout import Layout
from rich.columns import Columns
from rich.text import Text
from rich.align import Align
from rich.rule import Rule
from rich.status import Status
from rich.syntax import Syntax
from rich.markdown import Markdown

class MultiAgentSystem:
    def __init__(self):
        """Initializes all agents and the console."""
        self.agents = {
            "file_agent": FileAgentNode(),
            "shell_agent": ShellAgentNode(),
            "coder_agent": CoderAgentNode(),
            "web_search_agent": WebSearchAgentNode(),
            "error_resolver_agent": ErrorResolverAgentNode(),
            "planner_agent": PlannerAgentNode(),
            "environment_check_agent": EnvironmentCheckAgent(),
            "human_intervention_agent": HumanInterventionAgent(),
            "document_reader_agent": DocumentReaderAgent(),
        }
        self.prompt_refiner = PromptRefiner()
        self.console = Console()

    def execute_task(self, task: str, required_tools: List[str] = None):
        """
        Executes a task from start to finish using a dynamic, state-driven loop
        with pre-flight checks and a rich terminal UI.
        """
        # Enhanced header with gradient-like styling
        self.console.print()
        self.console.print(Rule("[bold blue]UltronAI Multi-Agent System[/bold blue]", style="blue"))
        self.console.print()
        
        # Show system info
        system_info = Columns([
            "[bold cyan]🤖 Agents:[/bold cyan] 9 specialized agents",
            "[bold cyan]🧠 AI Models:[/bold cyan] Groq DeepSeek",
            "[bold cyan]⚡ Status:[/bold cyan] Ready"
        ], equal=True, expand=True)
        self.console.print(system_info)
        self.console.print()
        
        # Enhanced task display
        task_panel = Panel(
            f"[bold cyan]📋 Task:[/bold cyan]\n{task}",
            title="[bold green]🚀 Task Execution Started[/bold green]",
            border_style="green",
            padding=(1, 2)
        )
        self.console.print(task_panel)
        
        refined_task = self.prompt_refiner.refine(task)
        shared_state = SharedState(original_task=refined_task)
        
        # Show system status
        self.console.print(f"[dim]🔄 Refined task: {refined_task[:100]}{'...' if len(refined_task) > 100 else ''}[/dim]")
        self.console.print()

        if required_tools:
            self.console.print("[bold yellow]Running pre-flight environment check...[/bold yellow]")
            env_status = self.agents["environment_check_agent"].check_dependencies(required_tools)
            missing_tools = [tool for tool, installed in env_status.items() if not installed]
            if missing_tools:
                problem = f"The following required tools are missing from your system: {', '.join(missing_tools)}. Please install them and try again."
                help_message = self.agents["human_intervention_agent"].request_help(problem)
                self.console.print(Panel(help_message, title="[bold red]❌ Environment Check Failed[/bold red]", border_style="red"))
                return

        # Check if we already have document content (from previous runs)
        if hasattr(shared_state, 'document_content') and shared_state.document_content:
            self.console.print(f"[bold green]✅ Document content already available ({len(shared_state.document_content)} characters)[/bold green]")

        # Enhanced document reading section
        path_match = re.search(r"named\s+['\"]?([\w\._-]+)['\"]?", refined_task)
        if path_match:
            file_name = path_match.group(1)
            desktop_path = Path.home() / "Desktop"
            file_path = desktop_path / file_name
            
            # Enhanced file reading display
            with Status("[bold yellow]📖 Reading document...", spinner="dots"):
                self.console.print(f"[yellow]📄 Found document: [bold]{file_name}[/bold] at {file_path}[/yellow]")
                read_result = self.agents["document_reader_agent"].run(str(file_path))
            
            if read_result.get("status") == "success":
                content_length = len(read_result["file_content"])
                shared_state.set_document_content(read_result["file_content"])
                
                # Enhanced success display
                success_panel = Panel(
                    f"[bold green]✅ Document loaded successfully![/bold green]\n"
                    f"[dim]📊 Content: {content_length:,} characters[/dim]\n"
                    f"[dim]📁 File: {file_name}[/dim]",
                    title="[bold green]📖 Document Read[/bold green]",
                    border_style="green",
                    padding=(1, 2)
                )
                self.console.print(success_panel)
            else:
                error_msg = f"Failed to read document: {read_result.get('error')}"
                error_panel = Panel(
                    f"[bold red]❌ {error_msg}[/bold red]",
                    title="[bold red]📖 Document Read Failed[/bold red]",
                    border_style="red",
                    padding=(1, 2)
                )
                self.console.print(error_panel)
                shared_state.update_status("failed")
        
        self.console.print()

        # Initialize progress tracking
        total_steps = 0
        completed_steps = 0
        
        with Live(console=self.console, screen=False, auto_refresh=True, vertical_overflow="visible") as live:
            while shared_state.current_status not in ["completed", "failed"]:
                current_status = shared_state.current_status
                
                try:
                    if current_status == "planning":
                        # Enhanced planning display
                        with Status("[bold blue]🧠 Planning phase...", spinner="dots"):
                            live.update(Text("[bold blue]🧠 Planner agent is analyzing task and creating execution plan...[/bold blue]"))
                            plan = self.agents["planner_agent"].plan(shared_state.get_full_context())
                        
                        if not plan:
                            error_msg = "The Planner Agent failed to create a plan. This could be a connection issue or a complex task. Halting."
                            error_panel = Panel(
                                f"[bold red]❌ {error_msg}[/bold red]",
                                title="[bold red]🧠 Planning Failed[/bold red]",
                                border_style="red",
                                padding=(1, 2)
                            )
                            live.update(error_panel)
                            shared_state.log_execution_output(None, error_msg)
                            shared_state.update_status("failed")
                            continue

                        shared_state.update_plan(plan)
                        total_steps = len(plan)
                        
                        # Enhanced plan display
                        plan_panel = Panel(
                            f"[bold bright_magenta]📋 Execution Plan Created[/bold bright_magenta]\n"
                            f"[dim]Total steps: {total_steps}[/dim]",
                            title="[bold bright_magenta]📋 Execution Plan[/bold bright_magenta]",
                            border_style="bright_magenta",
                            padding=(1, 2)
                        )
                        self.console.print(plan_panel)
                        
                        # Enhanced plan table
                        table = Table(
                            title="[bold bright_magenta]📋 Step-by-Step Plan[/bold bright_magenta]",
                            show_header=True,
                            header_style="bold magenta",
                            border_style="bright_magenta"
                        )
                        table.add_column("Step", style="dim", width=6, justify="center")
                        table.add_column("Agent", style="cyan", width=15)
                        table.add_column("Task Description", style="white")
                        table.add_column("Status", style="dim", width=10, justify="center")
                        
                        for i, p in enumerate(plan, 1):
                            table.add_row(
                                f"[bold]{i}[/bold]",
                                f"[bold]{p['agent']}[/bold]",
                                p['description'],
                                "[dim]⏳ Pending[/dim]"
                            )
                        self.console.print(table)
                        self.console.print()

                        shared_state.update_status("executing")
                        time.sleep(1)

                    elif current_status == "executing":
                        if not shared_state.current_plan:
                            shared_state.update_status("completed")
                            continue

                        subtask = shared_state.current_plan.pop(0)

                        if not isinstance(subtask, dict) or "agent" not in subtask or "description" not in subtask:
                            error_msg = f"Malformed subtask received: {subtask}. Halting execution."
                            error_panel = Panel(
                                f"[bold red]❌ {error_msg}[/bold red]",
                                title="[bold red]🚫 Execution Error[/bold red]",
                                border_style="red",
                                padding=(1, 2)
                            )
                            live.update(error_panel)
                            shared_state.log_execution_output(None, error_msg)
                            shared_state.update_status("failed")
                            continue

                        agent_key = subtask["agent"]
                        prompt = subtask["description"]
                        
                        # Calculate progress
                        completed_steps = total_steps - len(shared_state.current_plan)
                        current_step = completed_steps + 1
                        progress_percent = (completed_steps / total_steps) * 100

                        # Enhanced execution display with progress bar
                        progress_bar = "█" * int(progress_percent / 10) + "░" * (10 - int(progress_percent / 10))
                        execution_status = f"[bold blue]🏃 {agent_key}[/bold blue] | Step {current_step}/{total_steps} ({progress_percent:.1f}%)"
                        task_description = f"[i]'{prompt[:80]}{'...' if len(prompt) > 80 else ''}'[/i]"
                        progress_display = f"[green]{progress_bar}[/green] {progress_percent:.1f}%"
                        
                        live.update(Text(f"{execution_status}\n{progress_display}\n{task_description}"))

                        if agent_key == "human_intervention":
                            problem = prompt
                            help_message = self.agents["human_intervention_agent"].request_help(problem)
                            self.console.print(Panel(help_message, title="[bold red]❗ Human Intervention Required[/bold red]", border_style="red"))
                            shared_state.update_status("failed")
                            continue

                        if agent_key in self.agents:
                            result = self.agents[agent_key].run(prompt, shared_state)
                            
                            if result.get("status") == "error":
                                # Enhanced error display
                                error_panel = Panel(
                                    f"[bold red]❌ {result.get('error', 'Unknown error')}[/bold red]\n"
                                    f"[dim]Agent: {agent_key}[/dim]\n"
                                    f"[dim]Task: {prompt[:100]}{'...' if len(prompt) > 100 else ''}[/dim]",
                                    title="[bold red]❌ Execution Failed[/bold red]",
                                    border_style="red",
                                    padding=(1, 2)
                                )
                                self.console.print(error_panel)
                                shared_state.log_execution_output(result.get("output"), result.get("error", "Unknown error"))
                            else:
                                # Enhanced success display
                                success_info = []
                                
                                if "project_directory" in result and result["project_directory"]:
                                    shared_state.set_project_directory(Path(result["project_directory"]))
                                    success_info.append(f"📁 Project: {Path(result['project_directory']).name}")
                                
                                if "created_files" in result:
                                    for f in result["created_files"]:
                                        shared_state.add_created_file(f)
                                    success_info.append(f"📄 Files: {len(result['created_files'])} created")
                                
                                if "generated_code" in result and "filename" in result:
                                    shared_state.add_generated_code(result["filename"], result["generated_code"])
                                    code_size = len(result["generated_code"])
                                    success_info.append(f"💻 Code: {result['filename']} ({code_size:,} chars)")
                                
                                # Show success message
                                if success_info:
                                    success_panel = Panel(
                                        f"[bold green]✅ {agent_key} completed successfully![/bold green]\n"
                                        f"\n".join([f"[dim]{info}[/dim]" for info in success_info]),
                                        title="[bold green]✅ Step Completed[/bold green]",
                                        border_style="green",
                                        padding=(1, 2)
                                    )
                                    self.console.print(success_panel)
                                
                                shared_state.log_execution_output(result.get("output"))
                        else:
                            error_msg = f"Agent '{agent_key}' not found!"
                            error_panel = Panel(
                                f"[bold red]❌ {error_msg}[/bold red]",
                                title="[bold red]🚫 Agent Not Found[/bold red]",
                                border_style="red",
                                padding=(1, 2)
                            )
                            self.console.print(error_panel)
                            shared_state.log_execution_output(None, error_msg)

                    elif current_status == "error":
                        # Enhanced error resolution display
                        with Status("[bold red]🔧 Error resolution phase...", spinner="dots"):
                            live.update(Text("[bold red]🔧 An error occurred. Engaging Error Resolver Agent...[/bold red]"))
                            fix_plan = self.agents["error_resolver_agent"].run(shared_state)
                        
                        if not fix_plan or not all(isinstance(p, dict) and "agent" in p and "description" in p for p in fix_plan):
                            error_msg = f"Error Resolver created a malformed plan: {fix_plan}. Halting to prevent loop."
                            error_panel = Panel(
                                f"[bold red]❌ {error_msg}[/bold red]",
                                title="[bold red]🔧 Error Resolution Failed[/bold red]",
                                border_style="red",
                                padding=(1, 2)
                            )
                            live.update(error_panel)
                            shared_state.log_execution_output(None, error_msg)
                            shared_state.update_status("failed")
                            continue
                        
                        if fix_plan and fix_plan[0]['agent'] != 'human_intervention':
                            # Enhanced fix plan display
                            fix_panel = Panel(
                                f"[bold orange3]🛠️ Error Resolution Plan Generated[/bold orange3]\n"
                                f"[dim]Fix steps: {len(fix_plan)}[/dim]",
                                title="[bold orange3]🛠️ Error Resolution[/bold orange3]",
                                border_style="orange3",
                                padding=(1, 2)
                            )
                            self.console.print(fix_panel)
                            
                            # Enhanced fix plan table
                            table = Table(
                                title="[bold orange3]🛠️ Fix Plan Steps[/bold orange3]",
                                show_header=True,
                                header_style="bold orange3",
                                border_style="orange3"
                            )
                            table.add_column("Step", style="dim", width=6, justify="center")
                            table.add_column("Agent", style="cyan", width=15)
                            table.add_column("Task Description", style="white")
                            table.add_column("Type", style="dim", width=10, justify="center")
                            
                            for i, p in enumerate(fix_plan, 1):
                                table.add_row(
                                    f"[bold]{i}[/bold]",
                                    f"[bold]{p.get('agent', 'N/A')}[/bold]",
                                    p.get('description', 'N/A'),
                                    "[dim]🔧 Fix[/dim]"
                                )
                            self.console.print(table)
                            self.console.print()
                        
                        shared_state.current_plan = fix_plan + shared_state.current_plan
                        shared_state.update_status("executing")

                except Exception as e:
                    self.console.print(f"💥 [bold red]A critical error occurred in the main loop: {e}[/bold red]")
                    shared_state.update_status("failed")

        # Enhanced completion display
        self.console.print()
        self.console.print(Rule("[bold blue]Task Execution Summary[/bold blue]", style="blue"))
        self.console.print()
        
        # Calculate statistics
        total_files = len(shared_state.created_files) if hasattr(shared_state, 'created_files') else 0
        total_code = sum(len(code) for code in shared_state.generated_code.values()) if hasattr(shared_state, 'generated_code') else 0
        project_name = Path(shared_state.project_directory).name if shared_state.project_directory else "Unknown"
        
        # Create summary panel
        summary_content = f"""
[bold green]✅ Task Execution Completed![/bold green]

[bold]📊 Summary:[/bold]
• [dim]Status:[/dim] {shared_state.current_status.upper()}
• [dim]Project:[/dim] {project_name}
• [dim]Files Created:[/dim] {total_files}
• [dim]Code Generated:[/dim] {total_code:,} characters
• [dim]Document Content:[/dim] {len(shared_state.document_content) if hasattr(shared_state, 'document_content') and shared_state.document_content else 0:,} characters

[bold]📁 Output Location:[/bold]
{shared_state.project_directory if shared_state.project_directory else "No project directory"}
        """
        
        completion_panel = Panel(
            summary_content,
            title="[bold green]🎉 Task Completed Successfully[/bold green]",
            border_style="green",
            padding=(1, 2)
        )
        self.console.print(completion_panel)
        
        # Show final rule
        self.console.print()
        self.console.print(Rule("[bold blue]UltronAI Multi-Agent System[/bold blue]", style="blue"))
        self.console.print()
        
        return shared_state.get_full_context()


# --- Main Execution Block ---
if __name__ == "__main__":
    system = MultiAgentSystem()

    task = """
    my resume is in desktop named 'Himaja_Resume_4_2025.pdf', read it and make a Portfolio page for it.
    it should be in html format, css and javascript, it should be responsive and mobile friendly.
    it should be visually appealing and should have a nice UI.
    it should be a single page website.
    """
    
    # This task doesn't require external tools like curl, so we can omit the check.
    system.execute_task(task)
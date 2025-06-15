# Example usage
from Agents.file_handler_agent import FileAgentNode
from Agents.shell_executer_agent import ShellAgentNode
from Agents.planner_agent import PlannerAgentNode
from Agents.web_search import WebSearchAgentNode
from Agents.coder_agent import CoderAgentNode

# ... import others similarly

# Initialize all agent nodes (once)
agents = {
    "file_agent": FileAgentNode(agent_id="file_agent"),
    "shell_agent": ShellAgentNode(agent_id="shell_agent"),
    "web_search_agent": WebSearchAgentNode(agent_id="web_search_agent"),
    "coder_agent": CoderAgentNode(agent_id="coder_agent"),
}

# Instantiate the planner
planner = PlannerAgentNode(agent_id="planner_master")

# Input task
task = "write a prgram to make a bottol of cad  make necessary installations and save the file as stl file in local"

# Step 1: Plan the task
subtasks = planner.plan(task)

# Step 2: Execute the plan
planner.execute_plan(subtasks, agents)

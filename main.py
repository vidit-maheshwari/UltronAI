# Example usage
from Agents.file_handler_agent import FileAgentNode
from Agents.shell_executer_agent import ShellAgentNode
from Agents.planner_agent import PlannerAgentNode
# ... import others similarly

# Initialize all agent nodes (once)
agents = {
    "file_agent": FileAgentNode(agent_id="file_agent"),
    "shell_agent": ShellAgentNode(agent_id="shell_agent"),
    # Add the rest...
}

# Instantiate the planner
planner = PlannerAgentNode(agent_id="planner_master")

# Input task
task = "make a test.py and make a greeting function and execute it in the terminal"

# Step 1: Plan the task
subtasks = planner.plan(task)

# Step 2: Execute the plan
planner.execute_plan(subtasks, agents)

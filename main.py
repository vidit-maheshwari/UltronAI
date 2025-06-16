# Example usage
from Agents.file_handler_agent import FileAgentNode
from Agents.shell_executer_agent import ShellAgentNode
from Agents.planner_agent import PlannerAgentNode
from Agents.coder_agent import CoderAgentNode
from Agents.web_search import WebSearchAgentNode
from Agents.installer_agent import InstallerAgentNode
from Agents.executer_agent import ExecutorAgentNode
# ... import others similarly

main_agent = CoderAgentNode()


# Initialize all agent nodes (once)
agents = {
    "file_agent": FileAgentNode(agent_id="file_agent"),
    "shell_agent": ShellAgentNode(agent_id="shell_agent"),
    "coder_agent": CoderAgentNode(agent_id="coder_agent"),
    "web_search_agent": WebSearchAgentNode(agent_id="web_search_agent"),
    "installer_agent": InstallerAgentNode(agent_id="installer_agent"),
    "executor_agent": ExecutorAgentNode(agent_id="executor_agent"),
    # Add the rest...
}

# Instantiate the planner
planner = PlannerAgentNode(agent_id="planner_master")

# Input task
task = "check my system information and give me the output in a json format and save it in a file called system_configuration.json"

# Step 1: Plan the task
subtasks = planner.plan(task)

# Step 2: Execute the plan
planner.execute_plan(subtasks, agents)

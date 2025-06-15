from phi.agent import Agent
from phi.model.groq import GroqChat

from Agents.coder_agent import CoderAgentNode
from Agents.file_handler_agent import FileAgentNode
from Agents.shell_executer_agent import ShellAgentNode
from Agents.executer_agent import ExecutorAgentNode

# Groq model instance
groq_model = GroqChat(model="deepseek-coder", api_key="your_groq_key_or_env_var")

# Define each agent with model
coder_agent = Agent(
    name="Coder Agent",
    role="Writes and debugs code",
    run=CoderAgentNode(agent_id="coder_agent").run,
    model=groq_model,
)

file_agent = Agent(
    name="File Agent",
    role="Handles file operations",
    run=FileAgentNode(agent_id="file_agent").run,
    model=groq_model,
)

shell_agent = Agent(
    name="Shell Agent",
    role="Executes shell commands",
    run=ShellAgentNode(agent_id="shell_agent").run,
    model=groq_model,
)

executor_agent = Agent(
    name="Executor Agent",
    role="Runs and coordinates code execution",
    run=ExecutorAgentNode(agent_id="executor_agent").run,
    model=groq_model,
)

# Now the team itself
developer_team_agent = Agent(
    name="Developer Team",
    role="Full-stack developer team that codes, manages files, runs shells, and executes",
    team=[coder_agent, file_agent, shell_agent, executor_agent],
    model=groq_model,  # 👈 Optional but ensures team-wide default
    instructions=[
        "Use Coder Agent to generate or refactor code.",
        "Use File Agent to manage file creation and manipulation.",
        "Use Shell Agent to run system-level shell commands.",
        "Use Executor Agent to compile/run/test code and coordinate output.",
    ],
    show_tool_calls=True,
    markdown=True,
)

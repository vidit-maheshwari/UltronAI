from agno.team import Team
from agno.models.groq import Groq
from Agents.coder_agent import CoderAgentNode
from Agents.file_handler_agent import FileAgentNode
from Agents.shell_executer_agent import ShellAgentNode
from Agents.executer_agent import ExecutorAgentNode
 

coder_team = Team(
    model=Groq(id="deepseek-r1-distill-llama-70b"),
    members=[
        CoderAgentNode(agent_id="coder_agent"),
        FileAgentNode(agent_id="file_agent"),
        ShellAgentNode(agent_id="shell_agent"),
        ExecutorAgentNode(agent_id="executor_agent")
    ],
    show_tool_calls=True,
    markdown=True,
    description="A team of agents that can code,read files,rename files, create files, delete files, execute shell commands, navigate the file system, and execute code",
    name="Coder Team",
    mode='coordinate'
)


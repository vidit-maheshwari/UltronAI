from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.duckduckgo import DuckDuckGoTools

# Create a basic web search agent with Groq
web_search_agent = Agent(
    model=Groq(id="deepseek-r1-distill-llama-70b"),  # Recommended for general use
    tools=[DuckDuckGoTools()],
    show_tool_calls=True,
    markdown=True
)


# # Agents/web_search_agent.py

# from agno.agent import Agent
# from agno.models.groq import Groq
# from agno.tools.duckduckgo import DuckDuckGoTools
# import dotenv
# import os

# dotenv.load_dotenv()

# agent = Agent(
#     model=Groq(id="deepseek-r1-distill-llama-70b"),
#     tools=[DuckDuckGoTools()],
#     show_tool_calls=True,
#     markdown=True,
# )

# agent.print_response("Search for top 5 movies in India by box office collection", stream=False)

# Agents/web_search_agent.py

from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.storage.sqlite import SqliteStorage
from Agents.prompt_refiner import PromptRefiner
import dotenv
import os

dotenv.load_dotenv()


class WebSearchAgentNode:
    def __init__(self, agent_id="web_search_agent", db_file="agents.db", table_name="agent_sessions"):
        self.agent_id = agent_id

        # Initialize model
        self.model = Groq(id="deepseek-r1-distill-llama-70b")

        # Use DuckDuckGoTools (no setup required)
        self.search_tools = DuckDuckGoTools()

        # Optional storage for logging sessions
        self.storage = SqliteStorage(db_file=db_file, table_name=table_name)

        # Setup agent
        self.agent = Agent(
            model=self.model,
            tools=[self.search_tools],
            agent_id=self.agent_id,
            storage=self.storage,
            show_tool_calls=True,
            markdown=True,
        )

    def run(self, prompt: str, stream: bool = True):
        print(f"\n🔍 Prompt: {prompt}")
        return self.agent.print_response(prompt, stream=stream)


# ✅ Example Run
if __name__ == "__main__":
    refiner = PromptRefiner()
    web_search_agent = WebSearchAgentNode()

    user_input = "can u give me the gdp of all state in india"
    refined = refiner.refine(user_input)
    web_search_agent.run(refined)


# from agno.agent import Agent
# from agno.models.groq import Groq
# from agno.tools.searxng import SearxngTools
# import dotenv
# import os

# dotenv.load_dotenv()


# class WebSearchAgentNode:
#     def __init__(self, agent_id="web_search_agent"):
#         self.agent_id = agent_id
#         self.model = Groq(id="deepseek-r1-distill-llama-70b")

#         self.search_tools = SearxngTools(
#             host="http://localhost:53153",
#             fixed_max_results=5,
#             images=True,
#             it=True,
#             map=True,
#             music=True,
#             news=True,
#             science=True,
#             videos=True,
#         )

#         self.agent = Agent(
#             model=self.model,
#             tools=[self.search_tools],
#             agent_id=self.agent_id,
#             show_tool_calls=True,
#             markdown=True,
#         )

#     def run(self, prompt: str, stream: bool = True):
#         return self.agent.print_response(prompt, stream=stream)


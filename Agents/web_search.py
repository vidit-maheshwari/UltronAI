from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.storage.sqlite import SqliteStorage
from .prompt_refiner import PromptRefiner
import dotenv
import os
from datetime import datetime
import json

dotenv.load_dotenv()


class WebSearchAgentNode:
    def __init__(self, agent_id="web_search_agent", db_file="agents.db", table_name="agent_sessions"):
        self.agent_id = agent_id

        # Initialize model with a more capable version
        self.model = Groq(id="deepseek-r1-distill-llama-70b")

        # Initialize DuckDuckGoTools without max_results parameter
        self.search_tools = DuckDuckGoTools()

        # Optional storage for logging sessions
        self.storage = SqliteStorage(db_file=db_file, table_name=table_name)

        # Setup agent with enhanced instructions
        self.agent = Agent(
            model=self.model,
            tools=[self.search_tools],
            agent_id=self.agent_id,
            storage=self.storage,
            show_tool_calls=True,
            markdown=True,
            instructions="""You are an advanced web research and analysis agent. Your capabilities include:

1. Comprehensive Research:
   - Perform deep web searches on any topic
   - Analyze multiple sources for accuracy and relevance
   - Cross-reference information from different sources
   - Identify trends and patterns in data
   - Always perform multiple searches to get comprehensive results

2. Detailed Analysis:
   - Provide in-depth analysis of search results
   - Compare and contrast different viewpoints
   - Highlight key insights and implications
   - Identify potential biases or limitations in sources
   - Include specific metrics and benchmarks when available

3. Response Format:
   - Start with a brief overview of the topic
   - Present key findings with supporting evidence
   - Include relevant statistics and data points
   - Provide context and background information
   - End with conclusions and implications
   - Include source citations when relevant
   - Use bullet points for better readability
   - Include specific examples and use cases

4. Specialized Knowledge Areas:
   - Technology and programming
   - Business and economics
   - Science and research
   - Current events and news
   - Academic topics
   - Technical documentation
   - Market analysis
   - Industry trends

Always aim to provide comprehensive, well-structured responses that combine multiple sources and perspectives. When comparing technologies or tools, include:
- Performance metrics
- Community support
- Learning curve
- Use cases
- Pros and cons
- Real-world examples"""
        )

    def run(self, prompt: str, stream: bool = True):
        # Add timestamp and context to the prompt
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        enhanced_prompt = f"""
🔍 Research Request (Timestamp: {timestamp})
Topic: {prompt}

Please provide a comprehensive analysis including:
1. Overview and context
2. Key findings and data points
3. Analysis and implications
4. Supporting evidence from multiple sources
5. Conclusions and recommendations

For technology comparisons, please include:
- Performance benchmarks
- Community support metrics
- Learning curve analysis
- Use case scenarios
- Pros and cons
- Real-world examples
- Future trends and predictions

"""
        print(f"\n🔍 Research Request: {prompt}")
        return self.agent.print_response(enhanced_prompt, stream=stream)

    def save_search_results(self, query: str, results: dict):
        """Save search results to storage for future reference"""
        try:
            self.storage.save({
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "results": json.dumps(results)
            })
        except Exception as e:
            print(f"Error saving search results: {str(e)}")


# ✅ Example Run
if __name__ == "__main__":
    refiner = PromptRefiner()
    web_search_agent = WebSearchAgentNode()

    # Example queries for different domains
    example_queries = [
        "What are the latest developments in quantum computing?",
        "Analyze the impact of AI on healthcare in 2024",
        "Compare the performance of React vs Vue.js in 2024",
        "What are the emerging trends in sustainable technology?",
        "Analyze the current state of the global semiconductor industry"
    ]

    # Use the React vs Vue.js comparison query
    user_input = "Compare the performance of React vs Vue.js in 2024"
    refined = refiner.refine(user_input)
    web_search_agent.run(refined)



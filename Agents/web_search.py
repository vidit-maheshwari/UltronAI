from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.storage.sqlite import SqliteStorage
from .prompt_refiner import PromptRefiner
import dotenv
import os
from datetime import datetime
import json
from typing import Dict, Any, List, Optional

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

        # Search Agent - Performs the actual web searches
        self.search_agent = Agent(
            model=self.model,
            tools=[self.search_tools],
            agent_id=f"{self.agent_id}_searcher",
            storage=self.storage,
            show_tool_calls=True,
            markdown=True,
            instructions="""You are a comprehensive web research agent. Your job is to:
            
            1. **Perform Multiple Searches**: Always perform at least 3-5 different searches to get comprehensive coverage
            2. **Use Varied Search Terms**: Use different keywords and phrases to capture different aspects
            3. **Focus on Recent Information**: Prioritize recent sources (last 2-3 years)
            4. **Capture Diverse Perspectives**: Include different viewpoints and sources
            
            **Search Strategy:**
            - Start with broad searches, then narrow down
            - Use quotes for exact phrases
            - Include "2024" or "latest" for current information
            - Search for "comparison", "vs", "alternatives" for comparisons
            - Include "best practices", "tutorial", "guide" for how-to information
            
            Return ALL search results in a structured format for analysis.
            """
        )

        # Analysis Agent - Synthesizes and analyzes search results
        self.analysis_agent = Agent(
            model=self.model,
            agent_id=f"{self.agent_id}_analyzer",
            storage=self.storage,
            show_tool_calls=False,
            markdown=True,
            instructions="""You are an expert research analyst specializing in synthesizing information from multiple sources.
            
            **Analysis Capabilities:**
            - Synthesize information from multiple sources
            - Identify key trends and patterns
            - Compare and contrast different viewpoints
            - Evaluate source credibility and authority
            - Extract actionable insights and recommendations
            - Identify gaps in current knowledge
            
            **Source Evaluation Criteria:**
            - **Authority**: Official websites, academic sources, industry leaders
            - **Recency**: Prefer sources from the last 2-3 years
            - **Relevance**: Direct relevance to the search query
            - **Objectivity**: Balanced, factual presentation
            - **Completeness**: Comprehensive coverage of the topic
            
            **Output Format:**
            Provide a structured analysis with:
            1. **Executive Summary** (2-3 sentences)
            2. **Key Findings** (bullet points)
            3. **Detailed Analysis** (organized by themes)
            4. **Source Evaluation** (most reliable sources)
            5. **Recommendations** (actionable insights)
            6. **Limitations** (what's missing or uncertain)
            """
        )

        # Synthesis Agent - Creates final, polished output
        self.synthesis_agent = Agent(
            model=self.model,
            agent_id=f"{self.agent_id}_synthesizer",
            storage=self.storage,
            show_tool_calls=False,
            markdown=True,
            instructions="""You are a professional content synthesizer who creates clear, actionable research summaries.
            
            **Synthesis Principles:**
            - Present information in a clear, logical structure
            - Use bullet points and numbered lists for readability
            - Include specific examples and data points
            - Provide context and background information
            - Highlight practical applications and use cases
            - Address the original question directly
            
            **For Technology Comparisons:**
            - Performance metrics and benchmarks
            - Community support and ecosystem
            - Learning curve and documentation
            - Use cases and best applications
            - Pros and cons analysis
            - Real-world examples and case studies
            - Future trends and predictions
            
            **For Research Topics:**
            - Current state of knowledge
            - Recent developments and breakthroughs
            - Key challenges and opportunities
            - Expert opinions and consensus
            - Practical implications
            - Future directions
            
            Create a professional, well-structured response that directly answers the user's question.
            """
        )

    def _perform_comprehensive_search(self, query: str) -> List[Dict[str, Any]]:
        """Perform multiple searches to get comprehensive coverage."""
        log_info(f"Starting comprehensive search for: {query}")
        
        # Generate multiple search variations
        search_variations = self._generate_search_variations(query)
        
        all_results = []
        for variation in search_variations:
            try:
                search_prompt = f"Search for: {variation}"
                response = self.search_agent.run(search_prompt)
                
                # Extract results from the response
                results = self._extract_search_results(response.content)
                all_results.extend(results)
                
                log_info(f"Search variation '{variation}' completed with {len(results)} results")
            except Exception as e:
                log_info(f"Error in search variation '{variation}': {e}")
        
        # Remove duplicates and limit to top results
        unique_results = self._deduplicate_results(all_results)
        log_info(f"Comprehensive search completed. Total unique results: {len(unique_results)}")
        
        return unique_results

    def _generate_search_variations(self, query: str) -> List[str]:
        """Generate multiple search variations for comprehensive coverage."""
        variations = [query]  # Start with original query
        
        # Add variations based on query type
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["best", "top", "compare", "vs", "versus"]):
            # For comparison queries, add specific comparison terms
            variations.extend([
                f"{query} comparison 2024",
                f"{query} alternatives",
                f"{query} pros and cons",
                f"{query} performance benchmark"
            ])
        elif any(word in query_lower for word in ["how", "tutorial", "guide", "learn"]):
            # For how-to queries, add tutorial variations
            variations.extend([
                f"{query} tutorial 2024",
                f"{query} best practices",
                f"{query} step by step guide",
                f"{query} examples"
            ])
        else:
            # For general research queries, add comprehensive variations
            variations.extend([
                f"{query} 2024",
                f"{query} latest developments",
                f"{query} current state",
                f"{query} overview",
                f"{query} analysis"
            ])
        
        return variations[:5]  # Limit to 5 variations

    def _extract_search_results(self, content: str) -> List[Dict[str, Any]]:
        """Extract structured search results from agent response."""
        results = []
        
        # Simple extraction - look for URLs and titles in the content
        lines = content.split('\n')
        current_result = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith('http'):
                if current_result:
                    results.append(current_result)
                current_result = {'url': line, 'title': '', 'snippet': ''}
            elif line and current_result and not current_result.get('title'):
                current_result['title'] = line
            elif line and current_result and current_result.get('title'):
                current_result['snippet'] = line
                results.append(current_result)
                current_result = {}
        
        if current_result:
            results.append(current_result)
        
        return results

    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate results based on URL."""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results[:20]  # Limit to top 20 results

    def _analyze_search_results(self, query: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze and synthesize search results."""
        log_info(f"Analyzing {len(search_results)} search results")
        
        # Prepare analysis prompt
        results_text = "\n\n".join([
            f"**Source {i+1}:**\nTitle: {r.get('title', 'N/A')}\nURL: {r.get('url', 'N/A')}\nSnippet: {r.get('snippet', 'N/A')}"
            for i, r in enumerate(search_results)
        ])
        
        analysis_prompt = f"""
        Analyze the following search results for the query: "{query}"
        
        **Search Results:**
        {results_text}
        
        Provide a comprehensive analysis including:
        1. Executive Summary
        2. Key Findings
        3. Detailed Analysis by Themes
        4. Source Evaluation (most reliable sources)
        5. Recommendations
        6. Limitations and Gaps
        """
        
        response = self.analysis_agent.run(analysis_prompt)
        return {
            "query": query,
            "results_count": len(search_results),
            "analysis": response.content
        }

    def _synthesize_final_response(self, query: str, analysis: Dict[str, Any]) -> str:
        """Create the final, polished response."""
        log_info("Synthesizing final response")
        
        synthesis_prompt = f"""
        Create a clear, actionable summary for the query: "{query}"
        
        **Analysis Results:**
        {analysis['analysis']}
        
        Create a professional response that:
        - Directly answers the user's question
        - Provides clear, actionable insights
        - Uses bullet points and structured formatting
        - Includes specific examples and data points
        - Highlights practical applications
        - Addresses limitations and uncertainties
        """
        
        response = self.synthesis_agent.run(synthesis_prompt)
        return response.content

    def run(self, prompt: str, stream: bool = True):
        """Execute comprehensive web research with synthesis and analysis."""
        # Add timestamp and context to the prompt
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"\n🔍 Research Request (Timestamp: {timestamp})")
        print(f"Topic: {prompt}")
        print("Performing comprehensive research and analysis...")
        
        try:
            # Step 1: Perform comprehensive search
            search_results = self._perform_comprehensive_search(prompt)
            
            if not search_results:
                return "No search results found. Please try a different search query."
            
            # Step 2: Analyze search results
            analysis = self._analyze_search_results(prompt, search_results)
            
            # Step 3: Synthesize final response
            final_response = self._synthesize_final_response(prompt, analysis)
            
            # Step 4: Save results for future reference
            self.save_search_results(prompt, {
                "timestamp": timestamp,
                "results_count": len(search_results),
                "analysis": analysis,
                "final_response": final_response
            })
            
            print(f"\n✅ Research completed successfully!")
            print(f"📊 Analyzed {len(search_results)} sources")
            print(f"📝 Generated comprehensive analysis")
            
            return final_response
            
        except Exception as e:
            error_msg = f"Error during research: {str(e)}"
            log_info(error_msg)
            return f"❌ Research failed: {error_msg}"

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



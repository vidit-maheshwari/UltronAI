# Agents/researcher_agent.py
from textwrap import dedent
from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.newspaper4k import Newspaper4kTools
from agno.storage.sqlite import SqliteStorage
import dotenv
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dotenv.load_dotenv()

class PromptRefiner:
    """Simple prompt refiner class to replace the missing import"""
    def refine(self, prompt: str) -> str:
        """Basic prompt refinement"""
        # Add research-specific keywords and context
        refined = f"{prompt.strip()}"
        if not any(word in prompt.lower() for word in ['research', 'analyze', 'investigate']):
            refined = f"Research and analyze: {refined}"
        return refined

class ResearcherAgentNode:
    def __init__(self, agent_id="researcher_agent", db_file="agents.db", table_name="research_sessions"):
        self.agent_id = agent_id
        
        try:
            # Initialize model with error handling
            self.model = Groq(id="deepseek-r1-distill-llama-70b")
            logger.info("✅ Groq model initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Groq model: {e}")
            self.model = None
        
        # Initialize tools with error handling
        try:
            self.search_tools = DuckDuckGoTools()
            logger.info("✅ DuckDuckGo tools initialized")
        except Exception as e:
            logger.warning(f"⚠️ DuckDuckGo tools failed: {e}")
            self.search_tools = None
        
        try:
            self.newspaper_tools = Newspaper4kTools()
            logger.info("✅ Newspaper tools initialized")
        except Exception as e:
            logger.warning(f"⚠️ Newspaper tools failed: {e}")
            self.newspaper_tools = None
        
        # Optional storage for logging sessions
        try:
            self.storage = SqliteStorage(db_file=db_file, table_name=table_name)
        except Exception as e:
            logger.warning(f"⚠️ Storage initialization failed: {e}")
            self.storage = None
        
        # Initialize prompt refiner
        self.prompt_refiner = PromptRefiner()
        
        # Collect available tools
        available_tools = []
        if self.search_tools:
            available_tools.append(self.search_tools)
        if self.newspaper_tools:
            available_tools.append(self.newspaper_tools)
        
        # Setup agent with enhanced research capabilities
        if self.model and available_tools:
            self.agent = Agent(
                model=self.model,
                tools=available_tools,
                agent_id=self.agent_id,
                storage=self.storage,
                description=dedent("""\
                    🔬 You are an elite investigative journalist and researcher with decades of experience.
                    
                    Your expertise encompasses:
                    📰 Deep investigative research and analysis
                    🔍 Meticulous fact-checking and source verification
                    ✍️ Compelling narrative construction
                    📊 Data-driven reporting and visualization
                    🎤 Expert interview synthesis
                    📈 Trend analysis and future predictions
                    🧠 Complex topic simplification
                    ⚖️ Ethical journalism practices
                    🌐 Balanced perspective presentation
                """),
                instructions=dedent("""\
                    🔬 RESEARCH METHODOLOGY:
                    
                    1. 🔍 DISCOVERY PHASE
                       - Search for authoritative sources on the topic
                       - Prioritize recent publications and expert opinions
                       - Include academic papers, industry reports, and news articles
                       - Look for primary sources and original research
                    
                    2. 📊 ANALYSIS PHASE
                       - Extract and verify critical information from sources
                       - Cross-reference facts across multiple sources
                       - Identify emerging patterns, trends, and correlations
                       - Evaluate conflicting viewpoints and controversies
                    
                    3. 🧠 SYNTHESIS PHASE
                       - Organize information into coherent themes
                       - Connect dots between different pieces of information
                       - Develop insights and draw meaningful conclusions
                    
                    4. ✍️ REPORTING PHASE
                       - Craft informative content in professional style
                       - Include relevant quotes, statistics, and data points
                       - Maintain objectivity while providing analysis
                       - Explain complex concepts in accessible language
                """),
                expected_output=dedent("""\
                    # 📰 Research Report: {Topic}
                    
                    ## 🎯 Executive Summary
                    {Concise overview of key findings and main takeaways}
                    
                    ## 🔍 Key Research Findings
                    {Main discoveries and insights from research}
                    {Statistical evidence and data points}
                    {Expert analysis and interpretations}
                    
                    ## 📊 Analysis & Implications
                    {Current implications and effects}
                    {Industry, economic, or societal impacts}
                    
                    ## 🔮 Future Outlook
                    {Emerging trends and developments}
                    {Expert predictions and forecasts}
                    {Recommendations}
                    
                    ## 📚 Sources
                    {List of primary sources with key contributions}
                    
                    ---
                    🔬 Research conducted by AI Research Agent
                    📅 Date: {current_date}
                """),
                markdown=True,
                show_tool_calls=True,
                add_datetime_to_instructions=True,
            )
            logger.info("✅ Research agent initialized successfully")
        else:
            logger.error("❌ Failed to initialize research agent - missing model or tools")
            self.agent = None
    
    def run(self, prompt: str, stream: bool = False):
        """
        Main method to run research based on the given prompt
        Standardized interface for compatibility with orchestrator
        """
        if not self.agent:
            return "❌ Research agent not properly initialized"
            
        try:
            print(f"\n🔬 Starting Research on: {prompt}")
            print("="*60)
            
            # Refine the prompt for better research results
            refined_prompt = self.prompt_refiner.refine(prompt)
            print(f"🎯 Refined Research Query: {refined_prompt}")
            
            # Add research context to the prompt
            enhanced_prompt = self._enhance_research_prompt(refined_prompt)
            
            # Execute research with multiple fallback attempts
            print("\n🔍 Conducting comprehensive research...")
            
            # Try multiple approaches for better reliability
            for attempt in range(3):
                try:
                    if hasattr(self.agent, 'run'):
                        result = self.agent.run(enhanced_prompt)
                    elif hasattr(self.agent, 'print_response'):
                        result = self.agent.print_response(enhanced_prompt, stream=stream)
                    else:
                        return "❌ Agent has no compatible run method"
                    
                    if result and str(result).strip():
                        print("\n✅ Research completed successfully!")
                        return str(result)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Research attempt {attempt + 1} failed: {e}")
                    if attempt == 2:  # Last attempt
                        # Return a basic research response
                        return self._create_fallback_research(prompt)
                    continue
            
            return self._create_fallback_research(prompt)
            
        except Exception as e:
            error_msg = f"❌ Error during research: {str(e)}"
            logger.error(error_msg)
            return self._create_fallback_research(prompt)
    
    def _create_fallback_research(self, prompt: str) -> str:
        """Create a basic research response when tools fail"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        return f"""
# 📰 Research Report: {prompt}

## 🎯 Executive Summary
Research topic identified: {prompt}

Due to technical limitations with external research tools, this is a basic analysis based on general knowledge.

## 🔍 Key Areas for Investigation
- Current state and recent developments in {prompt}
- Industry trends and market conditions
- Expert opinions and academic research
- Statistical data and performance metrics
- Future implications and predictions

## 📊 Research Methodology Needed
- Literature review of academic papers
- Industry report analysis  
- Expert interviews and surveys
- Statistical data collection
- Trend analysis and forecasting

## 🔮 Recommendations
- Conduct primary research through surveys/interviews
- Review latest academic publications
- Analyze industry reports and white papers
- Monitor news sources for recent developments
- Consult domain experts and thought leaders

## 📚 Next Steps
1. Access specialized databases for {prompt}
2. Contact industry experts for insights
3. Review recent publications and reports
4. Analyze statistical trends and data
5. Synthesize findings into comprehensive report

---
🔬 Basic Research Framework Generated
📅 Date: {current_date}
⚠️ Note: Full research capabilities require functional external tools
"""
    
    def _enhance_research_prompt(self, prompt: str) -> str:
        """
        Enhance the research prompt with additional context and instructions
        """
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        enhanced_prompt = f"""
        🔬 COMPREHENSIVE RESEARCH REQUEST:
        
        TOPIC: {prompt}
        
        🎯 RESEARCH OBJECTIVES:
        - Provide thorough, well-researched analysis
        - Include multiple authoritative sources when possible
        - Present balanced perspectives
        - Identify key trends and implications
        - Offer actionable insights
        
        📅 RESEARCH DATE: {current_date}
        
        Focus on:
        • Recent developments and current status
        • Expert opinions and analysis
        • Key facts and data points
        • Multiple perspectives and viewpoints
        • Practical implications and applications
        
        Please provide a comprehensive research report following the structured format.
        """
        
        return enhanced_prompt
    
    def quick_research(self, topic: str) -> str:
        """
        Perform quick research for time-sensitive queries
        """
        try:
            print(f"\n⚡ Quick Research on: {topic}")
            
            quick_prompt = f"""
            Provide a concise but informative research summary on: {topic}
            
            Focus on:
            - Key facts and current status
            - Recent developments
            - Main stakeholders
            - Primary implications
            
            Keep it brief but comprehensive.
            """
            
            return self.run(quick_prompt)
            
        except Exception as e:
            return f"❌ Quick research error: {str(e)}"
    
    def fact_check(self, claim: str) -> str:
        """
        Fact-check a specific claim or statement
        """
        try:
            print(f"\n🔍 Fact-checking: {claim}")
            
            fact_check_prompt = f"""
            Please fact-check this claim: "{claim}"
            
            Provide:
            - Verification status (True/False/Partially True/Unverified)
            - Evidence supporting or refuting the claim
            - Reliable sources for verification
            - Any important context or nuances
            
            Be thorough and objective in your analysis.
            """
            
            return self.run(fact_check_prompt)
            
        except Exception as e:
            return f"❌ Fact-check error: {str(e)}"


# ✅ Example Usage and Testing
if __name__ == "__main__":
    # Initialize the researcher agent
    researcher = ResearcherAgentNode()
    
    print("🔬 ResearcherAgentNode Test Suite")
    print("="*50)
    
    # Test 1: Basic research
    print("\n📊 Test 1: Basic Research")
    result1 = researcher.run("Python calculator implementations")
    print(f"Result: {result1[:200]}...")
    
    # Test 2: Quick research
    print("\n⚡ Test 2: Quick Research")
    result2 = researcher.quick_research("Basic calculator features")
    print(f"Result: {result2[:200]}...")
    
    print("\n✅ All tests completed!")
    print("ResearcherAgentNode is ready for use in the Universal Agent Orchestrator.")
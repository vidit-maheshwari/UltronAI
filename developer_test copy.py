# main.py - Enhanced version with planner-first architecture
from pathlib import Path
import sys
import os
import json
import re

# Add the current directory to Python path if needed
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Import all agent classes (make sure these files exist in the same directory)
from Agents.coder_agent import CoderAgentNode
from Agents.installer_agent import InstallerAgentNode  
from Agents.executer_agent import ExecutorAgentNode
from Agents.error_resolver import ErrorResolverAgentNode
from Agents.file_handler_agent import FileAgentNode
from Agents.researcher_agent import ResearcherAgentNode
from Agents.shell_executer_agent import ShellAgentNode
from Agents.planner_agent import PlannerAgentNode
from Agents.web_search import WebSearchAgentNode

class UniversalAgentOrchestrator:
    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path("./projects")
        self.base_dir.mkdir(exist_ok=True)
        
        print(f"🏁 Initializing Universal Agent Orchestrator with base directory: {self.base_dir}")
        
        # Initialize all agents
        self.agents = {}
        self._initialize_agents()
        
        # Agent execution order mapping
        self.agent_execution_map = {
            'planner': self.planner,
            'researcher': self.researcher,
            'web_search': self.web_search,
            'coder': self.coder,
            'file_handler': self.file_handler,
            'installer': self.installer,
            'executor': self.executor,
            'shell_executor': self.shell_executor,
            'error_resolver': self.error_resolver
        }
        
    def _initialize_agents(self):
        """Initialize all agents with error handling"""
        agent_configs = [
            ('planner', PlannerAgentNode, {}),
            ('researcher', ResearcherAgentNode, {}),
            ('web_search', WebSearchAgentNode, {}),
            ('coder', CoderAgentNode, {'base_dir': self.base_dir}),
            ('file_handler', FileAgentNode, {'base_dir': self.base_dir}),
            ('installer', InstallerAgentNode, {}),
            ('executor', ExecutorAgentNode, {'base_dir': self.base_dir}),
            ('shell_executor', ShellAgentNode, {}),
            ('error_resolver', ErrorResolverAgentNode, {})
        ]
        
        for agent_name, agent_class, kwargs in agent_configs:
            try:
                agent_instance = agent_class(**kwargs)
                setattr(self, agent_name, agent_instance)
                self.agents[agent_name] = agent_instance
                print(f"✅ {agent_name.title()} agent initialized")
            except Exception as e:
                print(f"❌ Error initializing {agent_name} agent: {e}")
                setattr(self, agent_name, None)
                self.agents[agent_name] = None

    def handle_request(self, request: str) -> str:
        """Main entry point - Always starts with planner agent"""
        print(f"\n🎯 Processing request: {request}")
        print("="*60)
        
        try:
            # Step 1: ALWAYS start with planner
            print("🧠 Step 1: Planning phase...")
            if self.planner is None:
                return "❌ Planner agent not available"
            
            plan_result = self.planner.run(request)
            print(f"📋 Plan generated: {plan_result}")
            
            # Step 2: Parse the plan and extract agent sequence
            agent_sequence = self._parse_plan(plan_result, request)
            print(f"🔄 Agent execution sequence: {agent_sequence}")
            
            # Step 3: Execute agents in planned sequence
            execution_results = {}
            for step_num, (agent_name, task_description) in enumerate(agent_sequence, 1):
                print(f"\n🔄 Step {step_num}: Executing {agent_name} agent")
                print(f"📝 Task: {task_description}")
                
                result = self._execute_agent(agent_name, task_description, execution_results)
                execution_results[agent_name] = result
                
                # Check for critical errors
                if self._is_critical_error(result):
                    print(f"🚨 Critical error detected in {agent_name}")
                    return self._handle_critical_error(agent_name, result, execution_results)
            
            # Step 4: Generate final summary
            final_result = self._generate_final_summary(execution_results)
            print(f"\n🏁 Final Result: {final_result}")
            return final_result
            
        except Exception as e:
            error_msg = f"❌ Critical error in orchestration: {str(e)}"
            print(error_msg)
            return error_msg

    def _parse_plan(self, plan_result: str, original_request: str) -> list:
        """Parse planner output to determine agent execution sequence"""
        # Default sequence based on request type
        default_sequences = {
            'web_scraper': [
                ('researcher', 'Research web scraping techniques and best practices'),
                ('coder', 'Create web scraping code'),
                ('installer', 'Install required packages like requests, beautifulsoup4'),
                ('executor', 'Execute and test the web scraper'),
            ],
            'api': [
                ('researcher', 'Research API development best practices'),
                ('coder', 'Create API code'),
                ('installer', 'Install required packages like flask, fastapi'),
                ('executor', 'Execute and test the API'),
            ],
            'calculator': [
                ('coder', 'Create calculator code'),
                ('executor', 'Execute and test the calculator'),
            ],
            'data_analysis': [
                ('researcher', 'Research data analysis techniques'),
                ('coder', 'Create data analysis code'),
                ('installer', 'Install required packages like pandas, numpy'),
                ('executor', 'Execute and test the analysis'),
            ]
        }
        
        # Try to extract specific agent mentions from plan
        plan_lower = plan_result.lower()
        request_lower = original_request.lower()
        
        # Determine request type
        request_type = 'default'
        if any(word in request_lower for word in ['scrap', 'web', 'crawl']):
            request_type = 'web_scraper'
        elif any(word in request_lower for word in ['api', 'rest', 'flask', 'fastapi']):
            request_type = 'api'
        elif any(word in request_lower for word in ['calculat', 'math']):
            request_type = 'calculator'
        elif any(word in request_lower for word in ['data', 'analysis', 'pandas', 'numpy']):
            request_type = 'data_analysis'
        
        # Get sequence
        if request_type in default_sequences:
            sequence = default_sequences[request_type]
        else:
            # Default general sequence
            sequence = [
                ('researcher', f'Research: {original_request}'),
                ('coder', f'Create code for: {original_request}'),
                ('installer', f'Install packages for: {original_request}'),
                ('executor', f'Execute: {original_request}'),
            ]
        
        # Add error resolution at the end if needed
        if any(word in request_lower for word in ['complex', 'advanced', 'difficult']):
            sequence.append(('error_resolver', 'Handle any errors that occur'))
        
        return sequence

    def _execute_agent(self, agent_name: str, task: str, previous_results: dict) -> str:
        """Execute a specific agent with error handling"""
        if agent_name not in self.agents or self.agents[agent_name] is None:
            return f"❌ Agent '{agent_name}' not available"
        
        try:
            agent = self.agents[agent_name]
            
            # Add context from previous results if relevant
            enhanced_task = self._enhance_task_with_context(task, previous_results)
            
            print(f"🤖 Executing {agent_name} with task: {enhanced_task}")
            result = agent.run(enhanced_task)
            
            if result:
                print(f"✅ {agent_name} completed successfully")
                return str(result)
            else:
                print(f"⚠️ {agent_name} returned empty result")
                return f"⚠️ {agent_name} completed but returned no output"
                
        except Exception as e:
            error_msg = f"❌ Error in {agent_name}: {str(e)}"
            print(error_msg)
            return error_msg

    def _enhance_task_with_context(self, task: str, previous_results: dict) -> str:
        """Add context from previous agent results to current task"""
        if not previous_results:
            return task
        
        # Add relevant context based on agent type and previous results
        context_parts = []
        
        if 'researcher' in previous_results:
            context_parts.append(f"Research context: {previous_results['researcher'][:200]}...")
        
        if 'coder' in previous_results and 'installer' in task.lower():
            context_parts.append("Note: Code has been created, focus on required packages")
        
        if context_parts:
            enhanced_task = f"{task}\n\nContext from previous steps:\n" + "\n".join(context_parts)
            return enhanced_task
        
        return task

    def _is_critical_error(self, result: str) -> bool:
        """Check if result indicates a critical error"""
        if not result:
            return False
        
        critical_indicators = [
            'critical error',
            'cannot continue',
            'fatal error',
            'system failure'
        ]
        
        result_lower = str(result).lower()
        return any(indicator in result_lower for indicator in critical_indicators)

    def _handle_critical_error(self, failed_agent: str, error_result: str, all_results: dict) -> str:
        """Handle critical errors by invoking error resolver"""
        print(f"🔧 Attempting to resolve critical error from {failed_agent}")
        
        if self.error_resolver:
            try:
                error_context = f"Error in {failed_agent}: {error_result}\nPrevious results: {all_results}"
                resolution = self.error_resolver.run(error_context)
                return f"🔧 Error resolved: {resolution}"
            except Exception as e:
                return f"❌ Could not resolve error: {str(e)}"
        else:
            return f"❌ Critical error in {failed_agent} and no error resolver available: {error_result}"

    def _generate_final_summary(self, execution_results: dict) -> str:
        """Generate a final summary of all agent executions"""
        successful_agents = []
        failed_agents = []
        
        for agent_name, result in execution_results.items():
            if result and not str(result).startswith('❌'):
                successful_agents.append(agent_name)
            else:
                failed_agents.append(agent_name)
        
        summary = f"✅ Execution completed - {len(successful_agents)} agents succeeded"
        if failed_agents:
            summary += f", {len(failed_agents)} agents had issues: {', '.join(failed_agents)}"
        
        return summary

    def test_individual_agents(self):
        """Test each agent individually"""
        print("\n🧪 Testing individual agents...")
        print("="*60)
        
        test_cases = [
            ('planner', 'Create a plan for building a simple calculator'),
            ('researcher', 'Research Python calculator implementations'),
            ('web_search', 'Search for Python calculator examples'),
            ('coder', 'Create a simple hello world Python script'),
            ('file_handler', 'List files in the current directory'),
            ('installer', 'Check if requests package is installed'),
            ('executor', 'Test syntax of any Python files in the directory'),
            ('shell_executor', 'Execute a simple shell command'),
            ('error_resolver', 'Analyze this error: ModuleNotFoundError: No module named requests')
        ]
        
        for agent_name, test_task in test_cases:
            try:
                print(f"\n🧪 Testing {agent_name.title()} Agent...")
                if agent_name in self.agents and self.agents[agent_name]:
                    result = self.agents[agent_name].run(test_task)
                    print(f"✅ {agent_name} agent test passed")
                else:
                    print(f"❌ {agent_name} agent not available")
            except Exception as e:
                print(f"❌ {agent_name} agent test failed: {e}")

    def interactive_mode(self):
        """Interactive mode with enhanced options"""
        print("\n" + "="*60)
        print("🎮 Universal Agent System - Interactive Mode")
        print("🧠 All requests are planned first, then executed systematically")
        print("="*60)
        print("Choose an option:")
        print("1. Simple calculator")
        print("2. Web scraper") 
        print("3. REST API")
        print("4. Data analysis tool")
        print("5. Custom request")
        print("6. Test all agents")
        print("7. Exit")
        
        while True:
            choice = input("\nEnter your choice (1-7): ").strip()
            
            if choice == "1":
                result = self.handle_request("Create a simple calculator with basic math operations (+, -, *, /) that can handle user input")
            elif choice == "2":
                result = self.handle_request("Create a web scraper that can extract titles and links from websites using requests and beautifulsoup")
            elif choice == "3":
                result = self.handle_request("Create a simple REST API using Flask for managing a todo list with GET, POST, PUT, DELETE operations")
            elif choice == "4":
                result = self.handle_request("Create a data analysis tool that can read CSV files and generate basic statistics using pandas")
            elif choice == "5":
                custom_request = input("Enter your custom request: ").strip()
                if custom_request:
                    result = self.handle_request(custom_request)
                else:
                    print("❌ Empty request")
                    continue
            elif choice == "6":
                self.test_individual_agents()
                continue
            elif choice == "7":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-7.")
                continue
                
            print(f"\n🏁 Final Result: {result}")
            print("\n" + "="*60)


if __name__ == "__main__":
    # Method 1: Using raw string (recommended for Windows)
    base_path = Path(r"C:\Users\z0053h8u\Documents\Awishkar25\Ultronai\UltronAI\projects")
    
    # Method 2: Using forward slashes (also works on Windows)
    # base_path = Path("C:/Users/susmi/Documents/UltonAi/UltronAI-1/Agents/projects")
    
    # Method 3: Using pathlib to build path (most portable)
    # base_path = Path.home() / "Documents" / "UltonAi" / "UltronAI-1" / "Agents" / "projects"
    
    # Method 4: Using current directory (simplest)
    # base_path = Path("./projects")
    
    print(f"🚀 Starting Universal Agent System with Planner-First Architecture")
    print(f"📁 Base directory: {base_path}")
    
    try:
        # Initialize the universal agent system
        universal_agent = UniversalAgentOrchestrator(base_dir=base_path)
        
        # Test individual agents first
        print("\n🔍 Testing system readiness...")
        universal_agent.test_individual_agents()
        
        # Start interactive mode
        universal_agent.interactive_mode()
            
    except Exception as e:
        print(f"💥 Critical error starting the system: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure all agent files exist in the Agents/ directory")
        print("2. Check that your .env file has the GROQ_API_KEY")
        print("3. Verify all required packages are installed")
        print("4. Try using a simpler path like Path('./projects')")
        print("5. Ensure all agent classes have the same interface (run method)")
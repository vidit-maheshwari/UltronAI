# main.py - Smart planner-first architecture with dynamic agent selection
from pathlib import Path
import sys
import os
import json
import re
from typing import List, Dict, Tuple, Optional

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

class SmartAgentOrchestrator:
    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path("./projects")
        self.base_dir.mkdir(exist_ok=True)
        
        print(f"🏁 Initializing Smart Agent Orchestrator with base directory: {self.base_dir}")
        
        # Initialize all agents
        self.agents = {}
        self._initialize_agents()
        
        # Agent capabilities mapping for smart selection
        self.agent_capabilities = {
            'planner': ['planning', 'task_breakdown', 'strategy', 'analysis'],
            'researcher': ['research', 'information_gathering', 'best_practices', 'learning', 'documentation'],
            'web_search': ['web_search', 'online_info', 'current_data', 'external_resources'],
            'coder': ['code_creation', 'programming', 'script_writing', 'development'],
            'file_handler': ['file_operations', 'directory_listing', 'file_management', 'path_operations'],
            'installer': ['package_installation', 'dependency_management', 'environment_setup'],
            'executor': ['code_execution', 'testing', 'running_programs', 'validation'],
            'shell_executor': ['shell_commands', 'system_operations', 'terminal_tasks'],
            'error_resolver': ['error_handling', 'debugging', 'troubleshooting', 'problem_solving']
        }
        
        # Direct execution patterns - tasks that can be handled by a single agent
        self.direct_execution_patterns = {
        # Existing patterns
        r'(current|get|show|display).*(directory|folder|path|pwd)': 'file_handler',
        r'list.*(file|director|content|ls)': 'file_handler',
        r'create.*(directory|folder|mkdir)': 'file_handler',
        r'delete.*(file|directory|rm)': 'file_handler',
        r'read.*(file|content|cat)': 'file_handler',
        r'write.*(file|content)': 'file_handler',
        
        r'execute.*(command|shell|cmd)': 'shell_executor',
        r'run.*(shell|command|terminal)': 'shell_executor',
        r'(echo|print).*(hello|world|test)': 'shell_executor',
        
        r'create.*simple.*(hello|world|test|script)': 'coder',
        r'write.*simple.*(program|code|function)': 'coder',
        
        r'install.*(package|module|pip|library)': 'installer',
        r'check.*install': 'installer',
        
        r'run.*python.*(file|script|code)': 'executor',
        r'execute.*python': 'executor',
        r'test.*code': 'executor',
        
        # Add these new patterns
        r'(tell|share).*(joke|funny)': 'researcher',
        r'what.*(time|date)': 'researcher',
        r'search.*': 'web_search',
        r'find.*': 'web_search',
        r'research.*': 'researcher',
        r'explain.*': 'researcher',
        r'how.*works': 'researcher',
        r'what.*is': 'researcher',
        r'why.*': 'researcher',
        r'define.*': 'researcher',
        r'meaning.*': 'researcher'
    }
        
        # Task complexity levels
        self.complexity_keywords = {
            'simple': ['hello', 'world', 'test', 'basic', 'simple', 'quick', 'show', 'get', 'list'],
            'moderate': ['create', 'build', 'make', 'calculator', 'game', 'utility', 'script'],
            'complex': ['web scraper', 'api', 'machine learning', 'ai', 'database', 'server', 'framework', 'advanced', 'complex', 'system']
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


    def _is_code_related(self, request: str) -> bool:
            """Determine if the request is related to coding"""
            coding_keywords = [
                'code', 'program', 'script', 'function', 
                'class', 'python', 'java', 'javascript',
                'compile', 'debug', 'variable', 'loop',
                'algorithm', 'programming', 'developer',
                'development', 'software', 'application',
                'app', 'coding', 'programmer'
            ]
            request_lower = request.lower()
            return any(keyword in request_lower for keyword in coding_keywords)
    

    def handle_request(self, request: str) -> str:
        """Main entry point - Smart agent selection based on request complexity"""
        print(f"\n🎯 Processing request: {request}")
        print("="*60)
        
        try:
            # Step 1: Handle simple requests first
            request_lower = request.lower().strip()
            
            # Joke requests - Simplified handling
            if any(word in request_lower for word in ['joke', 'funny', 'laugh']):
                print("🎭 Joke request detected")
                joke_request = {
                    'role': 'user',
                    'content': 'Tell me a short, funny joke (just the joke itself, no analysis or research needed)'
                }
                try:
                    result = self.researcher.run(joke_request['content'])
                    # Clean up the response
                    if isinstance(result, str):
                        # Extract just the joke part if it's wrapped in system messages
                        joke_lines = [line for line in result.split('\n') if line.strip() and not line.startswith(('🔬', '📅', '#', '##'))]
                        return "🎭 " + '\n'.join(joke_lines)
                    return "🎭 " + str(result)
                except Exception as e:
                    # Fallback joke if there's an error
                    return "🎭 Here's a joke:\nWhy did the programmer quit his job?\nBecause he didn't get arrays! 😄"
            
            # Time/date requests
            if any(word in request_lower for word in ['time', 'date', 'day']):
                print("🕒 Time request detected")
                return f"🕒 Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Step 2: Check for direct execution patterns
            direct_agent = self._check_direct_execution(request)
            if direct_agent:
                print(f"🚀 Direct execution detected - using {direct_agent}")
                return self._execute_single_agent(direct_agent, request)
            
            # Step 3: Handle file operations
            if any(word in request_lower for word in ['file', 'directory', 'folder', 'path']):
                print("📁 File operation detected")
                return self._execute_single_agent('file_handler', request)
            
            # Step 4: Handle shell commands
            if any(word in request_lower for word in ['command', 'shell', 'terminal', 'cmd']):
                print("💻 Shell command detected")
                return self._execute_single_agent('shell_executor', request)
            
            # Step 5: Handle package installation
            if any(word in request_lower for word in ['install', 'pip', 'package']):
                print("📦 Installation request detected")
                return self._execute_single_agent('installer', request)
            
            # Step 6: Handle code-related requests
            if self._is_code_related(request):
                print("👨‍💻 Code-related request detected")
                complexity = self._determine_complexity(request)
                
                if complexity == 'simple':
                    return self._execute_single_agent('coder', request)
                else:
                    agents_needed = ['planner', 'coder', 'executor']
                    if 'install' in request_lower or 'package' in request_lower:
                        agents_needed.insert(1, 'installer')
                    return self._execute_minimal_sequence(agents_needed, request)
            
            # Step 7: Handle research/information requests
            if any(word in request_lower for word in ['search', 'find', 'what', 'how', 'why', 'explain']):
                print("🔍 Research request detected")
                return self._execute_single_agent('researcher', 
                    f"Provide a brief, clear answer about: {request}")
            
            # Step 8: For complex tasks that don't fit above categories
            print("🤔 Complex request detected - analyzing...")
            complexity = self._determine_complexity(request)
            agents_needed = self._select_agents_by_complexity(complexity, request)
            
            print(f"🎯 Selected agents for task: {', '.join(agents_needed)}")
            return self._execute_minimal_sequence(agents_needed, request)
            
        except Exception as e:
            error_msg = f"❌ Error processing request: {str(e)}"
            print(error_msg)
            return error_msg

    def _select_agents_by_complexity(self, complexity: str, request: str) -> List[str]:
        """Select agents based on task complexity"""
        if complexity == 'simple':
            return self._select_simple_agents(request)
        elif complexity == 'moderate':
            return self._select_moderate_agents(request)
        else:
            return self._select_complex_agents(request)

    def _clean_response(self, response: str) -> str:
        """Clean up the response for better readability"""
        if not response:
            return "No response generated"
        
        # If it's a joke response, return it directly with minimal cleaning
        if '🎭' in response or any(word in response.lower() for word in ['joke', 'funny']):
            lines = response.split('\n')
            joke_lines = [line for line in lines if line.strip() and not line.startswith(('RunResponse', 'Message', 'metrics'))]
            return '\n'.join(joke_lines)
        
        # Remove system messages and debug info
        lines = response.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip debug/system messages and technical details
            if any(skip in line for skip in ['RunResponse', 'MessageMetrics', 'debug:', 'system:', 'info:']):
                continue
            if line.strip() and not line.strip().startswith(('===', '---')):
                cleaned_lines.append(line)
        
        cleaned_response = '\n'.join(cleaned_lines).strip()
        cleaned_response = re.sub(r'\n\s*\n', '\n\n', cleaned_response)
        
        return cleaned_response

    def _check_direct_execution(self, request: str) -> Optional[str]:
        """Check if request can be handled by a single agent"""
        request_lower = request.lower().strip()
        
        for pattern, agent in self.direct_execution_patterns.items():
            if re.search(pattern, request_lower):
                print(f"✅ Matched direct execution pattern: {pattern} -> {agent}")
                return agent
        
        return None

    def _determine_complexity(self, request: str) -> str:
        """Determine task complexity based on keywords and patterns"""
        request_lower = request.lower()
        
        # Count keywords for each complexity level
        complexity_scores = {'simple': 0, 'moderate': 0, 'complex': 0}
        
        for complexity, keywords in self.complexity_keywords.items():
            for keyword in keywords:
                if keyword in request_lower:
                    complexity_scores[complexity] += 1
        
        # Special patterns that indicate complexity
        if any(pattern in request_lower for pattern in ['web scraping', 'machine learning', 'api integration', 'database', 'multiple files']):
            complexity_scores['complex'] += 3
        elif any(pattern in request_lower for pattern in ['create', 'build', 'calculator', 'game']):
            complexity_scores['moderate'] += 2
        elif any(pattern in request_lower for pattern in ['show', 'get', 'list', 'display', 'hello world']):
            complexity_scores['simple'] += 2
        
        # Return the complexity with highest score
        return max(complexity_scores, key=complexity_scores.get)

    def _select_simple_agents(self, request: str) -> List[str]:
        """Select minimal agents for simple tasks"""
        request_lower = request.lower()
        
        # Information and general queries
        if any(word in request_lower for word in ['tell', 'joke', 'funny', 'explain', 'what', 
                                                'how', 'why', 'define', 'meaning']):
            return ['researcher']
        
        # Web searches
        if any(word in request_lower for word in ['search', 'find', 'look up', 'google']):
            return ['web_search']
        
        # File operations
        if any(word in request_lower for word in ['file', 'directory', 'folder', 'path', 
                                                'list', 'show', 'create folder', 'delete file']):
            return ['file_handler']
        
        # Shell commands
        if any(word in request_lower for word in ['command', 'shell', 'echo', 'terminal', 
                                                'cmd', 'powershell', 'bash']):
            return ['shell_executor']
        
        # Simple code execution
        if any(word in request_lower for word in ['run', 'execute']) and 'python' in request_lower:
            return ['executor']
        
        # Package installation
        if any(word in request_lower for word in ['install', 'pip', 'package', 'dependency']):
            return ['installer']
        
        # Code-related tasks
        if self._is_code_related(request):
            return ['coder']
        
        # Default to researcher for any other queries
        return ['researcher']

    def _select_moderate_agents(self, request: str) -> List[str]:
        """Select minimal agents for moderate tasks"""
        request_lower = request.lower()
        agents = []
        
        # Code creation tasks
        if any(word in request_lower for word in ['create', 'build', 'make', 'write']):
            agents.append('coder')
            agents.append('executor')  # Test the created code
        
        # If installation might be needed
        if any(word in request_lower for word in ['package', 'library', 'import', 'module']):
            agents.insert(0, 'installer')  # Install first
        
        # If file operations are mentioned
        if any(word in request_lower for word in ['file', 'save', 'directory']):
            agents.insert(0, 'file_handler')  # Handle files first
        
        return agents if agents else ['coder', 'executor']

    def _select_complex_agents(self, request: str) -> List[str]:
        """Select minimal agents for complex tasks"""
        request_lower = request.lower()
        agents = []
        
        # Start with planning for complex tasks
        agents.append('planner')
        
        # Add research only if truly needed
        if any(word in request_lower for word in ['research', 'best practices', 'how to', 'learn', 'documentation']):
            agents.append('researcher')
        
        # Add web search only if current info is needed
        if any(word in request_lower for word in ['latest', 'current', 'recent', 'new', 'updated']):
            agents.append('web_search')
        
        # Core development agents
        agents.extend(['coder', 'installer', 'executor'])
        
        return agents

    def _execute_single_agent(self, agent_name: str, request: str) -> str:
        """Execute a single agent for direct tasks"""
        print(f"🤖 Executing {agent_name} for: {request}")
        
        if agent_name not in self.agents or self.agents[agent_name] is None:
            return f"❌ Agent '{agent_name}' not available"
        
        try:
            result = self.agents[agent_name].run(request)
            
            # If there's an error and error_resolver is available, try once
            if self._is_error(result) and self.error_resolver:
                print("🔧 Error detected, trying error resolver...")
                error_context = f"Error in {agent_name}: {result}\nOriginal task: {request}"
                resolution = self.error_resolver.run(error_context)
                
                # Try the original agent once more with the resolution
                enhanced_request = f"{request}\n\nError resolution guidance: {resolution}"
                result = self.agents[agent_name].run(enhanced_request)
            
            return str(result) if result else f"⚠️ {agent_name} completed but returned no output"
            
        except Exception as e:
            error_msg = f"❌ Error in {agent_name}: {str(e)}"
            print(error_msg)
            return error_msg

    def _execute_minimal_sequence(self, agents_needed: List[str], request: str) -> str:
        """Execute minimal sequence of agents"""
        results = {}
        context = ""
        
        for i, agent_name in enumerate(agents_needed):
            print(f"\n🔄 Step {i+1}/{len(agents_needed)}: Executing {agent_name}")
            
            if agent_name not in self.agents or self.agents[agent_name] is None:
                result = f"❌ Agent '{agent_name}' not available"
            else:
                # Enhance request with context from previous steps
                enhanced_request = self._create_enhanced_request(request, context, agent_name)
                
                try:
                    result = self.agents[agent_name].run(enhanced_request)
                    
                    # Handle errors immediately
                    if self._is_error(result) and self.error_resolver and agent_name != 'error_resolver':
                        print(f"🔧 Error in {agent_name}, trying error resolver...")
                        error_context = f"Error in {agent_name}: {result}\nOriginal request: {request}"
                        resolution = self.error_resolver.run(error_context)
                        
                        # Update context with resolution
                        context += f"\nError resolution for {agent_name}: {resolution}"
                        
                        # Retry with resolution
                        retry_request = f"{enhanced_request}\n\nError resolution: {resolution}"
                        result = self.agents[agent_name].run(retry_request)
                    
                    if result and not self._is_error(result):
                        # Add successful result to context for next agents
                        context += f"\n{agent_name} result: {str(result)[:200]}..."
                    
                except Exception as e:
                    result = f"❌ Error in {agent_name}: {str(e)}"
            
            results[agent_name] = result
            print(f"✅ {agent_name} completed")
        
        return self._generate_final_summary(results, request)

    def _create_enhanced_request(self, original_request: str, context: str, current_agent: str) -> str:
        """Create enhanced request with relevant context"""
        base_request = original_request
        
        # Add specific instructions based on agent type
        if current_agent == 'planner':
            base_request = f"Create a minimal plan for: {original_request}\nFocus on essential steps only."
        elif current_agent == 'researcher':
            base_request = f"Research essential information for: {original_request}\nProvide only key insights."
        elif current_agent == 'coder':
            base_request = f"Create code for: {original_request}\nMake it functional and well-commented."
        elif current_agent == 'installer':
            base_request = f"Handle package installation for: {original_request}\nInstall only necessary packages."
        elif current_agent == 'executor':
            base_request = f"Execute and test the code for: {original_request}\nProvide clear execution results."
        
        # Add context if available and relevant
        if context and len(context.strip()) > 0:
            return f"{base_request}\n\nContext from previous steps:{context}"
        
        return base_request

    def _is_error(self, result: str) -> bool:
        """Check if result indicates an error"""
        if not result:
            return True
        
        error_indicators = ['❌', 'error', 'failed', 'exception', 'not found', 'could not', 'unable to']
        result_lower = str(result).lower()
        return any(indicator in result_lower for indicator in error_indicators)

    def _generate_final_summary(self, results: Dict[str, str], original_request: str) -> str:
        """Generate a concise final summary"""
        summary_parts = [f"🎯 Request: {original_request}"]
        
        successful_agents = []
        failed_agents = []
        
        for agent, result in results.items():
            if result and not self._is_error(result):
                successful_agents.append(agent)
            else:
                failed_agents.append(agent)
        
        summary_parts.append(f"✅ Successful: {', '.join(successful_agents)}")
        
        if failed_agents:
            summary_parts.append(f"❌ Failed: {', '.join(failed_agents)}")
        
        # Include the most relevant final result
        priority_agents = ['executor', 'file_handler', 'shell_executor', 'coder']
        for agent in priority_agents:
            if agent in results and not self._is_error(results[agent]):
                summary_parts.append(f"🏁 Final Result: {results[agent]}")
                break
        
        return "\n".join(summary_parts)

    def test_individual_agents(self):
        """Test each agent individually with simple tasks"""
        print("\n🧪 Testing individual agents with simple tasks...")
        print("="*60)
        
        test_cases = [
            ('file_handler', 'Get current directory path'),
            ('shell_executor', 'Execute: echo "Hello World"'),
            ('coder', 'Create a simple hello world Python script'),
            ('executor', 'Test: print("Hello World")'),
            ('installer', 'Check if os package is available'),
        ]
        
        for agent_name, test_task in test_cases:
            try:
                print(f"\n🧪 Testing {agent_name.title()} Agent...")
                if agent_name in self.agents and self.agents[agent_name]:
                    result = self.agents[agent_name].run(test_task)
                    print(f"✅ {agent_name} test result: {str(result)[:100]}...")
                else:
                    print(f"❌ {agent_name} agent not available")
            except Exception as e:
                print(f"❌ {agent_name} agent test failed: {e}")

    def interactive_mode(self):
        """Enhanced interactive mode with smart task detection"""
        print("\n" + "="*60)
        print("🎮 Smart Agent System - Interactive Mode")
        print("🧠 Automatically detects task complexity and uses minimal agents")
        print("="*60)
        print("Examples:")
        print("• 'get current directory' → file_handler only")
        print("• 'create simple calculator' → coder + executor")
        print("• 'build web scraper' → planner + researcher + coder + installer + executor")
        print("• 'install numpy' → installer only")
        print("="*60)
        
        while True:
            request = input("\n🎯 Enter your request (or 'quit' to exit): ").strip()
            
            if request.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            elif request.lower() == 'test':
                self.test_individual_agents()
                continue
            elif not request:
                print("❌ Please enter a request")
                continue
            
            try:
                result = self.handle_request(request)
                print(f"\n🏁 Final Result:\n{result}")
            except Exception as e:
                print(f"❌ Error processing request: {e}")
            
            print("\n" + "="*60)

if __name__ == "__main__":
    # Use the provided path
    base_path = Path(r"C:\Users\z0053h8u\Documents\Awishkar25\Ultronai\UltronAI\projects")
    
    print(f"🚀 Starting Smart Agent System")
    print(f"📁 Base directory: {base_path}")
    
    try:
        # Initialize the smart agent system
        smart_agent = SmartAgentOrchestrator(base_dir=base_path)
        
        # Test system readiness
        print("\n🔍 Testing system readiness...")
        smart_agent.test_individual_agents()
        
        # Start interactive mode
        smart_agent.interactive_mode()
            
    except Exception as e:
        print(f"💥 Critical error starting the system: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure all agent files exist in the Agents/ directory")
        print("2. Check that your .env file has the GROQ_API_KEY")
        print("3. Verify all required packages are installed")
        print("4. Try using a simpler path like Path('./projects')")
        print("5. Ensure all agent classes have the same interface (run method)")
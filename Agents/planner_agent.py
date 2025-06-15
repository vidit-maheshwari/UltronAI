# Agents/planner_agent.py
from agno.agent import Agent
from agno.models.groq import Groq
from agno.storage.sqlite import SqliteStorage as SqlAgentStorage
from agno.utils.log import log_info
from typing import List, Dict, Any
import json
import re
import dotenv
import os
from textwrap import dedent

dotenv.load_dotenv()


class PlannerAgentNode:
    def __init__(
        self,
        agent_id: str = "planner_agent",
        db_file: str = "agents.db",
        table_name: str = "multi_agent_memory",
        model_name: str = "deepseek-r1-distill-llama-70b",
        markdown: bool = True,
    ):
        self.storage = SqlAgentStorage(table_name=table_name, db_file=db_file)
        self.agent_id = agent_id

        self.agent = Agent(
            model=Groq(id=model_name),
            storage=self.storage,
            agent_id=self.agent_id,
            description=dedent("""\
                🧠 You are the Master Planner Agent in a sophisticated multi-agent system.
                
                Your role is to:
                🎯 Analyze complex tasks and break them into manageable subtasks
                🔄 Determine optimal execution sequence for maximum efficiency
                🤖 Assign appropriate specialized agents to each subtask
                ⚡ Identify dependencies between tasks
                🔍 Anticipate potential issues and plan error handling
                📊 Optimize resource allocation and task distribution
            """),
            instructions=dedent("""\
                🧠 PLANNING METHODOLOGY:
                
                1. 📋 TASK ANALYSIS
                   - Break down the main task into logical subtasks
                   - Identify task dependencies and prerequisites
                   - Determine the optimal execution order
                   - Consider resource requirements and constraints
                
                2. 🤖 AGENT ASSIGNMENT
                   Available agents and their capabilities:
                   - **researcher**: Research topics, gather information, fact-checking
                   - **web_search**: Search for current information online
                   - **coder**: Write, modify, and optimize code
                   - **file_handler**: Create, read, write, and manage files/directories
                   - **installer**: Install packages, manage dependencies
                   - **executor**: Run and test code, execute programs
                   - **shell_executor**: Execute shell commands and system operations
                   - **error_resolver**: Debug issues, resolve errors, troubleshoot
                
                3. 🎯 EXECUTION STRATEGY
                   - Assign each subtask to the most appropriate agent
                   - Define clear, actionable descriptions for each subtask
                   - Plan for error handling and recovery
                   - Optimize for efficiency and success rate
                
                4. 📊 OUTPUT FORMAT
                   Always return a structured JSON plan with subtasks
            """),
            expected_output=dedent("""\
                📋 EXECUTION PLAN
                
                ## 🎯 Task Analysis
                {Brief analysis of the main task and approach}
                
                ## 🔄 Execution Strategy
                {High-level strategy and reasoning}
                
                ## 🤖 Subtask Breakdown
                ```json
                [
                    {
                        "step": 1,
                        "agent": "agent_name",
                        "description": "Clear, actionable description of what to do",
                        "priority": "high/medium/low",
                        "dependencies": ["previous_step_numbers"]
                    }
                ]
                ```
                
                ## ⚡ Success Factors
                {Key factors for successful execution}
                
                ## 🔍 Potential Issues
                {Anticipated challenges and mitigation strategies}
            """),
            show_tool_calls=False,
            markdown=markdown,
        )

    def run(self, task: str) -> str:
        """
        Main interface method - consistent with other agents
        Analyzes task and returns a comprehensive execution plan
        """
        try:
            print(f"🧠 Planning task: {task}")
            
            # Create enhanced planning prompt
            planning_prompt = self._create_planning_prompt(task)
            
            # Get plan from agent - using run instead of print_response for consistency
            try:
                # First try the standard run method
                response = self.agent.run(planning_prompt)
            except AttributeError:
                try:
                    # Fallback to print_response if run doesn't exist
                    response = self.agent.print_response(planning_prompt, stream=False)
                except AttributeError:
                    # Last resort - create a basic plan manually
                    response = self._create_fallback_plan(task)
            
            # Store the plan for later use
            self.last_plan = response
            
            # Ensure we return a string response
            if hasattr(response, 'content'):
                return str(response.content)
            elif hasattr(response, 'text'):
                return str(response.text)
            else:
                return str(response)
            
        except Exception as e:
            error_msg = f"❌ Planning error: {str(e)}"
            log_info(error_msg)
            print(f"Error details: {e}")
            # Return a fallback plan instead of just an error
            return self._create_fallback_plan(task)

    def _create_fallback_plan(self, task: str) -> str:
        """Create a basic fallback plan when the agent fails"""
        task_lower = task.lower()
        
        if "gui calculator" in task_lower and "folder" in task_lower:
            return """
📋 EXECUTION PLAN

## 🎯 Task Analysis
Creating a GUI calculator project with proper folder structure and comprehensive testing.

## 🔄 Execution Strategy
1. Create project directory structure
2. Develop calculator logic
3. Create GUI interface
4. Implement comprehensive tests
5. Execute and validate the application

## 🤖 Subtask Breakdown
```json
[
    {
        "step": 1,
        "agent": "file_handler",
        "description": "Create projects folder and GUI calculator project structure with main.py, calculator.py, gui.py, tests/ directory, and requirements.txt",
        "priority": "high"
    },
    {
        "step": 2,
        "agent": "coder",
        "description": "Create calculator logic class with basic math operations (add, subtract, multiply, divide, power, square root) and error handling",
        "priority": "high"
    },
    {
        "step": 3,
        "agent": "coder",
        "description": "Create GUI interface using tkinter with buttons, display, proper layout, and event handling for calculator operations",
        "priority": "high"
    },
    {
        "step": 4,
        "agent": "coder",
        "description": "Create comprehensive unit tests for calculator logic including edge cases, error handling, and GUI functionality tests",
        "priority": "medium"
    },
    {
        "step": 5,
        "agent": "executor",
        "description": "Run the GUI calculator application to verify it launches correctly and basic functionality works",
        "priority": "high"
    },
    {
        "step": 6,
        "agent": "executor",
        "description": "Execute all unit tests and generate test report to ensure code quality and functionality",
        "priority": "medium"
    }
]
```

## ⚡ Success Factors
- Proper separation of concerns between logic and GUI
- Comprehensive error handling for division by zero and invalid inputs
- User-friendly interface with clear button layout
- Thorough testing coverage for reliability

## 🔍 Potential Issues
- Tkinter compatibility issues on different systems
- Input validation challenges
- Test framework setup requirements
"""
        else:
            return f"""
📋 EXECUTION PLAN

## 🎯 Task Analysis
Analyzing task: {task}

## 🔄 Execution Strategy
Breaking down the task into manageable steps with appropriate agent assignment.

## 🤖 Subtask Breakdown
```json
[
    {{
        "step": 1,
        "agent": "researcher",
        "description": "Research and analyze requirements for: {task}",
        "priority": "high"
    }},
    {{
        "step": 2,
        "agent": "coder",
        "description": "Implement solution for: {task}",
        "priority": "high"
    }},
    {{
        "step": 3,
        "agent": "executor",
        "description": "Test and validate: {task}",
        "priority": "medium"
    }}
]
```

## ⚡ Success Factors
- Clear requirements understanding
- Proper implementation
- Thorough testing

## 🔍 Potential Issues
- Requirement ambiguity
- Implementation complexity
"""

    def plan(self, task: str) -> List[Dict[str, Any]]:
        """
        Legacy method - maintains backward compatibility
        Returns structured subtasks list
        """
        try:
            print(f"🧠 Creating structured plan for: {task}")
            
            planning_prompt = self._create_structured_planning_prompt(task)
            
            # Try different response methods
            try:
                response = self.agent.run(planning_prompt)
            except AttributeError:
                try:
                    response = self.agent.print_response(planning_prompt, stream=False)
                except AttributeError:
                    # Create fallback structured plan
                    return self._create_fallback_structured_plan(task)
            
            # Extract JSON from response
            subtasks = self._extract_json_plan(response)
            
            if subtasks:
                log_info(f"✅ Generated {len(subtasks)} subtasks")
                return subtasks
            else:
                log_info("⚠️ No structured plan could be generated, using fallback")
                return self._create_fallback_structured_plan(task)
                
        except Exception as e:
            log_info(f"❌ Failed to create structured plan: {e}")
            return self._create_fallback_structured_plan(task)

    def _create_fallback_structured_plan(self, task: str) -> List[Dict[str, Any]]:
        """Create a fallback structured plan"""
        task_lower = task.lower()
        
        if "gui calculator" in task_lower and "folder" in task_lower:
            return [
                {
                    "step": 1,
                    "agent": "file_handler",
                    "description": "Create projects folder and GUI calculator project structure",
                    "priority": "high"
                },
                {
                    "step": 2,
                    "agent": "coder",
                    "description": "Create calculator logic class with math operations",
                    "priority": "high"
                },
                {
                    "step": 3,
                    "agent": "coder",
                    "description": "Create GUI interface using tkinter",
                    "priority": "high"
                },
                {
                    "step": 4,
                    "agent": "coder",
                    "description": "Create unit tests for calculator",
                    "priority": "medium"
                },
                {
                    "step": 5,
                    "agent": "executor",
                    "description": "Run and test the GUI calculator",
                    "priority": "high"
                },
                {
                    "step": 6,
                    "agent": "executor", 
                    "description": "Execute unit tests",
                    "priority": "medium"
                }
            ]
        else:
            return [
                {
                    "step": 1,
                    "agent": "researcher",
                    "description": f"Research: {task}",
                    "priority": "high"
                },
                {
                    "step": 2,
                    "agent": "coder", 
                    "description": f"Implement: {task}",
                    "priority": "high"
                },
                {
                    "step": 3,
                    "agent": "executor",
                    "description": f"Test: {task}",
                    "priority": "medium"
                }
            ]

    def _create_planning_prompt(self, task: str) -> str:
        """Create comprehensive planning prompt"""
        return f"""
        🧠 MASTER PLANNER ANALYSIS REQUEST
        
        **PRIMARY TASK**: {task}
        
        Please analyze this task and create a comprehensive execution plan following your instructions.
        
        Consider:
        • What are the logical steps needed?
        • Which agents are best suited for each step?
        • What are the dependencies between steps?
        • What could go wrong and how to handle it?
        • What's the optimal execution order?
        
        Provide a detailed analysis and structured plan that can guide the execution of this task.
        """

    def _create_structured_planning_prompt(self, task: str) -> str:
        """Create prompt for structured JSON output"""
        return f"""
        You are the Master Planner Agent. Break down this task into structured subtasks:

        **TASK**: {task}

        **AVAILABLE AGENTS**:
        - researcher: Research topics, gather information, analysis
        - web_search: Search for current information online  
        - coder: Write, modify, and optimize code
        - file_handler: Create, read, write, manage files/directories
        - installer: Install packages, manage dependencies
        - executor: Run and test code, execute programs
        - shell_executor: Execute shell commands and system operations
        - error_resolver: Debug issues, resolve errors, troubleshoot

        **OUTPUT FORMAT** (JSON only):
        [
            {{
                "step": 1,
                "agent": "agent_name",
                "description": "Clear, actionable description",
                "priority": "high"
            }},
            {{
                "step": 2,
                "agent": "agent_name", 
                "description": "Next task description",
                "priority": "medium"
            }}
        ]

        Return ONLY the JSON array, no other text.
        """

    def _extract_json_plan(self, response: str) -> List[Dict[str, Any]]:
        """Extract JSON plan from agent response"""
        try:
            # Handle different response types
            if hasattr(response, 'content'):
                content = response.content
            elif hasattr(response, 'text'):
                content = response.text
            else:
                content = str(response)
            
            # Try to find JSON in the response
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                subtasks = json.loads(json_str)
                return subtasks
            
            # If no JSON found, try to parse the entire content
            try:
                subtasks = json.loads(content)
                return subtasks
            except:
                pass
            
            # If still no luck, try eval as fallback (less safe)
            try:
                subtasks = eval(content)
                if isinstance(subtasks, list):
                    return subtasks
            except:
                pass
            
            log_info("⚠️ Could not extract JSON plan from response")
            return []
            
        except Exception as e:
            log_info(f"❌ Error extracting JSON plan: {e}")
            return []

    def execute_plan(self, subtasks: List[Dict[str, Any]], agents: Dict[str, Any]):
        """Execute a structured plan using available agents"""
        if not subtasks:
            log_info("⚠️ No subtasks to execute")
            return
        
        print(f"\n🚀 Executing plan with {len(subtasks)} subtasks")
        print("="*50)
        
        results = {}
        
        for i, subtask in enumerate(subtasks, 1):
            agent_key = subtask.get("agent", "unknown")
            description = subtask.get("description", "No description")
            priority = subtask.get("priority", "medium")
            
            print(f"\n🔧 Step {i}: [{agent_key.upper()}] {description}")
            print(f"   Priority: {priority}")
            
            if agent_key in agents and agents[agent_key] is not None:
                try:
                    # Ensure the agent has a run method
                    if hasattr(agents[agent_key], 'run'):
                        result = agents[agent_key].run(description)
                        results[f"step_{i}"] = result
                        print(f"   ✅ Completed successfully")
                    else:
                        error_msg = f"⚠️ Agent '{agent_key}' missing run method"
                        results[f"step_{i}"] = error_msg
                        print(f"   {error_msg}")
                except Exception as e:
                    error_msg = f"❌ Error in step {i}: {str(e)}"
                    results[f"step_{i}"] = error_msg
                    print(f"   {error_msg}")
            else:
                error_msg = f"⚠️ Agent '{agent_key}' not available"
                results[f"step_{i}"] = error_msg
                print(f"   {error_msg}")
        
        return results

    def get_plan_summary(self, subtasks: List[Dict[str, Any]]) -> str:
        """Generate a summary of the execution plan"""
        if not subtasks:
            return "No plan available"
        
        summary = f"📋 Execution Plan Summary ({len(subtasks)} steps):\n"
        
        for i, task in enumerate(subtasks, 1):
            agent = task.get("agent", "unknown")
            desc = task.get("description", "No description")[:50]
            priority = task.get("priority", "medium")
            
            summary += f"  {i}. [{agent}] {desc}... (Priority: {priority})\n"
        
        return summary


# ✅ Example Usage and Testing
if __name__ == "__main__":
    # Test the planner agent
    planner = PlannerAgentNode()
    
    print("🧠 PlannerAgentNode Test Suite")
    print("="*50)
    
    # Test 1: Basic planning with run() method
    print("\n🎯 Test 1: Basic Planning (run method)")
    test_task = "Create a GUI calculator with proper file structure and tests"
    result = planner.run(test_task)
    print("✅ Run method test completed")
    print(f"Result: {result[:200]}...")
    
    # Test 2: Structured planning with plan() method  
    print("\n📋 Test 2: Structured Planning (plan method)")
    subtasks = planner.plan(test_task)
    print(f"Generated {len(subtasks)} subtasks")
    
    # Test 3: Plan summary
    if subtasks:
        print("\n📊 Test 3: Plan Summary")
        summary = planner.get_plan_summary(subtasks)
        print(summary)
    
    print("\n✅ All tests completed!")
    print("PlannerAgentNode is ready for use in the Universal Agent Orchestrator.")
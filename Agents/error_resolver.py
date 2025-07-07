# Agents/error_resolver.py

from agno.agent import Agent
from agno.models.groq import Groq
from agno.storage.sqlite import SqliteStorage
from agno.utils.log import log_info
import dotenv
import json
import re
from typing import Dict, Any, List, Optional
from shared_state import SharedState

dotenv.load_dotenv()


class ErrorResolverAgentNode:
    def __init__(
        self,
        agent_id: str = "error_resolver_agent",
        db_file: str = "agents.db",
        table_name: str = "error_resolver_sessions",
    ):
        self.storage = SqliteStorage(table_name=table_name, db_file=db_file)
        self.agent_id = agent_id

        # Root Cause Analysis Agent - Identifies the underlying cause of errors
        self.root_cause_analyzer = Agent(
            model=Groq(id="deepseek-r1-distill-llama-70b"),
            agent_id=f"{self.agent_id}_root_cause_analyzer",
            storage=self.storage,
            show_tool_calls=False,
            instructions="""You are an expert root cause analysis specialist. Your job is to:
            
            1. **Identify the Root Cause**: What is the fundamental reason this error occurred?
            2. **Analyze Error Patterns**: Is this a one-time error or a systemic issue?
            3. **Assess Impact**: How does this error affect the overall goal?
            4. **Identify Contributing Factors**: What conditions led to this error?
            5. **Predict Future Issues**: Are there similar errors likely to occur?
            
            **Root Cause Categories:**
            - **Systemic Issues**: Problems with the overall approach or architecture
            - **Quality Issues**: Poor output quality that needs refinement
            - **Dependency Issues**: Missing prerequisites or tools
            - **Configuration Issues**: Incorrect setup or environment
            - **Logic Issues**: Flaws in the implementation approach
            - **Resource Issues**: Missing files, permissions, or system resources
            
            **Output Format:**
            Return a JSON object with this structure:
            {
                "root_cause": "string",
                "category": "systemic|quality|dependency|configuration|logic|resource",
                "severity": "critical|high|medium|low",
                "impact_analysis": "string",
                "contributing_factors": ["string"],
                "systemic_issues": ["string"],
                "recommended_approach": "string",
                "prevention_measures": ["string"]
            }
            """
        )

        # Fix Strategy Agent - Creates intelligent fix strategies
        self.fix_strategy_agent = Agent(
            model=Groq(id="deepseek-r1-distill-llama-70b"),
            agent_id=f"{self.agent_id}_fix_strategy",
            storage=self.storage,
            show_tool_calls=False,
            instructions="""You are an expert fix strategy specialist. Your job is to:
            
            1. **Design Fix Strategy**: Create a comprehensive approach to resolve the root cause
            2. **Prioritize Fixes**: Order fixes by impact and dependency
            3. **Consider Side Effects**: Ensure fixes don't create new problems
            4. **Plan for Prevention**: Include steps to prevent similar issues
            5. **Validate Approach**: Ensure the strategy addresses the root cause
            
            **Fix Strategy Principles:**
            - **Address Root Cause**: Don't just fix symptoms
            - **Systematic Approach**: Fix issues in logical order
            - **Quality Focus**: Ensure fixes improve overall quality
            - **Prevention**: Include steps to prevent recurrence
            - **Validation**: Include verification steps
            
            **Output Format:**
            Return a JSON object with this structure:
            {
                "fix_strategy": "string",
                "fix_priorities": [
                    {
                        "priority": 1-5,
                        "category": "string",
                        "description": "string",
                        "expected_impact": "string"
                    }
                ],
                "fix_steps": [
                    {
                        "step": "string",
                        "agent": "string",
                        "description": "string",
                        "validation": "string"
                    }
                ],
                "prevention_steps": ["string"],
                "success_criteria": ["string"]
            }
            """
        )

        # Plan Generator Agent - Creates the actual fix plan
        self.plan_generator = Agent(
            model=Groq(id="deepseek-r1-distill-llama-70b"),
            agent_id=f"{self.agent_id}_plan_generator",
            storage=self.storage,
            show_tool_calls=False,
            instructions="""You are the master Error Resolution Planner. Your job is to create JSON arrays of subtasks.
            You MUST use the following strict "Command Language" for the 'description' field of each subtask.

            **COMMAND LANGUAGE REFERENCE:**
            - To create a file or directory: `{"agent": "shell_agent", "description": "mkdir -p directory_name"}` or `{"agent": "file_agent", "description": "CREATE EMPTY FILE 'filename.ext'"}`
            - To fix code: `{"agent": "coder_agent", "description": "Generate code for 'filename.ext' that fixes..."}` followed by `{"agent": "file_agent", "description": "SAVE CODE TO 'filename.ext'"}`
            - To run a shell command: `{"agent": "shell_agent", "description": "executable_command_string"}`
            - To read existing files: `{"agent": "file_agent", "description": "READ FILE 'filename.ext'"}`
            - To refine existing code: `{"agent": "coder_agent", "description": "Refine and improve the code for 'filename.ext' to address..."}`
            - To install dependencies: `{"agent": "shell_agent", "description": "pip install package_name"}` or `{"agent": "shell_agent", "description": "npm install package_name"}`

            **CRITICAL RULES:**
            1. **Address Root Cause**: Focus on fixing the underlying issue, not just symptoms
            2. **Systematic Approach**: Fix issues in logical order (dependencies first, then implementation)
            3. **Quality Focus**: If the issue is poor quality, create refinement steps
            4. **Prevention**: Include steps to prevent similar issues in the future
            5. **Validation**: Include verification steps to ensure fixes work
            6. **If the error is unfixable**: Use `{"agent": "human_intervention", "description": "Explain the problem clearly to the user."}`

            Your output **MUST** be ONLY a valid JSON array in the format `[{"agent": "...", "description": "..."}, ...]`. No other text or keys.
            """
        )

    def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Safely parse JSON from agent response."""
        try:
            # Find JSON in the response
            json_match = re.search(r'\{[\s\S]*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return None
        except json.JSONDecodeError as e:
            log_info(f"Failed to parse JSON response: {e}")
            return None

    def _analyze_root_cause(self, error_context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform root cause analysis of the error."""
        log_info("Performing root cause analysis...")
        
        analysis_prompt = f"""
        Analyze the following error to identify the root cause:
        
        **Error Context:**
        - **Original Task:** {error_context.get('original_task', 'Unknown')}
        - **Error Message:** {error_context.get('last_execution_error', 'Unknown')}
        - **Last Output:** {error_context.get('last_execution_output', 'None')}
        - **Project Directory:** {error_context.get('project_directory', 'Not set')}
        - **Recent History:** {', '.join(error_context.get('history', [])[-3:])}
        
        Identify the root cause, categorize the issue, and assess its impact.
        """
        
        response = self.root_cause_analyzer.run(analysis_prompt)
        root_cause_analysis = self._parse_json_response(response.content)
        
        if not root_cause_analysis:
            log_info("Root cause analysis failed, using default analysis")
            root_cause_analysis = {
                "root_cause": "Unknown error occurred",
                "category": "systemic",
                "severity": "medium",
                "impact_analysis": "Error prevents task completion",
                "contributing_factors": ["Unknown"],
                "systemic_issues": [],
                "recommended_approach": "Investigate and fix the error",
                "prevention_measures": ["Better error handling"]
            }
        
        log_info(f"Root cause analysis complete. Category: {root_cause_analysis.get('category', 'Unknown')}")
        return root_cause_analysis

    def _create_fix_strategy(self, root_cause_analysis: Dict[str, Any], error_context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a comprehensive fix strategy based on root cause analysis."""
        log_info("Creating fix strategy...")
        
        strategy_prompt = f"""
        Create a fix strategy based on the root cause analysis:
        
        **Root Cause Analysis:**
        {json.dumps(root_cause_analysis, indent=2)}
        
        **Error Context:**
        - **Original Task:** {error_context.get('original_task', 'Unknown')}
        - **Error Message:** {error_context.get('last_execution_error', 'Unknown')}
        - **Project Directory:** {error_context.get('project_directory', 'Not set')}
        
        Design a comprehensive fix strategy that addresses the root cause and prevents future issues.
        """
        
        response = self.fix_strategy_agent.run(strategy_prompt)
        fix_strategy = self._parse_json_response(response.content)
        
        if not fix_strategy:
            log_info("Fix strategy creation failed, using default strategy")
            fix_strategy = {
                "fix_strategy": "Address the immediate error and improve error handling",
                "fix_priorities": [
                    {
                        "priority": 1,
                        "category": "immediate",
                        "description": "Fix the current error",
                        "expected_impact": "Resume task execution"
                    }
                ],
                "fix_steps": [
                    {
                        "step": "Fix the error",
                        "agent": "coder_agent",
                        "description": "Generate corrected code",
                        "validation": "Verify the fix works"
                    }
                ],
                "prevention_steps": ["Improve error handling"],
                "success_criteria": ["Error is resolved", "Task can continue"]
            }
        
        log_info(f"Fix strategy created with {len(fix_strategy.get('fix_steps', []))} steps")
        return fix_strategy

    def _generate_intelligent_fix_plan(self, root_cause_analysis: Dict[str, Any], fix_strategy: Dict[str, Any], error_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate an intelligent fix plan based on root cause analysis and fix strategy."""
        log_info("Generating intelligent fix plan...")
        
        # Prepare context for plan generation
        context_summary = f"""
        **Root Cause:** {root_cause_analysis.get('root_cause', 'Unknown')}
        **Category:** {root_cause_analysis.get('category', 'Unknown')}
        **Severity:** {root_cause_analysis.get('severity', 'medium')}
        
        **Fix Strategy:** {fix_strategy.get('fix_strategy', 'Standard fix approach')}
        **Priorities:** {', '.join([f"{p.get('priority')}: {p.get('description')}" for p in fix_strategy.get('fix_priorities', [])])}
        
        **Error Context:**
        - Original Task: {error_context.get('original_task', 'Unknown')}
        - Error: {error_context.get('last_execution_error', 'Unknown')}
        - Project: {error_context.get('project_directory', 'Not set')}
        """
        
        plan_prompt = f"""
        Create a fix plan based on the following analysis:
        
        {context_summary}
        
        **Fix Steps to Implement:**
        {json.dumps(fix_strategy.get('fix_steps', []), indent=2)}
        
        **Success Criteria:**
        {', '.join(fix_strategy.get('success_criteria', []))}
        
        Create a JSON array of subtasks that will implement this fix strategy.
        Focus on addressing the root cause, not just symptoms.
        """
        
        response = self.plan_generator.run(plan_prompt)
        fix_plan = self._parse_fix_plan_from_response(response.content)
        
        if not fix_plan:
            log_info("Intelligent fix plan generation failed")
            return []
        
        log_info(f"Intelligent fix plan generated with {len(fix_plan)} steps")
        return fix_plan

    def _parse_fix_plan_from_response(self, response: str) -> List[Dict[str, Any]]:
        """Parses a JSON array of subtasks from the LLM's response."""
        try:
            match = re.search(r'\[\s*\{[\s\S]*?\}\s*\]', response, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return []
        except Exception as e:
            log_info(f"Error parsing fix plan: {e}")
            return []

    def _handle_special_error_cases(self, error_message: str) -> Optional[List[Dict[str, Any]]]:
        """Handle common error patterns with specific fixes."""
        error_lower = error_message.lower()
        
        # Command not found errors
        if "command not found" in error_lower:
            if "wget" in error_lower:
                return [
                    {"agent": "shell_agent", "description": "curl -O filename"}
                ]
            elif "pip" in error_lower:
                return [
                    {"agent": "shell_agent", "description": "python -m pip install package_name"}
                ]
            elif "npm" in error_lower:
                return [
                    {"agent": "shell_agent", "description": "node --version"},
                    {"agent": "human_intervention", "description": "Node.js/npm not installed. Please install Node.js to continue."}
                ]
            elif "xdg-open" in error_lower:
                return [
                    {"agent": "shell_agent", "description": "open index.html"}
                ]
        
        # Permission errors
        elif "permission denied" in error_lower:
            return [
                {"agent": "shell_agent", "description": "chmod +x filename"},
                {"agent": "human_intervention", "description": "Permission issues detected. Please check file permissions and try again."}
            ]
        
        # File not found errors
        elif "no such file or directory" in error_lower:
            return [
                {"agent": "file_agent", "description": "CREATE PROJECT STRUCTURE"},
                {"agent": "coder_agent", "description": "Generate index.html using the available document content"},
                {"agent": "file_agent", "description": "SAVE CODE TO 'index.html'"}
            ]
        
        # Project structure issues (wrong type created)
        elif any(phrase in error_lower for phrase in ["react", "package.json", "src/", "node_modules", "python_package", "setup.py"]):
            return [
                {"agent": "file_agent", "description": "CREATE STANDARD STRUCTURE web_project"},
                {"agent": "coder_agent", "description": "Generate index.html using the available document content"},
                {"agent": "file_agent", "description": "SAVE CODE TO 'index.html'"}
            ]
        
        # Import errors
        elif "import" in error_lower and "error" in error_lower:
            return [
                {"agent": "shell_agent", "description": "pip install -r requirements.txt"},
                {"agent": "coder_agent", "description": "Regenerate the code with proper import statements and error handling"}
            ]
        
        return None

    def _create_simple_fallback_plan(self, shared_state: 'SharedState') -> List[Dict[str, Any]]:
        """Create a simple, direct plan when the system gets stuck in loops."""
        log_info("Creating simple fallback plan")
        
        # Analyze the original task to create a minimal viable plan
        task_lower = shared_state.original_task.lower()
        
        if "portfolio" in task_lower or "resume" in task_lower:
            # Simple portfolio plan
            return [
                {"agent": "file_agent", "description": "CREATE PROJECT STRUCTURE"},
                {"agent": "coder_agent", "description": "Generate index.html using the available document content"},
                {"agent": "file_agent", "description": "SAVE CODE TO 'index.html'"},
                {"agent": "coder_agent", "description": "Generate styles.css for responsive and attractive styling"},
                {"agent": "file_agent", "description": "SAVE CODE TO 'styles.css'"},
                {"agent": "coder_agent", "description": "Generate script.js for interactive functionality"},
                {"agent": "file_agent", "description": "SAVE CODE TO 'script.js'"}
            ]
        else:
            # Generic simple plan
            return [
                {"agent": "file_agent", "description": "CREATE PROJECT STRUCTURE"},
                {"agent": "coder_agent", "description": "Generate the main code file based on the task requirements"},
                {"agent": "file_agent", "description": "SAVE CODE TO the generated file"},
                {"agent": "human_intervention", "description": "Review the generated output and provide feedback"}
            ]

    def run(self, shared_state: 'SharedState') -> List[Dict[str, Any]]:
        """
        Analyzes an error from the shared state and returns an intelligent plan to fix it.
        """
        
        try:
            log_info("Error Resolver Agent is performing intelligent error resolution...")
            
            # Check for infinite loop prevention
            if len(shared_state.history) > 20:
                log_info("Too many error resolution attempts, creating simple fallback plan")
                return self._create_simple_fallback_plan(shared_state)
            
            # Check if we're stuck in a loop with the same error
            recent_errors = [h for h in shared_state.history[-5:] if "error" in h.lower()]
            if len(recent_errors) >= 3:
                log_info("Detected error loop, creating simple fallback plan")
                return self._create_simple_fallback_plan(shared_state)
            
            # Prepare error context
            error_context = {
                "original_task": shared_state.original_task,
                "last_execution_error": shared_state.last_execution_error,
                "last_execution_output": shared_state.last_execution_output,
                "project_directory": str(shared_state.project_directory) if shared_state.project_directory else None,
                "history": shared_state.history[-5:] if shared_state.history else []
            }
            
            # Step 1: Check for special error cases first
            special_fix = self._handle_special_error_cases(shared_state.last_execution_error or "")
            if special_fix:
                log_info("Special error case detected, using specific fix")
                return special_fix
            
            # Step 2: Perform root cause analysis
            root_cause_analysis = self._analyze_root_cause(error_context)
            
            # Step 3: Create fix strategy
            fix_strategy = self._create_fix_strategy(root_cause_analysis, error_context)
            
            # Step 4: Generate intelligent fix plan
            fix_plan = self._generate_intelligent_fix_plan(root_cause_analysis, fix_strategy, error_context)
            
            if not fix_plan:
                log_info("Intelligent error resolution failed, falling back to human intervention")
                return [{"agent": "human_intervention", "description": f"Automatic error resolution failed. Root cause: {root_cause_analysis.get('root_cause', 'Unknown')}. Please review and resolve manually."}]
            
            # Log the resolution approach
            shared_state.add_to_history(f"Error resolved using {root_cause_analysis.get('category', 'Unknown')} approach. Root cause: {root_cause_analysis.get('root_cause', 'Unknown')}")
            
            log_info(f"Intelligent error resolution completed with {len(fix_plan)} steps")
            return fix_plan

        except Exception as e:
            log_info(f"A critical error occurred in the ErrorResolverAgentNode: {e}")
            return [{"agent": "human_intervention", "description": f"Critical failure in error resolver: {e}"}]
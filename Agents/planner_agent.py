# Agents/planner_agent.py

from agno.agent import Agent
from agno.models.groq import Groq
from agno.storage.sqlite import SqliteStorage as SqlAgentStorage
from agno.utils.log import log_info
from typing import List, Dict, Any, Optional
import dotenv
import json
import re

dotenv.load_dotenv()


class PlannerAgentNode:
    def __init__(
        self,
        agent_id: str = "planner_agent",
        db_file: str = "agents.db",
        table_name: str = "multi_agent_memory",
        model_name: str = "deepseek-r1-distill-llama-70b",
    ):
        self.storage = SqlAgentStorage(table_name=table_name, db_file=db_file)
        self.agent_id = agent_id

        # Goal Analysis Agent - Analyzes the ultimate goal and success criteria
        self.goal_analyzer = Agent(
            model=Groq(id="deepseek-r1-distill-llama-70b"),
            agent_id=f"{self.agent_id}_goal_analyzer",
            storage=self.storage,
            show_tool_calls=False,
            instructions="""You are an expert goal analysis specialist. Your job is to:
            
            1. **Extract the Ultimate Goal**: Identify what the user really wants to achieve
            2. **Define Success Criteria**: What would constitute a successful outcome?
            3. **Identify Quality Indicators**: What specific qualities should the final output have?
            4. **Assess Complexity**: How complex is this task?
            5. **Identify Dependencies**: What needs to happen first?
            
            **Output Format:**
            Return a JSON object with this structure:
            {
                "ultimate_goal": "string",
                "success_criteria": ["string"],
                "quality_indicators": {
                    "functionality": ["string"],
                    "appearance": ["string"],
                    "performance": ["string"],
                    "usability": ["string"]
                },
                "complexity_level": "simple|moderate|complex",
                "estimated_steps": number,
                "critical_dependencies": ["string"],
                "risk_factors": ["string"]
            }
            """
        )

        # Quality Assessment Agent - Evaluates output quality and identifies issues
        self.quality_assessor = Agent(
            model=Groq(id="deepseek-r1-distill-llama-70b"),
            agent_id=f"{self.agent_id}_quality_assessor",
            storage=self.storage,
            show_tool_calls=False,
            instructions="""You are an expert quality assessment specialist. Your job is to:
            
            1. **Evaluate Output Quality**: Assess if the output meets the success criteria
            2. **Identify Quality Issues**: What's missing, incomplete, or substandard?
            3. **Assess Completeness**: Does the output fulfill the original requirements?
            4. **Check for Errors**: Are there technical or logical errors?
            5. **Evaluate User Experience**: Is the output user-friendly and professional?
            
            **Quality Assessment Criteria:**
            - **Completeness**: Does it address all requirements?
            - **Functionality**: Does it work as intended?
            - **Quality**: Is it well-crafted and professional?
            - **User Experience**: Is it intuitive and appealing?
            - **Technical Soundness**: Is it technically correct?
            
            **Output Format:**
            Return a JSON object with this structure:
            {
                "overall_quality_score": 1-10,
                "meets_success_criteria": boolean,
                "quality_issues": [
                    {
                        "severity": "critical|high|medium|low",
                        "category": "completeness|functionality|quality|ux|technical",
                        "description": "string",
                        "impact": "string"
                    }
                ],
                "missing_requirements": ["string"],
                "recommendations": ["string"],
                "requires_refinement": boolean
            }
            """
        )

        # Plan Generator Agent - Creates execution plans
        self.plan_generator = Agent(
            model=Groq(id="deepseek-r1-distill-llama-70b"),
            agent_id=f"{self.agent_id}_plan_generator",
            storage=self.storage,
            show_tool_calls=False,
            instructions="""You are the master Planner Agent. Your job is to create JSON arrays of subtasks.
            You MUST use the following strict "Command Language" for the 'description' field of each subtask.

            **CRITICAL CONTEXT INSTRUCTION:**
            - **If the `document_content` field in the project state contains text, you MUST use this text as the source material for the project.**
            - Your plan should involve the `coder_agent` using this content to create the website. Do not use placeholder or fake content if real content is provided.

            **COMMAND LANGUAGE REFERENCE:**
            - To create the main project folder: `{"agent": "file_agent", "description": "CREATE PROJECT STRUCTURE"}`
            - To create a new, empty file: `{"agent": "file_agent", "description": "CREATE EMPTY FILE 'filename.ext'"}`
            - To create a new directory: `{"agent": "shell_agent", "description": "mkdir -p directory_name"}`
            - To generate code: `{"agent": "coder_agent", "description": "Generate code for 'filename.ext' that does..."}`
            - To save generated code: `{"agent": "file_agent", "description": "SAVE CODE TO 'filename.ext'"}`
            - To run a shell command: `{"agent": "shell_agent", "description": "executable_command_string"}`
            - To read existing files: `{"agent": "file_agent", "description": "READ FILE 'filename.ext'"}`
            - To refine existing code: `{"agent": "coder_agent", "description": "Refine and improve the code for 'filename.ext' to..."}`

            **CRITICAL RULES:**
            1. **If the user asks to modify an existing project, your FIRST step must be to use the `file_agent` to `READ FILE 'filename.ext'` for all relevant files.**
            2. **If quality assessment shows issues, create refinement steps using the `coder_agent` with specific improvement instructions.**
            3. **Always consider the ultimate goal and success criteria when planning.**
            4. **Your output **MUST** be ONLY the JSON array in the format `[{"agent": "...", "description": "..."}, ...]`. Do not add any other keys, text, or explanations.**
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

    def _analyze_goal(self, task: str) -> Dict[str, Any]:
        """Analyze the ultimate goal and success criteria."""
        log_info("Analyzing ultimate goal and success criteria...")
        
        goal_prompt = f"""
        Analyze the following task to understand the ultimate goal and success criteria:
        
        **Task:** {task}
        
        Extract the ultimate goal, success criteria, quality indicators, and assess complexity.
        """
        
        response = self.goal_analyzer.run(goal_prompt)
        goal_analysis = self._parse_json_response(response.content)
        
        if not goal_analysis:
            log_info("Goal analysis failed, using default analysis")
            goal_analysis = {
                "ultimate_goal": "Complete the requested task successfully",
                "success_criteria": ["Task completed", "Output is functional"],
                "quality_indicators": {
                    "functionality": ["Works as intended"],
                    "appearance": ["Looks professional"],
                    "performance": ["Runs efficiently"],
                    "usability": ["Easy to use"]
                },
                "complexity_level": "moderate",
                "estimated_steps": 5,
                "critical_dependencies": [],
                "risk_factors": []
            }
        
        log_info(f"Goal analysis complete. Ultimate goal: {goal_analysis.get('ultimate_goal', 'Unknown')}")
        return goal_analysis

    def _assess_output_quality(self, task: str, output: str, success_criteria: List[str]) -> Dict[str, Any]:
        """Assess the quality of agent output."""
        log_info("Assessing output quality...")
        
        assessment_prompt = f"""
        Assess the quality of the following output against the original task and success criteria:
        
        **Original Task:** {task}
        **Success Criteria:** {', '.join(success_criteria)}
        **Output:** {output[:2000]}...  # Truncated for analysis
        
        Evaluate if this output meets the success criteria and identify any quality issues.
        """
        
        response = self.quality_assessor.run(assessment_prompt)
        quality_assessment = self._parse_json_response(response.content)
        
        if not quality_assessment:
            log_info("Quality assessment failed, assuming acceptable quality")
            quality_assessment = {
                "overall_quality_score": 7,
                "meets_success_criteria": True,
                "quality_issues": [],
                "missing_requirements": [],
                "recommendations": [],
                "requires_refinement": False
            }
        
        log_info(f"Quality assessment complete. Score: {quality_assessment.get('overall_quality_score', 0)}/10")
        return quality_assessment

    def _generate_refinement_plan(self, task: str, quality_issues: List[Dict[str, Any]], current_output: str) -> List[Dict[str, Any]]:
        """Generate a plan to refine and improve the output."""
        log_info("Generating refinement plan...")
        
        # Convert quality issues to refinement instructions
        refinement_instructions = []
        for issue in quality_issues:
            severity = issue.get('severity', 'medium')
            description = issue.get('description', '')
            category = issue.get('category', 'quality')
            
            if severity in ['critical', 'high']:
                refinement_instructions.append(f"CRITICAL: {description}")
            else:
                refinement_instructions.append(f"IMPROVE: {description}")
        
        refinement_prompt = f"""
        The current output has quality issues that need to be addressed. Create a refinement plan.
        
        **Original Task:** {task}
        **Quality Issues:** {', '.join(refinement_instructions)}
        **Current Output:** {current_output[:1000]}...
        
        Create a plan to refine and improve the output to address these issues.
        """
        
        response = self.plan_generator.run(refinement_prompt)
        refinement_plan = self._parse_plan_from_response(response.content)
        
        if not refinement_plan:
            log_info("Refinement plan generation failed")
            return []
        
        log_info(f"Refinement plan generated with {len(refinement_plan)} steps")
        return refinement_plan

    def _parse_plan_from_response(self, response: str) -> List[Dict[str, Any]]:
        """A simplified parser to extract a JSON array from the LLM's response."""
        try:
            # Find the JSON array using a regular expression
            match = re.search(r'\[\s*\{[\s\S]*?\}\s*\]', response, re.DOTALL)
            if match:
                json_string = match.group(0)
                return json.loads(json_string)
            else:
                log_info("No valid JSON array found in the planner's response.")
                return []
        except json.JSONDecodeError as e:
            log_info(f"Error decoding JSON from planner response: {e}")
            return []
        except Exception as e:
            log_info(f"An unexpected error occurred while parsing the plan: {e}")
            return []

    def plan(self, current_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Creates a goal-oriented plan based on the current state of the system.
        
        Args:
            current_state (Dict[str, Any]): The full context from the SharedState object.

        Returns:
            List[Dict[str, Any]]: A list of subtasks.
        """
        
        try:
            log_info("Planner agent is creating a goal-oriented plan...")
            
            # Step 1: Analyze the ultimate goal
            goal_analysis = self._analyze_goal(current_state.get('original_task', ''))
            
            # Step 2: Check if we need to assess quality of previous output
            last_output = current_state.get('last_execution_output', '')
            last_error = current_state.get('last_execution_error', '')
            
            # Check if we already have document content and project structure
            has_document_content = bool(current_state.get('document_content'))
            has_project_structure = bool(current_state.get('project_directory'))
            
            # If we have content but no project structure, create simple structure
            if has_document_content and not has_project_structure:
                log_info("Document content available but no project structure, creating simple plan")
                
                # Determine the appropriate file to generate based on the task
                task_lower = current_state.get('original_task', '').lower()
                if any(keyword in task_lower for keyword in ["portfolio", "resume", "html", "website"]):
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
                    return [
                        {"agent": "file_agent", "description": "CREATE PROJECT STRUCTURE"},
                        {"agent": "coder_agent", "description": "Generate the main output file using the available document content"},
                        {"agent": "file_agent", "description": "SAVE CODE TO the generated file"}
                    ]
            
            if last_output and not last_error:
                # Assess the quality of the last output
                quality_assessment = self._assess_output_quality(
                    current_state.get('original_task', ''),
                    last_output,
                    goal_analysis.get('success_criteria', [])
                )
                
                # If quality is poor, generate refinement plan
                if quality_assessment.get('requires_refinement', False) or quality_assessment.get('overall_quality_score', 0) < 6:
                    log_info("Quality issues detected, generating refinement plan")
                    refinement_plan = self._generate_refinement_plan(
                        current_state.get('original_task', ''),
                        quality_assessment.get('quality_issues', []),
                        last_output
                    )
                    
                    if refinement_plan:
                        log_info(f"Generated refinement plan with {len(refinement_plan)} steps")
                        return refinement_plan
            
            # Step 3: Generate initial plan
            planning_prompt = f"""
            Given the current state of the project, create the next set of subtasks.

            **Goal Analysis:**
            - **Ultimate Goal:** {goal_analysis.get('ultimate_goal', 'Complete the task')}
            - **Success Criteria:** {', '.join(goal_analysis.get('success_criteria', []))}
            - **Complexity Level:** {goal_analysis.get('complexity_level', 'moderate')}
            - **Estimated Steps:** {goal_analysis.get('estimated_steps', 5)}

            **Current Project State:**
            - **Original Task:** {current_state.get('original_task')}
            - **Current Status:** {current_state.get('current_status')}
            - **Project Directory:** {current_state.get('project_directory', 'Not created yet.')}
            - **Files Created:** {current_state.get('created_files', 'None')}
            - **Last Execution Error:** {current_state.get('last_execution_error', 'None')}
            - **Document Content Available:** {'Yes' if current_state.get('document_content') else 'No'}
            - **Execution History:**
            {"\n".join([f"  - {h}" for h in current_state.get('history', [])[-5:]])}

            **CRITICAL INSTRUCTIONS:**
            1. If document content is already available, DO NOT try to read the file again
            2. Create a simple, direct plan with minimal steps (5-8 steps max)
            3. For portfolio tasks, create simple HTML/CSS/JS files, not complex frameworks
            4. Focus on generating the actual output files, not setup complexity
            5. Use the existing document content directly in code generation

            **Your Task:**
            Create a simple, direct plan that will achieve the ultimate goal efficiently.

            Return ONLY the JSON array.
            """

            response = self.plan_generator.run(planning_prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            log_info(f"Raw response from planner LLM: {content[:300]}...")

            subtasks = self._parse_plan_from_response(content)
            
            if not subtasks:
                log_info("Planner failed to generate a valid plan.")
                return []

            log_info(f"Planner created a goal-oriented plan with {len(subtasks)} steps.")
            return subtasks
                
        except Exception as e:
            log_info(f"A critical error occurred in the plan method: {e}")
            return []
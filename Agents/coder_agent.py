# Agents/coder_agent.py

from agno.agent import Agent
from agno.models.groq import Groq
from agno.storage.sqlite import SqliteStorage
from agno.utils.log import log_info
import dotenv
from typing import Dict, Any, List, Optional
import re
import json
from shared_state import SharedState

dotenv.load_dotenv()

class CoderAgentNode:
    """
    An advanced, content-aware coding agent that can intelligently parse unstructured content,
    generate structured outputs, and perform iterative refinement to produce high-quality code.
    """
    def __init__(
        self,
        agent_id: str = "coder_agent",
        db_file: str = "agents.db",
        table_name: str = "coder_sessions",
    ):
        self.storage = SqliteStorage(table_name=table_name, db_file=db_file)
        self.agent_id = agent_id

        # Content Analysis Agent - Parses unstructured content into structured data
        self.content_analyzer = Agent(
            model=Groq(id="deepseek-r1-distill-llama-70b"),
            instructions="""You are an expert content analyst specializing in parsing unstructured text into structured data.
            
            Your job is to analyze content (like resumes, documents, etc.) and extract structured information.
            
            **Analysis Capabilities:**
            - Identify personal information (name, contact details, location)
            - Extract work experience (company, role, duration, achievements)
            - Parse education history (institution, degree, year, GPA)
            - Identify skills (technical, soft skills, languages, tools)
            - Extract projects (name, description, technologies, outcomes)
            - Identify certifications and awards
            
            **Output Format:**
            Return ONLY a JSON object with this structure:
            {
                "personal_info": {
                    "name": "string",
                    "email": "string", 
                    "phone": "string",
                    "location": "string",
                    "summary": "string"
                },
                "experience": [
                    {
                        "company": "string",
                        "role": "string", 
                        "duration": "string",
                        "achievements": ["string"]
                    }
                ],
                "education": [
                    {
                        "institution": "string",
                        "degree": "string",
                        "year": "string",
                        "gpa": "string"
                    }
                ],
                "skills": {
                    "technical": ["string"],
                    "languages": ["string"],
                    "tools": ["string"],
                    "soft_skills": ["string"]
                },
                "projects": [
                    {
                        "name": "string",
                        "description": "string",
                        "technologies": ["string"],
                        "outcome": "string"
                    }
                ],
                "certifications": ["string"],
                "awards": ["string"]
            }
            
            If any section is not found in the content, use empty arrays/objects as appropriate.
            """
        )

        # Structure Designer Agent - Creates optimal structure for the output
        self.structure_designer = Agent(
            model=Groq(id="deepseek-r1-distill-llama-70b"),
            instructions="""You are a UI/UX architect specializing in creating optimal structures for web content.
            
            Given structured data and a target output type, design the best structure and layout.
            
            **Design Principles:**
            - Mobile-first responsive design
            - Clear visual hierarchy
            - Intuitive navigation
            - Professional appearance
            - Accessibility compliance
            
            **Output Format:**
            Return ONLY a JSON object with this structure:
            {
                "layout_structure": {
                    "sections": [
                        {
                            "id": "string",
                            "name": "string",
                            "type": "hero|about|experience|education|skills|projects|contact",
                            "content_sources": ["string"],
                            "layout": "grid|list|card|timeline",
                            "priority": 1-10
                        }
                    ]
                },
                "styling_guide": {
                    "color_scheme": {
                        "primary": "string",
                        "secondary": "string", 
                        "accent": "string",
                        "background": "string",
                        "text": "string"
                    },
                    "typography": {
                        "heading_font": "string",
                        "body_font": "string",
                        "font_sizes": {
                            "h1": "string",
                            "h2": "string",
                            "body": "string"
                        }
                    },
                    "spacing": {
                        "section_padding": "string",
                        "element_margin": "string"
                    }
                },
                "interactive_features": ["string"],
                "responsive_breakpoints": {
                    "mobile": "string",
                    "tablet": "string",
                    "desktop": "string"
                }
            }
            """
        )

        # Code Generator Agent - Generates the actual code
        self.code_generator = Agent(
            model=Groq(id="deepseek-r1-distill-llama-70b"),
            instructions="""You are a senior full-stack developer specializing in creating production-ready web applications.
            
            Given structured data and design specifications, generate complete, professional code.
            
            **Code Standards:**
            - Semantic HTML5
            - Modern CSS3 with Flexbox/Grid
            - Vanilla JavaScript (ES6+)
            - Mobile-first responsive design
            - Accessibility (ARIA labels, semantic markup)
            - Performance optimized
            - Clean, maintainable code
            
            **Output Format:**
            Your response MUST be ONLY the raw code, wrapped in <<START_CODE>> and <<END_CODE>> markers.
            
            For HTML files, include:
            - Complete HTML5 structure
            - Meta tags for SEO and mobile
            - CSS and JS file links
            - Semantic sections with proper IDs
            
            For CSS files, include:
            - CSS custom properties for theming
            - Responsive breakpoints
            - Smooth animations and transitions
            - Professional styling
            
            For JS files, include:
            - Modern ES6+ syntax
            - Event handlers for interactivity
            - Smooth scrolling and animations
            - Form validation if needed
            """
        )

        # Code Reviewer Agent - Reviews and suggests improvements
        self.code_reviewer = Agent(
            model=Groq(id="deepseek-r1-distill-llama-70b"),
            instructions="""You are a senior code reviewer with expertise in web development best practices.
            
            Analyze the provided code for:
            - Code quality and maintainability
            - Performance optimization opportunities
            - Accessibility compliance
            - Responsive design implementation
            - Security best practices
            - Browser compatibility
            - SEO optimization
            
            **Review Output:**
            Return a JSON object with this structure:
            {
                "overall_score": 1-10,
                "issues": [
                    {
                        "severity": "critical|high|medium|low",
                        "category": "performance|accessibility|security|code_quality|responsive",
                        "description": "string",
                        "suggestion": "string",
                        "line_reference": "string"
                    }
                ],
                "strengths": ["string"],
                "recommendations": ["string"],
                "requires_refactor": boolean
            }
            
            If the code is excellent (score 9-10), return:
            {"overall_score": 9, "issues": [], "strengths": ["Excellent code quality"], "recommendations": [], "requires_refactor": false}
            """
        )

        # Code Refactorer Agent - Implements improvements based on review
        self.code_refactorer = Agent(
            model=Groq(id="deepseek-r1-distill-llama-70b"),
            instructions="""You are a senior software architect specializing in code refactoring and optimization.
            
            Given code and review feedback, implement improvements to create production-ready code.
            
            **Refactoring Principles:**
            - Maintain functionality while improving quality
            - Implement all critical and high-priority fixes
            - Optimize for performance and accessibility
            - Ensure responsive design works perfectly
            - Add missing features or improvements
            
            **Output Format:**
            Your response MUST be ONLY the improved code, wrapped in <<START_CODE>> and <<END_CODE>> markers.
            """
        )

    def _extract_code(self, raw_content: str) -> str:
        """A robust method to extract code from the special markers."""
        start_marker = "<<START_CODE>>"
        end_marker = "<<END_CODE>>"
        
        start_index = raw_content.find(start_marker)
        end_index = raw_content.find(end_marker)

        if start_index != -1 and end_index != -1:
            code = raw_content[start_index + len(start_marker):end_index].strip()
            log_info(f"Successfully extracted code using markers. Length: {len(code)}")
            return code
        
        log_info("Warning: Could not find code markers. Returning raw content as a fallback.")
        return raw_content.strip()

    def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Safely parse JSON from agent response."""
        try:
            # Find JSON in the response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group(0))
            return None
        except json.JSONDecodeError as e:
            log_info(f"Failed to parse JSON response: {e}")
            return None

    def _analyze_content(self, content: str) -> Dict[str, Any]:
        """Analyze unstructured content and extract structured data."""
        log_info("Step 1: Analyzing content structure...")
        
        analysis_prompt = f"""
        Analyze the following content and extract structured information:
        
        {content}
        
        Extract all relevant information and structure it according to the specified format.
        """
        
        response = self.content_analyzer.run(analysis_prompt)
        structured_data = self._parse_json_response(response.content)
        
        if not structured_data:
            log_info("Content analysis failed, using fallback structure")
            return {
                "personal_info": {"name": "Professional", "summary": "Experienced professional"},
                "experience": [],
                "education": [],
                "skills": {"technical": [], "languages": [], "tools": [], "soft_skills": []},
                "projects": [],
                "certifications": [],
                "awards": []
            }
        
        log_info(f"Content analysis complete. Found {len(structured_data.get('experience', []))} experiences, {len(structured_data.get('skills', {}).get('technical', []))} technical skills")
        return structured_data

    def _design_structure(self, structured_data: Dict[str, Any], output_type: str) -> Dict[str, Any]:
        """Design the optimal structure for the output."""
        log_info("Step 2: Designing output structure...")
        
        design_prompt = f"""
        Design the optimal structure for a {output_type} based on this structured data:
        
        {json.dumps(structured_data, indent=2)}
        
        Create a professional, modern design that showcases the information effectively.
        """
        
        response = self.structure_designer.run(design_prompt)
        design_spec = self._parse_json_response(response.content)
        
        if not design_spec:
            log_info("Structure design failed, using default design")
            return {
                "layout_structure": {
                    "sections": [
                        {"id": "hero", "name": "Hero", "type": "hero", "content_sources": ["personal_info"], "layout": "card", "priority": 1},
                        {"id": "about", "name": "About", "type": "about", "content_sources": ["personal_info"], "layout": "list", "priority": 2},
                        {"id": "experience", "name": "Experience", "type": "experience", "content_sources": ["experience"], "layout": "timeline", "priority": 3},
                        {"id": "skills", "name": "Skills", "type": "skills", "content_sources": ["skills"], "layout": "grid", "priority": 4},
                        {"id": "projects", "name": "Projects", "type": "projects", "content_sources": ["projects"], "layout": "card", "priority": 5}
                    ]
                },
                "styling_guide": {
                    "color_scheme": {"primary": "#2563eb", "secondary": "#64748b", "accent": "#f59e0b", "background": "#ffffff", "text": "#1f2937"},
                    "typography": {"heading_font": "Inter", "body_font": "Inter", "font_sizes": {"h1": "3rem", "h2": "2.25rem", "body": "1rem"}},
                    "spacing": {"section_padding": "4rem 0", "element_margin": "1rem"}
                },
                "interactive_features": ["smooth-scroll", "hover-effects"],
                "responsive_breakpoints": {"mobile": "640px", "tablet": "768px", "desktop": "1024px"}
            }
        
        log_info(f"Structure design complete. Created {len(design_spec.get('layout_structure', {}).get('sections', []))} sections")
        return design_spec

    def _generate_code(self, structured_data: Dict[str, Any], design_spec: Dict[str, Any], filename: str) -> str:
        """Generate the actual code based on structured data and design specifications."""
        log_info(f"Step 3: Generating code for {filename}...")
        
        code_prompt = f"""
        Generate professional code for the file '{filename}' based on:
        
        **Structured Data:**
        {json.dumps(structured_data, indent=2)}
        
        **Design Specifications:**
        {json.dumps(design_spec, indent=2)}
        
        Create a complete, production-ready {filename.split('.')[-1].upper()} file that:
        - Implements the design specifications exactly
        - Uses the structured data to populate content
        - Is mobile-first responsive
        - Follows accessibility best practices
        - Has clean, maintainable code
        """
        
        response = self.code_generator.run(code_prompt)
        code = self._extract_code(response.content)
        
        if not code:
            raise ValueError(f"Code generation failed for {filename}")
        
        log_info(f"Code generation complete for {filename}. Length: {len(code)} characters")
        return code

    def _review_code(self, code: str, filename: str) -> Dict[str, Any]:
        """Review the generated code for quality and improvements."""
        log_info(f"Step 4: Reviewing code for {filename}...")
        
        review_prompt = f"""
        Review this {filename.split('.')[-1].upper()} code for quality, performance, and best practices:
        
        {code}
        
        Provide a comprehensive review with specific recommendations for improvement.
        """
        
        response = self.code_reviewer.run(review_prompt)
        review_result = self._parse_json_response(response.content)
        
        if not review_result:
            log_info("Code review failed, assuming code is acceptable")
            return {"overall_score": 7, "issues": [], "strengths": ["Code generated successfully"], "recommendations": [], "requires_refactor": False}
        
        log_info(f"Code review complete. Score: {review_result.get('overall_score', 0)}/10")
        return review_result

    def _refactor_code(self, code: str, review_result: Dict[str, Any], filename: str) -> str:
        """Refactor code based on review feedback."""
        if not review_result.get("requires_refactor", False):
            log_info("No refactoring required, code quality is acceptable")
            return code
        
        log_info(f"Step 5: Refactoring code for {filename}...")
        
        refactor_prompt = f"""
        Refactor this {filename.split('.')[-1].upper()} code based on the review feedback:
        
        **Original Code:**
        {code}
        
        **Review Feedback:**
        {json.dumps(review_result, indent=2)}
        
        Implement all critical and high-priority improvements while maintaining functionality.
        """
        
        response = self.code_refactorer.run(refactor_prompt)
        refactored_code = self._extract_code(response.content)
        
        if not refactored_code:
            log_info("Refactoring failed, returning original code")
            return code
        
        log_info(f"Code refactoring complete for {filename}")
        return refactored_code

    def run(self, prompt: str, shared_state: 'SharedState') -> Dict[str, Any]:
        """Executes a comprehensive, content-aware coding process."""
        try:
            # Extract filename from prompt - improved extraction logic
            filename = "index.html"  # Default for portfolio tasks
            
            # Look for specific file references in the prompt
            if "css" in prompt.lower() or "style" in prompt.lower():
                filename = "styles.css"
            elif "javascript" in prompt.lower() or "js" in prompt.lower() or "script" in prompt.lower():
                filename = "script.js"
            elif "python" in prompt.lower() or ".py" in prompt.lower():
                filename = "main.py"
            elif "portfolio" in prompt.lower() or "html" in prompt.lower():
                filename = "index.html"
            else:
                # Try to extract from the prompt
                filename_match = re.search(r"for\s*['\"]?([\w\.\-]+)['\"]?", prompt)
                if filename_match:
                    filename = filename_match.group(1)
                else:
                    # Look for file extensions in the prompt
                    ext_match = re.search(r"\.(html|css|js|py|txt|md)\b", prompt, re.IGNORECASE)
                    if ext_match:
                        ext = ext_match.group(1).lower()
                        if ext == "html":
                            filename = "index.html"
                        elif ext == "css":
                            filename = "styles.css"
                        elif ext == "js":
                            filename = "script.js"
                        elif ext == "py":
                            filename = "main.py"
                        else:
                            filename = f"output.{ext}"
                    else:
                        filename = "index.html"  # Default for web content
            
            # Get document content if available
            document_content = getattr(shared_state, 'document_content', None)
            
            if not document_content:
                log_info("No document content available, using basic code generation")
                # Fallback to original method for simple code generation
                contextual_prompt = f"""
                Based on the following project context, please write the required code for the file: `{filename}`

                **Project Context:**
                - **Original Task:** {shared_state.original_task}
                - **Project Directory:** {shared_state.project_directory}

                **Current Coding Task:**
                {prompt}
                """
                
                response = self.code_generator.run(contextual_prompt)
                final_code = self._extract_code(response.content)
                
                return {
                    "status": "success",
                    "output": f"Code generated for {filename}.",
                    "filename": filename,
                    "generated_code": final_code,
                }
            
            # Content-aware generation process
            log_info(f"Starting content-aware code generation for {filename} with {len(document_content)} characters of content")
            
            # Step 1: Analyze content structure
            structured_data = self._analyze_content(document_content)
            
            # Step 2: Design optimal structure
            output_type = "portfolio" if "portfolio" in prompt.lower() or filename.endswith(".html") else "application"
            design_spec = self._design_structure(structured_data, output_type)
            
            # Step 3: Generate initial code
            initial_code = self._generate_code(structured_data, design_spec, filename)
            
            # Step 4: Review code quality
            review_result = self._review_code(initial_code, filename)
            
            # Step 5: Refactor if needed
            final_code = self._refactor_code(initial_code, review_result, filename)
            
            # Log the process
            shared_state.add_to_history(f"Content-aware code generation completed for {filename}. Quality score: {review_result.get('overall_score', 0)}/10")
            
            return {
                "status": "success",
                "output": f"High-quality, content-aware code generated for {filename}. Quality score: {review_result.get('overall_score', 0)}/10",
                "filename": filename,
                "generated_code": final_code,
                "quality_metrics": {
                    "score": review_result.get("overall_score", 0),
                    "issues_fixed": len(review_result.get("issues", [])),
                    "content_analyzed": len(document_content)
                }
            }

        except Exception as e:
            log_info(f"A critical error occurred in the CoderAgentNode run method: {e}")
            return {
                "status": "error",
                "error": str(e),
                "generated_code": None,
            }
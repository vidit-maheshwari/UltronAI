# UltronAI 

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)]()

## 🚀 Overview

UltronAI is a sophisticated **General-Purpose Artificial General Intelligence (AGI) system** that leverages multiple specialized AI agents to execute complex tasks intelligently. Built with a modular, state-driven architecture, it can handle diverse tasks ranging from system health checks to portfolio creation, web development, data analysis, and more.

### Key Features

- **🤖 Multi-Agent Architecture**: 9 specialized agents working in coordination
- **🧠 AI-Powered Planning**: Intelligent task decomposition and execution planning
- **📊 Rich Terminal UI**: Beautiful, informative interface with progress tracking
- **🔄 State-Driven Execution**: Persistent state management across task execution
- **🛡️ Error Resilience**: Robust error handling and recovery mechanisms
- **📁 Document Processing**: PDF reading and content extraction capabilities
- **🌐 Web Research**: Comprehensive web search and synthesis capabilities
- **💻 Code Generation**: Advanced code generation with quality assessment

## 🏗️ Architecture

### Core Components

```
UltronAI/
├── main.py                 # Main entry point and orchestration
├── shared_state.py         # State management and persistence
├── requirements.txt        # Dependencies
├── Agents/                # Specialized agent modules
│   ├── planner_agent.py   # Task planning and decomposition
│   ├── coder_agent.py     # Code generation and refinement
│   ├── file_handler_agent.py # File operations and project structure
│   ├── shell_executer_agent.py # System operations and shell commands
│   ├── web_search.py      # Web research and synthesis
│   ├── error_resolver.py  # Error analysis and recovery
│   ├── document_reader_agent.py # PDF and document processing
│   ├── environment_check_agent.py # System dependency checking
│   ├── human_intervention_agent.py # User interaction handling
│   └── prompt_refiner.py  # Task refinement and optimization
└── projects/              # Generated project outputs
```

### Agent Specialization

| Agent | Primary Function | Capabilities |
|-------|-----------------|--------------|
| **Planner Agent** | Task decomposition and planning | Goal analysis, quality assessment, execution planning |
| **Coder Agent** | Code generation and refinement | Content analysis, structure design, code review |
| **File Handler Agent** | File operations and project structure | Project detection, backup protection, intelligent naming |
| **Shell Executer Agent** | System operations and shell commands | Platform-aware commands, system health checks |
| **Web Search Agent** | Web research and synthesis | Multi-source search, analysis, synthesis |
| **Error Resolver Agent** | Error analysis and recovery | Root cause analysis, fix strategy generation |
| **Document Reader Agent** | Document processing | PDF reading, content extraction |
| **Environment Check Agent** | System dependency verification | Tool availability checking |
| **Human Intervention Agent** | User interaction handling | Help requests, user guidance |

## 🛠️ Installation

### Prerequisites

- Python 3.8 or higher
- macOS, Linux, or Windows
- Internet connection for AI model access

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd UltronAI
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Run the system**
   ```bash
   python main.py
   ```

## 🎯 Usage Examples

### System Health Check
```bash
python main.py
# Enter: "check my system health and report the status through terminal"
```

### Portfolio Creation from Resume
```bash
python main.py
# Enter: "my resume is in desktop named 'resume.pdf', read it and make a portfolio page"
```

### Web Development
```bash
python main.py
# Enter: "create a responsive landing page for a tech startup"
```

### Data Analysis
```bash
python main.py
# Enter: "analyze sales data and create visualizations"
```

## 🔧 Technical Details

### State Management

The system uses a sophisticated state management approach through the `SharedState` class:

```python
class SharedState:
    def __init__(self, original_task: str):
        self.original_task: str = original_task
        self.current_plan: List[Dict[str, Any]] = []
        self.project_directory: Optional[Path] = None
        self.created_files: List[str] = []
        self.generated_code: Dict[str, str] = {}
        self.document_content: Optional[str] = None
        # ... additional state properties
```

### Agent Communication Protocol

Agents communicate through a standardized JSON format:

```json
{
    "agent": "agent_name",
    "description": "specific command or instruction"
}
```

### Execution Flow

1. **Task Input** → User provides task description
2. **Task Refinement** → Prompt refiner optimizes the task
3. **State Initialization** → SharedState created with task context
4. **Document Processing** → If documents mentioned, read and extract content
5. **Planning Phase** → Planner agent creates execution plan
6. **Execution Loop** → Agents execute tasks in sequence
7. **Quality Assessment** → Output quality evaluated
8. **Refinement** → If needed, code is refined and improved
9. **Completion** → Final output delivered

### Error Handling

The system implements multiple layers of error handling:

- **Pre-flight Checks**: Environment and dependency verification
- **Execution Monitoring**: Real-time error detection
- **Error Analysis**: Root cause identification
- **Recovery Strategies**: Automatic fix plan generation
- **Human Intervention**: User guidance when automatic recovery fails

## 🧠 AI Models and Capabilities

### Primary AI Model
- **Groq DeepSeek R1 Distill Llama 70B**: High-performance, fast inference model

### Agent Intelligence Features

#### Planner Agent
- **Goal Analysis**: Extracts ultimate goals and success criteria
- **Quality Assessment**: Evaluates output quality (1-10 scale)
- **Execution Planning**: Creates detailed step-by-step plans
- **Refinement Planning**: Generates improvement strategies

#### Coder Agent
- **Content Analysis**: Parses unstructured text into structured data
- **Structure Design**: Creates optimal layouts and designs
- **Code Generation**: Produces production-ready code
- **Code Review**: Self-assessment and improvement
- **Iterative Refinement**: Continuous quality improvement

#### File Handler Agent
- **Project Type Detection**: Automatically identifies project types
- **Intelligent Structure Creation**: Creates appropriate project structures
- **Backup Protection**: Prevents data loss through backup mechanisms
- **Content Awareness**: Reads and analyzes existing files

#### Web Search Agent
- **Multi-Source Search**: Performs comprehensive web searches
- **Source Evaluation**: Assesses credibility and relevance
- **Information Synthesis**: Creates actionable summaries
- **Analysis**: Provides detailed insights and recommendations

## 📊 Performance and Scalability

### Performance Metrics
- **Response Time**: Typically 30-60 seconds for complex tasks
- **Accuracy**: High-quality output with iterative refinement
- **Reliability**: Robust error handling and recovery
- **Scalability**: Modular architecture supports easy expansion

### Resource Usage
- **Memory**: Efficient state management with cleanup
- **CPU**: Optimized for multi-agent coordination
- **Network**: Minimal API calls with intelligent caching
- **Storage**: SQLite-based persistent storage

## 🔒 Security and Safety

### Security Features
- **Command Validation**: Prevents dangerous shell commands
- **File Protection**: Backup mechanisms prevent data loss
- **Input Sanitization**: Validates all user inputs
- **Error Isolation**: Errors don't propagate across agents

### Safety Measures
- **Timeout Protection**: Prevents infinite loops
- **Resource Limits**: Prevents excessive resource usage
- **Error Recovery**: Graceful degradation on failures
- **User Confirmation**: Critical operations require user approval

## 🧪 Testing and Quality Assurance

### Testing Strategy
- **Unit Tests**: Individual agent functionality
- **Integration Tests**: Multi-agent coordination
- **End-to-End Tests**: Complete task execution
- **Error Scenario Tests**: Error handling and recovery

### Quality Metrics
- **Code Quality**: Automated code review and scoring
- **Output Quality**: 1-10 scale assessment
- **User Satisfaction**: Feedback collection and analysis
- **Performance Monitoring**: Response time and resource usage

## 🚀 Advanced Features

### Content-Aware Processing
- **Document Reading**: PDF parsing and content extraction
- **Structured Data**: Intelligent parsing of unstructured content
- **Context Preservation**: Maintains context across operations
- **Content Integration**: Uses real content instead of placeholders

### Intelligent Planning
- **Goal-Oriented**: Focuses on ultimate objectives
- **Quality-Driven**: Prioritizes output quality
- **Adaptive**: Adjusts plans based on progress
- **Iterative**: Continuous improvement cycles

### Rich User Interface
- **Progress Tracking**: Real-time execution progress
- **Status Updates**: Detailed status information
- **Error Reporting**: Clear error messages and solutions
- **Output Display**: Beautiful formatting of results

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests for new functionality
5. Submit a pull request

### Code Standards
- **PEP 8**: Python code style guidelines
- **Type Hints**: Comprehensive type annotations
- **Documentation**: Detailed docstrings and comments
- **Error Handling**: Robust error management

### Testing Guidelines
- **Unit Tests**: Test individual functions and methods
- **Integration Tests**: Test agent interactions
- **End-to-End Tests**: Test complete workflows
- **Performance Tests**: Monitor resource usage

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Groq**: For providing high-performance AI inference
- **DeepSeek**: For the powerful language model
- **Rich**: For the beautiful terminal UI framework
- **Agno**: For the agent framework and utilities

## 📞 Support

For support, questions, or feature requests:

- **Issues**: Create an issue on GitHub
- **Discussions**: Use GitHub Discussions
- **Documentation**: Check the inline code documentation
- **Examples**: See the `projects/` directory for examples

---

**UltronAI Multi-Agent System** - Empowering intelligent task execution through coordinated AI agents. 🚀

---

**Created with ❤️ by Amit Anand**  
GitHub: [@amitanand983](https://github.com/amitanand983) 
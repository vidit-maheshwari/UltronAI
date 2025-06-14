# main.py - Fixed version with proper Windows path handling
from pathlib import Path
import sys
import os

# Add the current directory to Python path if needed
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Import all agent classes (make sure these files exist in the same directory)
from Agents.coder_agent import CoderAgentNode
from Agents.installer_agent import InstallerAgentNode  
from Agents.executer_agent import ExecutorAgentNode
from Agents.error_resolver import ErrorResolverAgentNode

class UniversalAgentOrchestrator:
    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path("./projects")
        self.base_dir.mkdir(exist_ok=True)
        
        print(f"🏁 Initializing agents with base directory: {self.base_dir}")
        
        # Initialize all agents
        try:
            self.coder = CoderAgentNode(base_dir=self.base_dir)
            print("✅ Coder agent initialized")
        except Exception as e:
            print(f"❌ Error initializing coder agent: {e}")
            
        try:
            self.installer = InstallerAgentNode()
            print("✅ Installer agent initialized")
        except Exception as e:
            print(f"❌ Error initializing installer agent: {e}")
            
        try:
            self.executor = ExecutorAgentNode(base_dir=self.base_dir)
            print("✅ Executor agent initialized")
        except Exception as e:
            print(f"❌ Error initializing executor agent: {e}")
            
        try:
            self.error_resolver = ErrorResolverAgentNode()
            print("✅ Error resolver agent initialized")
        except Exception as e:
            print(f"❌ Error initializing error resolver agent: {e}")
        
    # REPLACE the entire handle_request method with:
    def handle_request(self, request: str) -> str:
        """Main entry point for handling any coding request"""
        print(f"\n🎯 Processing request: {request}")
        
        try:
            # Step 1: Create code
            print("📝 Creating code...")
            self.coder.run(request)
            
            # Step 2: Install if needed
            if any(word in request.lower() for word in ['import', 'package', 'install', 'requirements']):
                print("📦 Installing packages...")
                self.installer.run(f"Install packages for: {request}")
            
            # Step 3: Execute
            print("🚀 Executing...")
            result = self.executor.run("Run the Python files in the directory")
            
            # Step 4: Handle errors if any
            if "❌" in str(result) or "Error" in str(result):
                print("🔧 Analyzing errors...")
                self.error_resolver.run(f"Analyze error: {result}")
            
            return "✅ Completed"
            
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def test_individual_agents(self):
        """Test each agent individually"""
        print("\n🧪 Testing individual agents...")
        print("="*40)
        
        # Test Coder Agent
        try:
            print("Testing Coder Agent...")
            result = self.coder.run("Create a simple hello world Python script")
            print("✅ Coder agent test passed")
        except Exception as e:
            print(f"❌ Coder agent test failed: {e}")
        
        # Test Installer Agent  
        try:
            print("\nTesting Installer Agent...")
            result = self.installer.run("Check if requests package is installed")
            print("✅ Installer agent test passed")
        except Exception as e:
            print(f"❌ Installer agent test failed: {e}")
            
        # Test Executor Agent
        try:
            print("\nTesting Executor Agent...")
            result = self.executor.run("Test syntax of any Python files in the directory")
            print("✅ Executor agent test passed")
        except Exception as e:
            print(f"❌ Executor agent test failed: {e}")
            
        # Test Error Resolver Agent
        try:
            print("\nTesting Error Resolver Agent...")
            result = self.error_resolver.run("Analyze this error: ModuleNotFoundError: No module named 'requests'")
            print("✅ Error resolver agent test passed")
        except Exception as e:
            print(f"❌ Error resolver agent test failed: {e}")


if __name__ == "__main__":
    # Method 1: Using raw string (recommended for Windows)
    base_path = Path(r"C:\Users\susmi\Documents\UltonAi\UltronAI-1\projects")
    
    # Method 2: Using forward slashes (also works on Windows)
    # base_path = Path("C:/Users/susmi/Documents/UltonAi/UltronAI-1/Agents/projects")
    
    # Method 3: Using pathlib to build path (most portable)
    # base_path = Path.home() / "Documents" / "UltonAi" / "UltronAI-1" / "Agents" / "projects"
    
    # Method 4: Using current directory (simplest)
    # base_path = Path("./projects")
    
    print(f"🚀 Starting Universal Agent System")
    print(f"📁 Base directory: {base_path}")
    
    try:
        # Initialize the universal agent system
        universal_agent = UniversalAgentOrchestrator(base_dir=base_path)
        
        # Test individual agents first
        universal_agent.test_individual_agents()
        
        print("\n" + "="*60)
        print("🎮 Ready for requests! Choose an option:")
        print("1. Simple calculator")
        print("2. Web scraper") 
        print("3. REST API")
        print("4. Custom request")
        print("5. Exit")
        
        while True:
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == "1":
                result = universal_agent.handle_request("Create a simple calculator with basic math operations")
            elif choice == "2":
                result = universal_agent.handle_request("Create a web scraper that can extract titles from websites")
            elif choice == "3":
                result = universal_agent.handle_request("Create a simple REST API using Flask for managing tasks")
            elif choice == "4":
                custom_request = input("Enter your custom request: ").strip()
                if custom_request:
                    result = universal_agent.handle_request(custom_request)
                else:
                    print("❌ Empty request")
                    continue
            elif choice == "5":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-5.")
                continue
                
            print(f"\n🏁 Final Result: {result}")
            print("\n" + "="*60)
            
    except Exception as e:
        print(f"💥 Critical error starting the system: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure all agent files exist in the same directory")
        print("2. Check that your .env file has the GROQ_API_KEY")
        print("3. Verify all required packages are installed")
        print("4. Try using a simpler path like Path('./projects')")
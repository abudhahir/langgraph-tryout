"""
Configuration for the CodeInsight Agent.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from langchain.schema.language_model import BaseLanguageModel

@dataclass
class AgentConfig:
    """Configuration for the CodeInsight Agent."""
    
    # Repository information
    repo_url: str
    
    # Output directory
    output_dir: str
    
    # Model configuration
    model_name: str = "gpt-4-turbo"
    llm: Optional[BaseLanguageModel] = None
    
    # Task to perform
    task: str = "all"
    
    # Agent-specific configurations
    agent_configs: Dict[str, Any] = field(default_factory=dict)
    
    # Default chunk size for code indexing
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # Maximum files to process
    max_files: int = 100
    
    # File extensions to include/exclude
    include_extensions: list = field(default_factory=lambda: [
        ".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".hpp",
        ".cs", ".go", ".rb", ".php", ".swift", ".kt", ".rs",
        ".html", ".css", ".jsx", ".tsx", ".vue", ".md", ".json",
        ".yml", ".yaml", ".toml", ".ini", ".sql"
    ])
    
    exclude_directories: list = field(default_factory=lambda: [
        "node_modules", "venv", ".git", "__pycache__", ".idea", ".vscode",
        "build", "dist", "target", "bin", "obj", ".pytest_cache"
    ])
    
    def __post_init__(self):
        """Initialize default agent configs if not provided."""
        default_configs = {
            "repo_manager": {
                "timeout": 300,
                "cleanup": True
            },
            "code_understanding": {
                "max_files_to_analyze": 50,
                "priority_files": ["README.md", "main.py", "index.js", "package.json"]
            },
            "qa": {
                "default_questions": [
                    "What is the main purpose of this codebase?",
                    "What are the key dependencies?",
                    "What is the architecture of the application?",
                    "What are the entry points to the application?",
                    "How is the code organized?"
                ]
            },
            "report": {
                "sections": ["Overview", "Architecture", "Key Components", "Dependencies", "Code Quality"]
            },
            "documentation": {
                "generate_readme": True,
                "generate_api_docs": True
            },
            "refactoring": {
                "max_suggestions": 10
            }
        }
        
        # Update with user-provided configs
        for key, value in default_configs.items():
            if key not in self.agent_configs:
                self.agent_configs[key] = value
            else:
                self.agent_configs[key].update({
                    k: v for k, v in default_configs[key].items()
                    if k not in self.agent_configs[key]
                })

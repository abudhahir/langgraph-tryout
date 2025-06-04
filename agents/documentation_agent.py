"""
Documentation Generation Agent for CodeInsight.

This agent is responsible for:
1. Generating documentation for the codebase
2. Creating README files, API documentation, and usage guides
3. Documenting code structure and organization
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

from langchain.schema import HumanMessage
from llama_index.core import VectorStoreIndex

from utils.config import AgentConfig


class DocumentationAgent:
    """Agent for generating documentation for the codebase."""
    
    def __init__(self, config: AgentConfig):
        """Initialize the DocumentationAgent.
        
        Args:
            config: Configuration for the agent
        """
        self.config = config
        
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the documentation generation agent.
        
        Args:
            state: Current state of the workflow
            
        Returns:
            Updated state
        """
        try:
            if "understanding" not in state or not state["understanding"]:
                state["errors"].append("Code understanding must be completed before generating documentation")
                return state
            
            # Initialize documentation dictionary
            state["documentation"] = {}
            
            # Generate README if configured
            if self.config.agent_configs["documentation"]["generate_readme"]:
                readme = self.generate_readme(state)
                state["documentation"]["readme"] = readme
                self.save_documentation(state, "README.md", readme)
            
            # Generate API documentation if configured
            if self.config.agent_configs["documentation"]["generate_api_docs"]:
                api_docs = self.generate_api_docs(state)
                state["documentation"]["api_docs"] = api_docs
                
                # Save API docs as individual files
                for component, content in api_docs.items():
                    filename = f"api_{component.lower().replace(' ', '_')}.md"
                    self.save_documentation(state, f"api/{filename}", content)
            
            # Generate usage guides
            usage_guide = self.generate_usage_guide(state)
            state["documentation"]["usage_guide"] = usage_guide
            self.save_documentation(state, "usage_guide.md", usage_guide)
            
            # Update status
            state["status"] = "documentation_complete"
            
        except Exception as e:
            state["errors"].append(f"Documentation generation error: {str(e)}")
            state["status"] = "error"
            
        return state
    
    def generate_readme(self, state: Dict[str, Any]) -> str:
        """Generate a README file for the codebase.
        
        Args:
            state: Current state of the workflow
            
        Returns:
            Markdown README content
        """
        # Extract repo name
        repo_name = os.path.basename(state["repo_url"].rstrip("/").split("/")[-1])
        
        # Build README content
        sections = []
        
        # Title and introduction
        sections.append(f"# {repo_name}\n")
        
        # Try to extract project description from understanding
        description = "A software project."
        if "answers" in state and state["answers"]:
            for question, answer in state["answers"].items():
                if "purpose" in question.lower() or "what is" in question.lower():
                    description = answer["text"].split(".")[0] + "."  # First sentence
                    break
        
        sections.append(f"{description}\n")
        
        # Table of Contents
        sections.append("## Table of Contents\n")
        sections.append("- [Overview](#overview)")
        sections.append("- [Installation](#installation)")
        sections.append("- [Usage](#usage)")
        sections.append("- [Architecture](#architecture)")
        sections.append("- [API Documentation](#api-documentation)")
        sections.append("- [Contributing](#contributing)")
        sections.append("- [License](#license)\n")
        
        # Overview
        sections.append("## Overview\n")
        if "understanding" in state and "architecture" in state["understanding"]:
            # Extract a summary from the architecture analysis
            arch_text = state["understanding"]["architecture"]["analysis"]
            # Keep it concise for the README
            overview = " ".join(arch_text.split()[:100]) + "..."
            sections.append(f"{overview}\n")
        else:
            sections.append("This project provides...\n")
        
        # Installation
        sections.append("## Installation\n")
        sections.append("```bash")
        sections.append(f"git clone {state['repo_url']}")
        sections.append(f"cd {repo_name}")
        
        # Try to determine the installation method based on file types
        if any(f.endswith("requirements.txt") for f in state["file_list"]):
            sections.append("pip install -r requirements.txt")
        elif any(f.endswith("setup.py") for f in state["file_list"]):
            sections.append("pip install .")
        elif any(f.endswith("package.json") for f in state["file_list"]):
            sections.append("npm install")
        
        sections.append("```\n")
        
        # Usage
        sections.append("## Usage\n")
        sections.append("Basic usage instructions:\n")
        
        # Try to determine usage examples based on file types
        main_files = [f for f in state["file_list"] if os.path.basename(f) in ["main.py", "index.js", "app.py", "server.js"]]
        if main_files:
            main_file = main_files[0]
            if main_file.endswith(".py"):
                sections.append("```python")
                sections.append(f"python {main_file}")
                sections.append("```")
            elif main_file.endswith(".js"):
                sections.append("```javascript")
                sections.append(f"node {main_file}")
                sections.append("```")
        else:
            sections.append("Please refer to the documentation for detailed usage examples.\n")
        
        # Architecture
        sections.append("## Architecture\n")
        if "understanding" in state and "components" in state["understanding"]:
            sections.append("The codebase is organized into the following components:\n")
            components_text = state["understanding"]["components"]["list"]
            # Extract component names if possible
            try:
                # This assumes components is a JSON string
                components_data = json.loads(components_text)
                for component in components_data:
                    if isinstance(component, dict) and "name" in component:
                        sections.append(f"- **{component['name']}**: {component.get('purpose', '')}")
            except (json.JSONDecodeError, TypeError):
                # Fallback to using the raw text
                sections.append(components_text)
        else:
            sections.append("The project architecture consists of multiple interconnected components.\n")
        
        # API Documentation
        sections.append("## API Documentation\n")
        sections.append("For detailed API documentation, please refer to the `docs/api` directory.\n")
        
        # Contributing
        sections.append("## Contributing\n")
        sections.append("Contributions are welcome! Please feel free to submit a Pull Request.\n")
        
        # License
        sections.append("## License\n")
        sections.append("Please see the LICENSE file for details.\n")
        
        return "\n".join(sections)
    
    def generate_api_docs(self, state: Dict[str, Any]) -> Dict[str, str]:
        """Generate API documentation for the codebase.
        
        Args:
            state: Current state of the workflow
            
        Returns:
            Dictionary mapping component names to documentation content
        """
        api_docs = {}
        
        # Try to extract components from the understanding
        if "understanding" in state and "components" in state["understanding"]:
            components_text = state["understanding"]["components"]["list"]
            
            try:
                # This assumes components is a JSON string
                components_data = json.loads(components_text)
                
                for component in components_data:
                    if isinstance(component, dict) and "name" in component:
                        component_name = component["name"]
                        component_docs = self._generate_component_docs(state, component)
                        api_docs[component_name] = component_docs
            except (json.JSONDecodeError, TypeError):
                # Fallback to generating a single API doc
                api_docs["API Reference"] = self._generate_fallback_api_docs(state)
        else:
            # Fallback to generating a single API doc
            api_docs["API Reference"] = self._generate_fallback_api_docs(state)
        
        return api_docs
    
    def _generate_component_docs(self, state: Dict[str, Any], component: Dict[str, Any]) -> str:
        """Generate documentation for a specific component.
        
        Args:
            state: Current state of the workflow
            component: Component information
            
        Returns:
            Markdown documentation for the component
        """
        sections = []
        
        # Title and introduction
        sections.append(f"# {component['name']} API Documentation\n")
        
        # Purpose
        if "purpose" in component:
            sections.append("## Purpose\n")
            sections.append(f"{component['purpose']}\n")
        
        # Location
        if "location" in component:
            sections.append("## Location\n")
            sections.append(f"This component is located at: `{component['location']}`\n")
        
        # Dependencies
        if "dependencies" in component:
            sections.append("## Dependencies\n")
            if isinstance(component["dependencies"], list):
                for dep in component["dependencies"]:
                    sections.append(f"- {dep}")
            else:
                sections.append(component["dependencies"])
            sections.append("")
        
        # Functionality
        if "key_functionality" in component:
            sections.append("## Key Functionality\n")
            sections.append(f"{component['key_functionality']}\n")
        
        # API Reference
        sections.append("## API Reference\n")
        
        # Try to generate API reference based on the component location
        if "location" in component and component["location"] in state["files_content"]:
            # Extract functions and classes from the file content
            file_content = state["files_content"][component["location"]]
            
            # This is a very simplified approach - in a real implementation,
            # you would use a proper code parser to extract API details
            
            # Look for function definitions
            sections.append("### Functions\n")
            functions_found = False
            
            for line in file_content.split("\n"):
                if line.strip().startswith("def "):
                    functions_found = True
                    # Extract function name and args
                    func_def = line.strip()[4:].split("(", 1)
                    func_name = func_def[0].strip()
                    func_args = "(" + func_def[1].strip() if len(func_def) > 1 else "()"
                    
                    sections.append(f"#### `{func_name}{func_args}`\n")
                    sections.append("Description: *Function description*\n")
            
            if not functions_found:
                sections.append("No functions found in this component.\n")
            
            # Look for class definitions
            sections.append("### Classes\n")
            classes_found = False
            
            for line in file_content.split("\n"):
                if line.strip().startswith("class "):
                    classes_found = True
                    # Extract class name
                    class_def = line.strip()[6:].split("(", 1)
                    class_name = class_def[0].strip()
                    class_parent = "(" + class_def[1].strip() if len(class_def) > 1 else ""
                    
                    sections.append(f"#### `{class_name}{class_parent}`\n")
                    sections.append("Description: *Class description*\n")
            
            if not classes_found:
                sections.append("No classes found in this component.\n")
        else:
            sections.append("Detailed API reference information is not available for this component.\n")
        
        # Usage Examples
        sections.append("## Usage Examples\n")
        sections.append("```python")
        sections.append(f"# Example usage of {component['name']}")
        sections.append("# ...")
        sections.append("```\n")
        
        return "\n".join(sections)
    
    def _generate_fallback_api_docs(self, state: Dict[str, Any]) -> str:
        """Generate a fallback API documentation when structured component info is not available.
        
        Args:
            state: Current state of the workflow
            
        Returns:
            Markdown API documentation
        """
        repo_name = os.path.basename(state["repo_url"].rstrip("/").split("/")[-1])
        
        sections = []
        
        # Title and introduction
        sections.append(f"# {repo_name} API Documentation\n")
        sections.append("This document provides an overview of the API for this codebase.\n")
        
        # Find key files
        python_files = [f for f in state["file_list"] if f.endswith(".py")]
        js_files = [f for f in state["file_list"] if f.endswith(".js") or f.endswith(".ts")]
        
        # Document Python files
        if python_files:
            sections.append("## Python Modules\n")
            
            for file_path in sorted(python_files)[:10]:  # Limit to 10 files for brevity
                file_name = os.path.basename(file_path)
                sections.append(f"### {file_name}\n")
                
                if file_path in state["files_content"]:
                    file_content = state["files_content"][file_path]
                    
                    # Extract docstring if available
                    if '"""' in file_content or "'''" in file_content:
                        docstring_start = file_content.find('"""') if '"""' in file_content else file_content.find("'''")
                        if docstring_start >= 0:
                            docstring_end = file_content.find('"""', docstring_start + 3) if '"""' in file_content else file_content.find("'''", docstring_start + 3)
                            if docstring_end >= 0:
                                docstring = file_content[docstring_start + 3:docstring_end].strip()
                                sections.append(f"{docstring}\n")
                    
                    # Look for functions and classes
                    functions = []
                    classes = []
                    
                    for line in file_content.split("\n"):
                        if line.strip().startswith("def "):
                            functions.append(line.strip())
                        elif line.strip().startswith("class "):
                            classes.append(line.strip())
                    
                    if functions:
                        sections.append("**Functions:**\n")
                        for func in functions:
                            sections.append(f"- `{func}`")
                        sections.append("")
                    
                    if classes:
                        sections.append("**Classes:**\n")
                        for cls in classes:
                            sections.append(f"- `{cls}`")
                        sections.append("")
        
        # Document JavaScript/TypeScript files
        if js_files:
            sections.append("## JavaScript/TypeScript Modules\n")
            
            for file_path in sorted(js_files)[:10]:  # Limit to 10 files for brevity
                file_name = os.path.basename(file_path)
                sections.append(f"### {file_name}\n")
                
                if file_path in state["files_content"]:
                    file_content = state["files_content"][file_path]
                    
                    # Extract exports and functions
                    exports = []
                    functions = []
                    
                    for line in file_content.split("\n"):
                        line = line.strip()
                        if line.startswith("export "):
                            exports.append(line)
                        elif line.startswith("function ") or "=> {" in line:
                            functions.append(line)
                    
                    if exports:
                        sections.append("**Exports:**\n")
                        for exp in exports:
                            sections.append(f"- `{exp}`")
                        sections.append("")
                    
                    if functions:
                        sections.append("**Functions:**\n")
                        for func in functions:
                            sections.append(f"- `{func}`")
                        sections.append("")
        
        # Add usage examples section
        sections.append("## Usage Examples\n")
        sections.append("Below are examples of how to use key components of the API.\n")
        sections.append("```python")
        sections.append("# Python example")
        sections.append("# ...")
        sections.append("```\n")
        
        if js_files:
            sections.append("```javascript")
            sections.append("// JavaScript example")
            sections.append("// ...")
            sections.append("```\n")
        
        return "\n".join(sections)
    
    def generate_usage_guide(self, state: Dict[str, Any]) -> str:
        """Generate a usage guide for the codebase.
        
        Args:
            state: Current state of the workflow
            
        Returns:
            Markdown usage guide
        """
        repo_name = os.path.basename(state["repo_url"].rstrip("/").split("/")[-1])
        
        sections = []
        
        # Title and introduction
        sections.append(f"# {repo_name} Usage Guide\n")
        sections.append("This guide provides instructions on how to use this software effectively.\n")
        
        # Table of Contents
        sections.append("## Table of Contents\n")
        sections.append("- [Installation](#installation)")
        sections.append("- [Configuration](#configuration)")
        sections.append("- [Basic Usage](#basic-usage)")
        sections.append("- [Advanced Features](#advanced-features)")
        sections.append("- [Troubleshooting](#troubleshooting)\n")
        
        # Installation
        sections.append("## Installation\n")
        sections.append("### Prerequisites\n")
        sections.append("Before installing this software, ensure you have the following prerequisites:\n")
        
        # Try to determine prerequisites based on file types
        if any(f.endswith("requirements.txt") for f in state["file_list"]):
            sections.append("- Python 3.7 or higher")
            sections.append("- pip (Python package manager)")
        elif any(f.endswith("package.json") for f in state["file_list"]):
            sections.append("- Node.js 14 or higher")
            sections.append("- npm or yarn")
        
        sections.append("\n### Installation Steps\n")
        sections.append("```bash")
        sections.append(f"git clone {state['repo_url']}")
        sections.append(f"cd {repo_name}")
        
        # Try to determine the installation method based on file types
        if any(f.endswith("requirements.txt") for f in state["file_list"]):
            sections.append("pip install -r requirements.txt")
        elif any(f.endswith("setup.py") for f in state["file_list"]):
            sections.append("pip install .")
        elif any(f.endswith("package.json") for f in state["file_list"]):
            sections.append("npm install")
        
        sections.append("```\n")
        
        # Configuration
        sections.append("## Configuration\n")
        
        # Look for configuration files
        config_files = [
            f for f in state["file_list"] 
            if os.path.basename(f) in [
                "config.py", "settings.py", "config.json", ".env.example",
                "config.js", "config.yml", "config.yaml"
            ]
        ]
        
        if config_files:
            sections.append("The software can be configured using the following configuration files:\n")
            for config_file in config_files:
                sections.append(f"- `{config_file}`")
            
            sections.append("\nExample configuration:\n")
            
            # Try to show a sample from one of the config files
            for config_file in config_files:
                if config_file in state["files_content"]:
                    file_content = state["files_content"][config_file]
                    ext = os.path.splitext(config_file)[1]
                    
                    sections.append(f"```{ext[1:] if ext else ''}")
                    # Show first 10 lines or less
                    content_lines = file_content.split("\n")[:10]
                    sections.append("\n".join(content_lines))
                    if len(file_content.split("\n")) > 10:
                        sections.append("# ... more configuration options ...")
                    sections.append("```")
                    break
        else:
            sections.append("This software does not require specific configuration files.\n")
        
        # Basic Usage
        sections.append("## Basic Usage\n")
        
        # Try to determine usage examples based on file types
        main_files = [f for f in state["file_list"] if os.path.basename(f) in ["main.py", "index.js", "app.py", "server.js"]]
        if main_files:
            main_file = main_files[0]
            if main_file.endswith(".py"):
                sections.append("```python")
                sections.append(f"python {main_file}")
                sections.append("```")
            elif main_file.endswith(".js"):
                sections.append("```javascript")
                sections.append(f"node {main_file}")
                sections.append("```")
            
            sections.append("\nHere are some common usage patterns:\n")
            sections.append("1. **Basic operation**: [Description of basic operation]")
            sections.append("2. **Common task**: [Description of common task]")
            sections.append("3. **Typical workflow**: [Description of typical workflow]\n")
        else:
            sections.append("Basic usage information will vary depending on your specific needs.\n")
        
        # Advanced Features
        sections.append("## Advanced Features\n")
        sections.append("This software includes several advanced features for power users:\n")
        sections.append("1. **Feature 1**: [Description of advanced feature 1]")
        sections.append("2. **Feature 2**: [Description of advanced feature 2]")
        sections.append("3. **Feature 3**: [Description of advanced feature 3]\n")
        
        # Troubleshooting
        sections.append("## Troubleshooting\n")
        sections.append("### Common Issues\n")
        sections.append("Here are solutions to common issues you might encounter:\n")
        sections.append("1. **Problem**: [Description of common problem 1]")
        sections.append("   **Solution**: [Solution to problem 1]\n")
        sections.append("2. **Problem**: [Description of common problem 2]")
        sections.append("   **Solution**: [Solution to problem 2]\n")
        
        sections.append("### Getting Help\n")
        sections.append("If you encounter issues not covered in this guide, please:")
        sections.append("- Check the documentation")
        sections.append("- Look for similar issues in the project's issue tracker")
        sections.append("- Open a new issue if needed\n")
        
        return "\n".join(sections)
    
    def save_documentation(self, state: Dict[str, Any], filename: str, content: str) -> None:
        """Save documentation to a file.
        
        Args:
            state: Current state of the workflow
            filename: Name of the file to save
            content: Content to save
        """
        output_dir = Path(state["output_dir"]) / "documentation"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Handle subdirectories in the filename
        file_path = output_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

"""
Code Understanding Agent for CodeInsight.

This agent is responsible for:
1. Analyzing the codebase structure
2. Identifying key components and relationships
3. Creating a knowledge graph of the code
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional

from langchain.schema import HumanMessage
from llama_index.core import VectorStoreIndex
from llama_index.core import Response

from utils.config import AgentConfig


class CodeUnderstandingAgent:
    """Agent for understanding codebases."""
    
    def __init__(self, config: AgentConfig):
        """Initialize the CodeUnderstandingAgent.
        
        Args:
            config: Configuration for the agent
        """
        self.config = config
        
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the code understanding agent.
        
        Args:
            state: Current state of the workflow
            
        Returns:
            Updated state
        """
        try:
            if state["status"] != "repo_cloned" or not state["code_index"]:
                state["errors"].append("Repository must be cloned and indexed before code understanding")
                return state
            
            # Get file content for priority files first
            self.load_priority_files(state)
            
            # Analyze the codebase structure
            architecture = self.analyze_architecture(state)
            state["understanding"]["architecture"] = architecture
            
            # Identify key components
            components = self.identify_components(state)
            state["understanding"]["components"] = components
            
            # Extract dependencies
            dependencies = self.extract_dependencies(state)
            state["understanding"]["dependencies"] = dependencies
            
            # Analyze code quality
            code_quality = self.analyze_code_quality(state)
            state["understanding"]["code_quality"] = code_quality
            
            # Update status
            state["status"] = "understanding_complete"
            
        except Exception as e:
            state["errors"].append(f"Code understanding error: {str(e)}")
            state["status"] = "error"
            
        return state
    
    def load_priority_files(self, state: Dict[str, Any]) -> None:
        """Load content of priority files into the state.
        
        Args:
            state: Current state of the workflow
        """
        priority_files = self.config.agent_configs["code_understanding"]["priority_files"]
        repo_path = Path(state["repo_path"])
        files_content = state.get("files_content", {})
        
        # Find priority files in the repository
        for file_pattern in priority_files:
            for file_path in state["file_list"]:
                if file_path.endswith(file_pattern) or os.path.basename(file_path) == file_pattern:
                    try:
                        with open(repo_path / file_path, 'r', encoding='utf-8') as f:
                            files_content[file_path] = f.read()
                    except Exception as e:
                        # Skip files that can't be read
                        continue
        
        # Load some additional files if needed
        max_files = self.config.agent_configs["code_understanding"]["max_files_to_analyze"]
        if len(files_content) < max_files:
            for file_path in state["file_list"]:
                if file_path not in files_content and len(files_content) < max_files:
                    try:
                        with open(repo_path / file_path, 'r', encoding='utf-8') as f:
                            files_content[file_path] = f.read()
                    except Exception as e:
                        # Skip files that can't be read
                        continue
        
        state["files_content"] = files_content
    
    def analyze_architecture(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the codebase architecture.
        
        Args:
            state: Current state of the workflow
            
        Returns:
            Architecture analysis
        """
        # Use the LLM to analyze the codebase architecture
        query = """
        Analyze the overall architecture of this codebase. 
        Consider:
        1. What architectural patterns are used?
        2. How is the code organized?
        3. What are the main modules and their responsibilities?
        4. How do the components interact with each other?
        
        Format your response as a JSON with the following keys:
        - patterns: List of architectural patterns identified
        - structure: Description of the code organization
        - modules: Dictionary of main modules and their responsibilities
        - interactions: Description of how components interact
        """
        
        response = self._query_llm(state, query)
        
        # Parse response
        try:
            # For simplicity, we'll use the response as-is
            # In a real implementation, you'd parse the JSON response
            architecture = {
                "analysis": response.response,
                "confidence": response.metadata.get("confidence", 0.8)
            }
        except Exception as e:
            architecture = {
                "analysis": "Failed to parse architecture analysis",
                "error": str(e)
            }
        
        return architecture
    
    def identify_components(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Identify key components in the codebase.
        
        Args:
            state: Current state of the workflow
            
        Returns:
            Key components
        """
        query = """
        Identify the key components in this codebase.
        For each component, provide:
        1. Name
        2. Purpose
        3. Location (file path)
        4. Dependencies on other components
        5. Key functionality
        
        Focus on the most important components that are essential to understanding the codebase.
        Format your response as a JSON list of component objects.
        """
        
        response = self._query_llm(state, query)
        
        # Parse response
        components = {
            "list": response.response,
            "count": response.metadata.get("component_count", 0)
        }
        
        return components
    
    def extract_dependencies(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract dependencies from the codebase.
        
        Args:
            state: Current state of the workflow
            
        Returns:
            Dependencies
        """
        query = """
        Extract the dependencies of this codebase.
        Consider:
        1. External libraries and frameworks used
        2. Third-party services integrated
        3. Key internal dependencies between components
        
        Format your response as a JSON with the following keys:
        - external: List of external dependencies with versions if available
        - services: List of third-party services used
        - internal: Dictionary of internal component dependencies
        """
        
        response = self._query_llm(state, query)
        
        # Parse response
        dependencies = {
            "analysis": response.response,
            "timestamp": response.metadata.get("timestamp")
        }
        
        return dependencies
    
    def analyze_code_quality(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the code quality.
        
        Args:
            state: Current state of the workflow
            
        Returns:
            Code quality analysis
        """
        query = """
        Analyze the code quality of this codebase.
        Consider:
        1. Code organization and cleanliness
        2. Documentation quality
        3. Test coverage
        4. Maintainability
        5. Potential issues or technical debt
        
        Format your response as a JSON with the following keys:
        - overall_score: Numerical score from 1-10
        - strengths: List of strengths in the codebase
        - weaknesses: List of weaknesses or areas for improvement
        - recommendations: List of recommendations to improve code quality
        """
        
        response = self._query_llm(state, query)
        
        # Parse response
        code_quality = {
            "analysis": response.response,
            "confidence": response.metadata.get("confidence", 0.7)
        }
        
        return code_quality
    
    def _query_llm(self, state: Dict[str, Any], query: str) -> Response:
        """Query the LLM using the codebase index.
        
        Args:
            state: Current state of the workflow
            query: Query to send to the LLM
            
        Returns:
            Response from the LLM
        """
        # Get the index from the state
        index = state["code_index"]
        
        # Create query engine
        query_engine = index.as_query_engine()
        
        # Execute query
        response = query_engine.query(query)
        
        return response

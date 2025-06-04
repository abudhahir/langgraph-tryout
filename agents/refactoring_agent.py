"""
Refactoring Agent for CodeInsight.

This agent is responsible for:
1. Analyzing the code for potential improvements
2. Suggesting refactoring opportunities
3. Providing actionable recommendations for code quality
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

from langchain.schema import HumanMessage
from llama_index.core import VectorStoreIndex

from utils.config import AgentConfig


class RefactoringAgent:
    """Agent for suggesting code refactoring and improvements."""
    
    def __init__(self, config: AgentConfig):
        """Initialize the RefactoringAgent.
        
        Args:
            config: Configuration for the agent
        """
        self.config = config
        
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the refactoring agent.
        
        Args:
            state: Current state of the workflow
            
        Returns:
            Updated state
        """
        try:
            if "understanding" not in state or not state["understanding"]:
                state["errors"].append("Code understanding must be completed before suggesting refactoring")
                return state
            
            # Generate refactoring suggestions
            suggestions = self.generate_refactoring_suggestions(state)
            state["refactoring_suggestions"] = suggestions
            
            # Save suggestions to file
            self.save_suggestions(state)
            
            # Update status
            state["status"] = "refactoring_complete"
            
        except Exception as e:
            state["errors"].append(f"Refactoring suggestion error: {str(e)}")
            state["status"] = "error"
            
        return state
    
    def generate_refactoring_suggestions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate refactoring suggestions for the codebase.
        
        Args:
            state: Current state of the workflow
            
        Returns:
            List of refactoring suggestions
        """
        suggestions = []
        
        # Use the index to find code smells and refactoring opportunities
        index = state["code_index"]
        query_engine = index.as_query_engine(similarity_top_k=10)
        
        # Define queries for different types of refactoring opportunities
        refactoring_queries = [
            "Identify code duplication and suggest ways to reduce redundancy in this codebase",
            "Find complex methods or functions that should be simplified or broken down",
            "Identify performance bottlenecks or inefficient code patterns",
            "Suggest improvements to the code architecture or organization",
            "Find potential bugs or error-prone patterns in the code",
            "Identify violations of coding standards or best practices",
            "Suggest improvements to error handling and logging",
            "Identify opportunities to improve test coverage or testing approach"
        ]
        
        # Limit the number of suggestions based on configuration
        max_suggestions = self.config.agent_configs["refactoring"]["max_suggestions"]
        
        # Process queries to generate suggestions
        for query in refactoring_queries:
            response = query_engine.query(query)
            
            # Extract suggestions from the response
            suggestion = {
                "category": query.split("and")[0].replace("Identify", "").replace("Find", "").strip(),
                "description": response.response,
                "confidence": response.metadata.get("confidence", 0.7) if hasattr(response, "metadata") else 0.7,
                "sources": []
            }
            
            # Extract source information if available
            if hasattr(response, "source_nodes"):
                for node in response.source_nodes:
                    if hasattr(node, "metadata") and "file_path" in node.metadata:
                        source = {
                            "file_path": node.metadata["file_path"],
                            "score": node.score if hasattr(node, "score") else None,
                        }
                        suggestion["sources"].append(source)
            
            suggestions.append(suggestion)
            
            # Check if we've reached the maximum number of suggestions
            if len(suggestions) >= max_suggestions:
                break
        
        return suggestions
    
    def save_suggestions(self, state: Dict[str, Any]) -> None:
        """Save refactoring suggestions to a file.
        
        Args:
            state: Current state of the workflow
        """
        output_dir = Path(state["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        suggestions_path = output_dir / "refactoring.md"
        
        # Format suggestions as Markdown
        content = ["# Refactoring Suggestions\n"]
        content.append("This document contains suggestions for improving the codebase.\n")
        
        for i, suggestion in enumerate(state["refactoring_suggestions"], 1):
            content.append(f"## {i}. {suggestion['category']}\n")
            content.append(f"{suggestion['description']}\n")
            
            if suggestion.get("sources"):
                content.append("**Affected files:**\n")
                for source in suggestion["sources"]:
                    content.append(f"- `{source['file_path']}`")
                content.append("")
        
        # Add implementation guidance
        content.append("## Implementation Guidance\n")
        content.append("When implementing these refactoring suggestions, consider the following steps:\n")
        content.append("1. **Prioritize**: Focus on changes that provide the most value with the least risk")
        content.append("2. **Test**: Ensure adequate test coverage before making changes")
        content.append("3. **Incremental**: Make changes incrementally rather than all at once")
        content.append("4. **Review**: Have changes reviewed by peers to catch potential issues\n")
        
        with open(suggestions_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content))

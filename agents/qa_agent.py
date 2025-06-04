"""
Question Answering Agent for CodeInsight.

This agent is responsible for:
1. Answering questions about the codebase
2. Providing context from the code
3. Explaining code functionality
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional

from langchain.schema import HumanMessage
from llama_index.core import VectorStoreIndex
from llama_index.core import Response

from utils.config import AgentConfig


class QAAgent:
    """Agent for answering questions about the codebase."""
    
    def __init__(self, config: AgentConfig):
        """Initialize the QAAgent.
        
        Args:
            config: Configuration for the agent
        """
        self.config = config
        
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the QA agent.
        
        Args:
            state: Current state of the workflow
            
        Returns:
            Updated state
        """
        try:
            if "code_index" not in state or not state["code_index"]:
                state["errors"].append("Code index must be created before QA")
                return state
            
            # Get default questions if none provided
            if not state.get("questions"):
                state["questions"] = self.config.agent_configs["qa"]["default_questions"]
            
            # Answer each question
            answers = {}
            for question in state["questions"]:
                answer = self.answer_question(state, question)
                answers[question] = answer
            
            state["answers"] = answers
            
            # Update status
            state["status"] = "qa_complete"
            
        except Exception as e:
            state["errors"].append(f"QA error: {str(e)}")
            state["status"] = "error"
            
        return state
    
    def answer_question(self, state: Dict[str, Any], question: str) -> Dict[str, Any]:
        """Answer a question about the codebase.
        
        Args:
            state: Current state of the workflow
            question: Question to answer
            
        Returns:
            Answer with metadata
        """
        # Get the index from the state
        index = state["code_index"]
        
        # Create query engine
        query_engine = index.as_query_engine(similarity_top_k=5)
        
        # Execute query
        response = query_engine.query(question)
        
        # Format answer
        answer = {
            "text": response.response,
            "sources": [],
            "confidence": response.metadata.get("confidence", 0.8)
        }
        
        # Extract source information if available
        if hasattr(response, "source_nodes"):
            for node in response.source_nodes:
                if hasattr(node, "metadata") and "file_path" in node.metadata:
                    source = {
                        "file_path": node.metadata["file_path"],
                        "score": node.score if hasattr(node, "score") else None,
                        "excerpt": node.text[:200] + "..." if len(node.text) > 200 else node.text
                    }
                    answer["sources"].append(source)
        
        return answer
    
    def add_questions(self, state: Dict[str, Any], questions: List[str]) -> Dict[str, Any]:
        """Add questions to the state.
        
        Args:
            state: Current state of the workflow
            questions: Questions to add
            
        Returns:
            Updated state
        """
        if "questions" not in state:
            state["questions"] = []
        
        state["questions"].extend(questions)
        
        return state

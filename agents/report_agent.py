"""
Report Generation Agent for CodeInsight.

This agent is responsible for:
1. Generating comprehensive reports about the codebase
2. Summarizing the findings from other agents
3. Creating a structured overview of the codebase
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

from langchain.schema import HumanMessage
from llama_index.core import VectorStoreIndex

from utils.config import AgentConfig


class ReportAgent:
    """Agent for generating reports about the codebase."""
    
    def __init__(self, config: AgentConfig):
        """Initialize the ReportAgent.
        
        Args:
            config: Configuration for the agent
        """
        self.config = config
        
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the report generation agent.
        
        Args:
            state: Current state of the workflow
            
        Returns:
            Updated state
        """
        try:
            if "understanding" not in state or not state["understanding"]:
                state["errors"].append("Code understanding must be completed before generating report")
                return state
            
            if "answers" not in state or not state["answers"]:
                state["errors"].append("QA process must be completed before generating report")
                return state
            
            # Generate the report
            report = self.generate_report(state)
            state["report"] = report
            
            # Save report to file
            self.save_report(state)
            
            # Update status
            state["status"] = "report_complete"
            
        except Exception as e:
            state["errors"].append(f"Report generation error: {str(e)}")
            state["status"] = "error"
            
        return state
    
    def generate_report(self, state: Dict[str, Any]) -> str:
        """Generate a comprehensive report about the codebase.
        
        Args:
            state: Current state of the workflow
            
        Returns:
            Markdown report
        """
        # Get sections to include
        sections = self.config.agent_configs["report"]["sections"]
        
        # Build the report
        report_sections = []
        
        # Title and introduction
        repo_name = os.path.basename(state["repo_url"].rstrip("/").split("/")[-1])
        report_sections.append(f"# Code Analysis Report: {repo_name}\n")
        report_sections.append("## Introduction\n")
        report_sections.append(
            f"This report provides an analysis of the codebase at {state['repo_url']}. "
            f"It covers the architecture, key components, dependencies, and overall code quality.\n"
        )
        
        # Add sections based on the configuration
        for section in sections:
            if section == "Overview":
                report_sections.append(self._generate_overview_section(state))
            elif section == "Architecture":
                report_sections.append(self._generate_architecture_section(state))
            elif section == "Key Components":
                report_sections.append(self._generate_components_section(state))
            elif section == "Dependencies":
                report_sections.append(self._generate_dependencies_section(state))
            elif section == "Code Quality":
                report_sections.append(self._generate_code_quality_section(state))
        
        # Add QA section
        report_sections.append(self._generate_qa_section(state))
        
        # Add conclusion
        report_sections.append("## Conclusion\n")
        report_sections.append(
            "This report provides a comprehensive analysis of the codebase. "
            "The findings and recommendations should be used to improve code quality, "
            "maintain the codebase effectively, and onboard new developers.\n"
        )
        
        # Join all sections
        return "\n".join(report_sections)
    
    def _generate_overview_section(self, state: Dict[str, Any]) -> str:
        """Generate the overview section of the report.
        
        Args:
            state: Current state of the workflow
            
        Returns:
            Markdown section
        """
        section = ["## Overview\n"]
        
        # Extract information from the state
        if "answers" in state and state["answers"]:
            # Try to find an answer about the codebase purpose
            for question, answer in state["answers"].items():
                if "purpose" in question.lower() or "what is" in question.lower():
                    section.append(f"{answer['text']}\n")
                    break
        
        # Add file statistics
        section.append("### File Statistics\n")
        section.append(f"- Total files analyzed: {len(state['file_list'])}")
        
        # Count files by type
        file_types = {}
        for file_path in state["file_list"]:
            ext = os.path.splitext(file_path)[1].lower()
            if ext:
                file_types[ext] = file_types.get(ext, 0) + 1
        
        if file_types:
            section.append("- File types:")
            for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
                section.append(f"  - {ext}: {count}")
        
        return "\n".join(section)
    
    def _generate_architecture_section(self, state: Dict[str, Any]) -> str:
        """Generate the architecture section of the report.
        
        Args:
            state: Current state of the workflow
            
        Returns:
            Markdown section
        """
        section = ["## Architecture\n"]
        
        if "understanding" in state and "architecture" in state["understanding"]:
            architecture = state["understanding"]["architecture"]
            section.append(f"{architecture['analysis']}\n")
        
        return "\n".join(section)
    
    def _generate_components_section(self, state: Dict[str, Any]) -> str:
        """Generate the components section of the report.
        
        Args:
            state: Current state of the workflow
            
        Returns:
            Markdown section
        """
        section = ["## Key Components\n"]
        
        if "understanding" in state and "components" in state["understanding"]:
            components = state["understanding"]["components"]
            section.append(f"{components['list']}\n")
        
        return "\n".join(section)
    
    def _generate_dependencies_section(self, state: Dict[str, Any]) -> str:
        """Generate the dependencies section of the report.
        
        Args:
            state: Current state of the workflow
            
        Returns:
            Markdown section
        """
        section = ["## Dependencies\n"]
        
        if "understanding" in state and "dependencies" in state["understanding"]:
            dependencies = state["understanding"]["dependencies"]
            section.append(f"{dependencies['analysis']}\n")
        
        return "\n".join(section)
    
    def _generate_code_quality_section(self, state: Dict[str, Any]) -> str:
        """Generate the code quality section of the report.
        
        Args:
            state: Current state of the workflow
            
        Returns:
            Markdown section
        """
        section = ["## Code Quality\n"]
        
        if "understanding" in state and "code_quality" in state["understanding"]:
            code_quality = state["understanding"]["code_quality"]
            section.append(f"{code_quality['analysis']}\n")
        
        return "\n".join(section)
    
    def _generate_qa_section(self, state: Dict[str, Any]) -> str:
        """Generate the Q&A section of the report.
        
        Args:
            state: Current state of the workflow
            
        Returns:
            Markdown section
        """
        section = ["## Questions and Answers\n"]
        
        if "answers" in state and state["answers"]:
            for question, answer in state["answers"].items():
                section.append(f"### Q: {question}\n")
                section.append(f"{answer['text']}\n")
                
                if answer.get("sources"):
                    section.append("**Sources:**\n")
                    for source in answer["sources"]:
                        section.append(f"- {source['file_path']}")
                
                section.append("")  # Add empty line between Q&A pairs
        
        return "\n".join(section)
    
    def save_report(self, state: Dict[str, Any]) -> None:
        """Save the report to a file.
        
        Args:
            state: Current state of the workflow
        """
        output_dir = Path(state["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = output_dir / "report.md"
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(state["report"])

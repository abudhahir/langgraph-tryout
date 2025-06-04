#!/usr/bin/env python3
"""
Main entry point for the CodeInsight Agent application.
"""

import os
import argparse
from pathlib import Path
from typing import Dict, Any, List, TypedDict, Optional

from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from agents.repo_agent import RepoManager
from agents.code_understanding_agent import CodeUnderstandingAgent
from agents.qa_agent import QAAgent
from agents.report_agent import ReportAgent
from agents.documentation_agent import DocumentationAgent
from agents.refactoring_agent import RefactoringAgent
from utils.config import AgentConfig

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="CodeInsight Agent")
    parser.add_argument(
        "--repo", 
        type=str, 
        required=True, 
        help="URL of the GitLab repository to analyze"
    )
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default="./output", 
        help="Directory to save output files"
    )
    parser.add_argument(
        "--model", 
        type=str, 
        default="gpt-4-turbo", 
        help="LLM model to use"
    )
    parser.add_argument(
        "--task", 
        type=str, 
        choices=["all", "understand", "qa", "report", "docs", "refactor"],
        default="all", 
        help="Specific task to perform"
    )
    parser.add_argument(
        "--openai-api-key",
        type=str,
        help="OpenAI API key (alternatively, set OPENAI_API_KEY environment variable)"
    )
    parser.add_argument(
        "--gitlab-token",
        type=str,
        help="GitLab personal access token (alternatively, set GITLAB_TOKEN environment variable)"
    )
    return parser.parse_args()

class AgentState(TypedDict):
    """Type definition for the agent state."""
    repo_path: Optional[str]
    repo_url: Optional[str]
    code_index: Any
    file_list: List[str]
    files_content: Dict[str, str]
    understanding: Dict[str, Any]
    questions: List[str]
    answers: Dict[str, str]
    report: Optional[str]
    documentation: Dict[str, Any]
    refactoring_suggestions: List[Dict[str, Any]]
    errors: List[str]
    status: str
    output_dir: Optional[str]

def create_initial_state() -> AgentState:
    """Initialize the agent state."""
    return {
        "repo_path": None,
        "repo_url": None,
        "code_index": None,
        "file_list": [],
        "files_content": {},
        "understanding": {},
        "questions": [],
        "answers": {},
        "report": None,
        "documentation": {},
        "refactoring_suggestions": [],
        "errors": [],
        "status": "initialized",
        "output_dir": None,
    }

def define_graph(config: AgentConfig) -> StateGraph:
    """Define the LangGraph workflow."""
    # Initialize agents
    repo_agent = RepoManager(config)
    code_understanding_agent = CodeUnderstandingAgent(config)
    qa_agent = QAAgent(config)
    report_agent = ReportAgent(config)
    documentation_agent = DocumentationAgent(config)
    refactoring_agent = RefactoringAgent(config)
    
    # Create graph with properly typed state schema
    workflow = StateGraph(AgentState)
    
    # Add nodes with names that don't conflict with state keys
    workflow.add_node("repo_manager_node", repo_agent.run)
    workflow.add_node("code_understanding_node", code_understanding_agent.run)
    workflow.add_node("qa_node", qa_agent.run)
    workflow.add_node("report_node", report_agent.run)
    workflow.add_node("documentation_node", documentation_agent.run)
    workflow.add_node("refactoring_node", refactoring_agent.run)
    
    # Define edges
    workflow.add_edge("repo_manager_node", "code_understanding_node")
    workflow.add_edge("code_understanding_node", "qa_node")
    workflow.add_edge("qa_node", "report_node")
    workflow.add_edge("report_node", "documentation_node")
    workflow.add_edge("documentation_node", "refactoring_node")
    workflow.add_edge("refactoring_node", END)
    
    # Add conditional edges for specific tasks
    def route_based_on_task(state):
        if config.task == "understand":
            return END if state["status"] == "understanding_complete" else "code_understanding_node"
        elif config.task == "qa":
            return END if state["status"] == "qa_complete" else "qa_node"
        elif config.task == "report":
            return END if state["status"] == "report_complete" else "report_node"
        elif config.task == "docs":
            return END if state["status"] == "documentation_complete" else "documentation_node"
        elif config.task == "refactor":
            return END if state["status"] == "refactoring_complete" else "refactoring_node"
        return None
    
    if config.task != "all":
        for node in ["code_understanding_node", "qa_node", "report_node", "documentation_node", "refactoring_node"]:
            workflow.add_conditional_edges(node, route_based_on_task)
    
    # Set entry point
    workflow.set_entry_point("repo_manager_node")
    
    return workflow

def main():
    """Main function to run the agent."""
    args = parse_args()
    
    # Set API keys from command line if provided
    if args.openai_api_key:
        os.environ["OPENAI_API_KEY"] = args.openai_api_key
        
    if args.gitlab_token:
        os.environ["GITLAB_TOKEN"] = args.gitlab_token
    
    # Validate environment variables
    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError(
            "OpenAI API key not found. Please either:\n"
            "1. Set the OPENAI_API_KEY environment variable, or\n"
            "2. Provide it via the --openai-api-key command-line argument"
        )
    
    if not os.environ.get("GITLAB_TOKEN") and "gitlab" in args.repo:
        print("Warning: GITLAB_TOKEN environment variable not set for GitLab repository.")
        print("Public repositories may work, but private repositories will fail.")
        print("To set it: export GITLAB_TOKEN=your_token_here or use --gitlab-token")
        print("Continuing automatically with public access only...")
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize configuration
    config = AgentConfig(
        repo_url=args.repo,
        output_dir=str(output_dir),
        model_name=args.model,
        task=args.task,
        llm=ChatOpenAI(model=args.model)
    )
    
    # Create and run graph
    graph = define_graph(config)
    app = graph.compile()
    
    # Create initial state
    initial_state = create_initial_state()
    initial_state["repo_url"] = args.repo
    initial_state["output_dir"] = str(output_dir)
    initial_state["status"] = "initialized"
    
    # Run the workflow
    final_state = app.invoke(initial_state)
    
    # Print summary
    print(f"\n\n{'='*50}")
    print("CodeInsight Agent Execution Summary:")
    print(f"{'='*50}")
    print(f"Repository: {args.repo}")
    print(f"Task(s): {args.task}")
    
    if final_state is None:
        print("Status: Error - workflow did not return a valid state")
        print("\nThe LangGraph workflow returned None instead of a state dictionary.")
        print("This might be due to an error in the graph execution or configuration.")
    else:
        print(f"Status: {final_state.get('status', 'unknown')}")
        
        if final_state.get("errors"):
            print("\nErrors encountered:")
            for error in final_state["errors"]:
                print(f" - {error}")
        
        print(f"\nOutput files saved to: {output_dir}")
        
        if "report" in final_state and final_state["report"]:
            report_path = output_dir / "report.md"
            print(f"\nReport generated: {report_path}")
        
        if "documentation" in final_state and final_state["documentation"]:
            docs_path = output_dir / "documentation"
            print(f"\nDocumentation generated: {docs_path}")
        
        if "refactoring_suggestions" in final_state and final_state["refactoring_suggestions"]:
            refactor_path = output_dir / "refactoring.md"
            print(f"\nRefactoring suggestions: {refactor_path}")
    
    print(f"{'='*50}\n")

if __name__ == "__main__":
    main()

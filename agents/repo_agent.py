"""
Repository Manager Agent for CodeInsight.

This agent is responsible for:
1. Cloning repositories from GitLab
2. Managing the local copy of the codebase
3. Indexing the files for further processing
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional

import gitlab
import git
from llama_index.core import SimpleDirectoryReader, Document
from llama_index.core import VectorStoreIndex
from llama_index.core.settings import Settings

from utils.config import AgentConfig


class RepoManager:
    """Agent for managing repository operations."""
    
    def __init__(self, config: AgentConfig):
        """Initialize the RepoManager agent.
        
        Args:
            config: Configuration for the agent
        """
        self.config = config
        self.temp_dir = None
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the repository manager agent.
        
        Args:
            state: Current state of the workflow
            
        Returns:
            Updated state
        """
        try:
            # Clone the repository
            repo_path = self.clone_repository(state["repo_url"])
            state["repo_path"] = repo_path
            
            # Get list of files
            file_list = self.get_file_list(repo_path)
            state["file_list"] = file_list
            
            # Index files for code understanding
            index = self.index_files(repo_path, file_list)
            state["code_index"] = index
            
            # Update status
            state["status"] = "repo_cloned"
            
        except Exception as e:
            state["errors"].append(f"Repository manager error: {str(e)}")
            state["status"] = "error"
            
        return state
    
    def clone_repository(self, repo_url: str) -> str:
        """Clone a repository from GitLab.
        
        Args:
            repo_url: URL of the repository
            
        Returns:
            Path to the cloned repository
        """
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp()
        
        # Check if GitLab token is required
        if "gitlab" in repo_url.lower():
            if "GITLAB_TOKEN" not in os.environ:
                raise ValueError("GITLAB_TOKEN environment variable is required for GitLab repositories")
                
            # Parse GitLab URL to extract project info
            # Example URL: https://gitlab.com/namespace/project or https://gitlab.com/namespace/project.git
            # Remove .git extension if present
            clean_url = repo_url.replace(".git", "")
            parts = clean_url.strip("/").split("/")
            
            if len(parts) < 4:
                raise ValueError(f"Invalid GitLab URL: {repo_url}")
                
            gitlab_url = "/".join(parts[:3])
            
            # The project path should be namespace/project
            project_path = "/".join(parts[3:])
            
            print(f"DEBUG: GitLab URL: {gitlab_url}")
            print(f"DEBUG: Project path: {project_path}")
            
            # Connect to GitLab
            gl = gitlab.Gitlab(gitlab_url, private_token=os.environ["GITLAB_TOKEN"])
            gl.auth()
            
            # Find the project
            project = gl.projects.get(project_path)
            
            # Clone repository using the GitLab token
            repo_url_with_token = repo_url.replace(
                "https://", 
                f"https://oauth2:{os.environ['GITLAB_TOKEN']}@"
            )
            git.Repo.clone_from(repo_url_with_token, self.temp_dir)
        else:
            # Direct clone for public repositories
            git.Repo.clone_from(repo_url, self.temp_dir)
        
        return self.temp_dir
    
    def get_file_list(self, repo_path: str) -> List[str]:
        """Get a list of files in the repository.
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            List of file paths relative to the repository
        """
        file_list = []
        repo_path_obj = Path(repo_path)
        
        for root, dirs, files in os.walk(repo_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.config.exclude_directories]
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, repo_path)
                
                # Check if file extension should be included
                ext = os.path.splitext(file)[1].lower()
                if ext in self.config.include_extensions:
                    file_list.append(rel_path)
        
        # Limit number of files if needed
        return file_list[:self.config.max_files]
    
    def index_files(self, repo_path: str, file_list: List[str]) -> VectorStoreIndex:
        """Index the repository files for semantic search.
        
        Args:
            repo_path: Path to the repository
            file_list: List of files to index
            
        Returns:
            Index of the files
        """
        documents = []
        repo_path_obj = Path(repo_path)
        
        for file_path in file_list:
            abs_path = repo_path_obj / file_path
            
            try:
                with open(abs_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                doc = Document(
                    text=content,
                    metadata={
                        "file_path": file_path,
                        "file_type": os.path.splitext(file_path)[1],
                        "file_name": os.path.basename(file_path)
                    }
                )
                documents.append(doc)
            except Exception as e:
                # Skip files that can't be read as text
                continue
        
        # Configure settings with LLM
        Settings.llm = self.config.llm
        
        # Create index using the global settings
        index = VectorStoreIndex.from_documents(documents)
        
        return index
        
    def __del__(self):
        """Clean up temporary directory when done."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            if self.config.agent_configs.get("repo_manager", {}).get("cleanup", True):
                shutil.rmtree(self.temp_dir)

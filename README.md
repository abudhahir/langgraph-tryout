# CodeInsight Agent

A LangGraph-based agentic solution that can:

- Checkout repositories from GitLab
- Understand codebases
- Answer questions about the code
- Generate reports and documentation
- Suggest refactoring and improvements

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Setup](#setup)
- [Running the Agent](#running-the-agent)
- [Command-line Options](#command-line-options)
- [Usage Examples](#usage-examples)
- [Agent Capabilities](#agent-capabilities)
- [Output Files](#output-files)
- [Customization](#customization)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)
- [Architecture](#architecture)
- [Contributing](#contributing)

## Prerequisites

Before using CodeInsight Agent, ensure you have:

- Python 3.8 or higher
- Git
- Access to the GitLab repositories you want to analyze
- An OpenAI API key for language model access

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/codeinsight-agent.git
   cd codeinsight-agent
   ```

2. Create and activate a virtual environment:
   ```bash
   # Create virtual environment
   python3 -m venv venv
   
   # Activate the virtual environment
   # On Linux/macOS:
   source venv/bin/activate
   # On Windows:
   # venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   When you're done using the agent, you can deactivate the virtual environment:
   ```bash
   deactivate
   ```

## Setup

1. Set up environment variables (you can also create a `.env` file):

   ```bash
   # For OpenAI API access (required)
   export OPENAI_API_KEY="your-openai-api-key"
   
   # For GitLab repository access (required for GitLab repos)
   export GITLAB_TOKEN="your-gitlab-token"
   ```

2. (Optional) Configure the agent behavior by modifying the `utils/config.py` file:
   - Adjust file extensions to include/exclude
   - Change the maximum number of files to process
   - Customize agent-specific configurations

## Running the Agent

### Basic Usage

Run the agent on a GitLab repository:

```bash
python main.py --repo https://gitlab.com/your-username/your-repo-name
```

Run the agent on a local or GitHub repository:

```bash
python main.py --repo https://github.com/your-username/your-repo-name
```

### Specify Output Directory

```bash
python main.py --repo https://gitlab.com/your-username/your-repo-name --output-dir ./analysis-results
```

### Use a Different LLM Model

```bash
python main.py --repo https://gitlab.com/your-username/your-repo-name --model gpt-4o
```

### Run Specific Tasks

Run only the code understanding task:

```bash
python main.py --repo https://gitlab.com/your-username/your-repo-name --task understand
```

Run only the Q&A task:

```bash
python main.py --repo https://gitlab.com/your-username/your-repo-name --task qa
```

## Command-line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--repo` | URL of the GitLab repository to analyze | (Required) |
| `--output-dir` | Directory to save output files | `./output` |
| `--model` | LLM model to use | `gpt-4-turbo` |
| `--task` | Specific task to perform | `all` |

Available task options:
- `all`: Run the complete workflow
- `understand`: Only analyze code structure
- `qa`: Only answer questions about the code
- `report`: Only generate a report
- `docs`: Only generate documentation
- `refactor`: Only suggest refactoring improvements

## Usage Examples

### Analyze a Project and Generate a Full Report

```bash
python main.py --repo https://gitlab.com/your-username/your-project --output-dir ./reports/your-project
```

This will:
1. Clone the repository
2. Analyze the code structure
3. Answer key questions about the codebase
4. Generate a comprehensive report
5. Create documentation
6. Suggest refactoring improvements

### Answer Specific Questions About a Codebase

To ask custom questions, you can modify the default questions in `utils/config.py` under the `qa` agent configuration:

```python
"qa": {
    "default_questions": [
        "What is the main purpose of this codebase?",
        "What are the key dependencies?",
        "What is the architecture of the application?",
        "What are the entry points to the application?",
        "How is the code organized?",
        # Add your custom questions here
    ]
}
```

Then run:

```bash
python main.py --repo https://gitlab.com/your-username/your-project --task qa
```

### Generate Documentation Only

```bash
python main.py --repo https://gitlab.com/your-username/your-project --task docs
```

This will create:
- A comprehensive README.md
- API documentation for key components
- Usage guides

## Agent Capabilities

CodeInsight Agent consists of six specialized agents:

1. **Repository Manager (RepoManager)**
   - Clones repositories from GitLab/GitHub
   - Manages local copies of codebases
   - Indexes files for semantic search

2. **Code Understanding Agent (CodeUnderstandingAgent)**
   - Analyzes codebase structure and architecture
   - Identifies key components and relationships
   - Evaluates code quality

3. **QA Agent (QAAgent)**
   - Answers questions about the codebase
   - Provides context from the code
   - Explains functionality

4. **Report Agent (ReportAgent)**
   - Generates comprehensive reports
   - Summarizes findings
   - Creates structured overviews

5. **Documentation Agent (DocumentationAgent)**
   - Creates README files
   - Generates API documentation
   - Produces usage guides

6. **Refactoring Agent (RefactoringAgent)**
   - Suggests code improvements
   - Identifies technical debt
   - Provides actionable recommendations

## Output Files

The agent generates several output files in the specified output directory:

| File/Directory | Description |
|----------------|-------------|
| `report.md` | Comprehensive analysis report |
| `documentation/README.md` | Generated README file |
| `documentation/api/` | API documentation for components |
| `documentation/usage_guide.md` | Usage instructions |
| `refactoring.md` | Suggested code improvements |

## Customization

You can customize the agent's behavior by modifying `utils/config.py`:

```python
@dataclass
class AgentConfig:
    # ... existing code ...
    
    # Configure file types to analyze
    include_extensions: list = field(default_factory=lambda: [
        ".py", ".js", ".ts", ".java", ".c", ".cpp", 
        # Add or remove extensions based on your needs
    ])
    
    # Configure directories to ignore
    exclude_directories: list = field(default_factory=lambda: [
        "node_modules", "venv", ".git", 
        # Add custom directories to exclude
    ])
```

## Troubleshooting

### Common Issues

1. **Authentication Failures with GitLab**
   - Ensure your `GITLAB_TOKEN` is correctly set
   - Verify you have access to the repository

2. **OpenAI API Errors**
   - Check that your `OPENAI_API_KEY` is valid
   - Ensure you have sufficient credits

3. **Large Repository Processing**
   - For very large repositories, increase `max_files` in `utils/config.py`
   - Consider using `--task` to run specific tasks only

## Advanced Usage

### Programmatic Usage

You can use the CodeInsight Agent programmatically:

```python
from utils.config import AgentConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from main import define_graph

# Configure the agent
config = AgentConfig(
    repo_url="https://gitlab.com/your-username/your-repo",
    output_dir="./output",
    model_name="gpt-4-turbo",
    task="all",
    llm=ChatOpenAI(model="gpt-4-turbo")
)

# Create and run the graph
graph = define_graph(config)
app = graph.compile()

# Run the workflow
final_state = app.invoke({
    "repo_url": "https://gitlab.com/your-username/your-repo",
    "output_dir": "./output",
    "status": "initialized"
})

# Access results
print(f"Report: {final_state['report']}")
print(f"Documentation: {final_state['documentation']}")
```

### Extending the Agent

You can extend the agent by:

1. Creating new agent modules in the `agents/` directory
2. Adding new nodes to the workflow graph in `main.py`
3. Updating the agent configuration in `utils/config.py`

## Architecture

CodeInsight uses LangGraph to orchestrate a multi-agent workflow:

1. The workflow is defined as a directed graph
2. Each agent is a node in the graph
3. Edges define the flow between agents
4. The state dictionary passes information between agents

The main components are:

- **LangGraph**: For workflow orchestration
- **LangChain**: For language model interactions
- **Llama Index**: For semantic search and document retrieval
- **GitPython/python-gitlab**: For repository management

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

# SmolAgent
A lightweight AI agent system powered by SmolAgents and Ollama that executes tasks in a sandboxed Docker environment.

## Features

- Shell command execution in isolated Docker containers
- File writing and management
- Web search capabilities via DuckDuckGo
- Uses Qwen 2.5 Coder (1.5B) model for fast, efficient operation
- Interactive task-based interface

## Requirements

- Python 3.9+
- Docker
- Ollama with qwen2.5-coder:1.5b-instruct model

## Installation

1. Install dependencies:
```bash
pip install smolagents docker litellm
```

2. Pull the required model in Ollama:
```bash
ollama pull qwen2.5-coder:1.5b-instruct
```

3. Ensure Docker is running on your system

## Usage

Run the agent:
```bash
python devin.py
```

Enter tasks when prompted. The agent will:
- Execute shell commands in the sandbox
- Write files to the workspace directory
- Search the web for information
- Verify results before providing answers

Type `exit` or `quit` to stop the agent.

## Docker Setup

The agent automatically creates a Docker container named `smol_devin_sandbox`. The workspace directory is mounted to `/app` inside the container for file access.

To build a custom image (optional):
```bash
docker build -t smol-devin-image .
```

## Configuration

Edit these variables in `devin.py` to customize:
- `MODEL_ID`: Change the LLM model
- `API_BASE`: Ollama server URL
- `CONTAINER_NAME`: Docker container name
- `WORKSPACE_DIR`: Local workspace path
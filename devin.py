import os
import docker
import json
from smolagents import ToolCallingAgent, LiteLLMModel, tool, DuckDuckGoSearchTool

# ==============================================================================
# 1. CONFIGURATION
# ==============================================================================
MODEL_ID = "ollama/qwen2.5-coder:1.5b-instruct"
API_BASE = "http://localhost:11434"
CONTAINER_NAME = "smol_devin_sandbox"
WORKSPACE_DIR = os.path.join(os.getcwd(), "workspace")

if not os.path.exists(WORKSPACE_DIR):
    os.makedirs(WORKSPACE_DIR)

# ==============================================================================
# 2. SETUP DOCKER
# ==============================================================================
print(f"[*] Connecting to Docker...")
client = docker.from_env()

try:
    container = client.containers.get(CONTAINER_NAME)
    if container.status != "running":
        container.start()
except:
    container = client.containers.run(
        "python:3.9-slim",
        name=CONTAINER_NAME,
        detach=True,
        tty=True,
        volumes={WORKSPACE_DIR: {'bind': '/app', 'mode': 'rw'}},
        working_dir="/app"
    )

# ==============================================================================
# 3. DEFINE "GUARDRAIL" TOOLS
# ==============================================================================

@tool
def run_shell_command(command: str) -> str:
    """
    Executes a shell command. 
    Args:
        command: The command string (e.g. 'ls -la', 'python script.py').
    """
    # GUARDRAIL 1: Fix JSON Objects
    # Sometimes the model sends {'command': 'ls'} instead of just 'ls'
    if isinstance(command, dict):
        command = command.get('command', str(command))
    
    # Clean up quotes
    clean_command = str(command).strip("'").strip('"')
    
    # GUARDRAIL 2: The "Did you make the file?" Check
    # If the model tries to run a python script, we check if it exists locally first.
    if clean_command.startswith("python "):
        filename = clean_command.split(" ")[1] # Get 'script.py'
        local_file_path = os.path.join(WORKSPACE_DIR, filename)
        
        # If the file is missing, BLOCK the command and scold the model
        if not os.path.exists(local_file_path):
            return f"SYSTEM ERROR: You cannot run '{filename}' because it does not exist yet! STOP. You must use the 'write_file' tool to create '{filename}' first."

    print(f"    > Shell: {clean_command}")
    
    try:
        result = container.exec_run(
            f"/bin/sh -c '{clean_command}'", 
            workdir="/app"
        )
        output = result.output.decode("utf-8")
        if not output.strip():
            return "Success (Command ran, no output)"
        return output
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def write_file(filename: str, content: str) -> str:
    """
    Writes a file to the workspace.
    Args:
        filename: Name of file (e.g. 'main.py').
        content: The string content of the file.
    """
    print(f"    > Write: {filename}")
    try:
        local_path = os.path.join(WORKSPACE_DIR, filename)
        with open(local_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Success: File '{filename}' has been saved. NOW you can run it."
    except Exception as e:
        return f"Error: {str(e)}"

# ==============================================================================
# 4. INITIALIZE AGENT
# ==============================================================================
print(f"[*] Loading {MODEL_ID}...")

model = LiteLLMModel(
    model_id=MODEL_ID,
    api_base=API_BASE,
    api_key="ollama",
    num_ctx=4096 
)

search_tool = DuckDuckGoSearchTool()

agent = ToolCallingAgent(
    tools=[run_shell_command, write_file, search_tool],
    model=model,
    max_steps=15,
    verbosity_level=1
)

# ==============================================================================
# 5. MAIN LOOP
# ==============================================================================
if __name__ == "__main__":
    print("\nDevin (Guardrails Mode) is Ready!")
    print("   I will now stop the model from running missing files.")
    print("------------------------------------------------------------------")
    
    while True:
        user_input = input("\n>> Task: ")
        if user_input.lower() in ["exit", "quit"]:
            break
            
        # We append a reminder to the user's prompt
        prompt = user_input + " (Remember: Create the file first, THEN run it.)"
        
        print("\nDevin is working...")
        agent.run(prompt)
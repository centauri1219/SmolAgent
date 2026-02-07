import os
import docker
from smolagents import ToolCallingAgent, LiteLLMModel, tool, DuckDuckGoSearchTool

# ==============================================================================
# 1. CONFIGURATION
# ==============================================================================
# We use the 1.5B model for speed and reliability with JSON tools.
MODEL_ID = "ollama/qwen2.5-coder:1.5b-instruct"
API_BASE = "http://localhost:11434"
CONTAINER_NAME = "smol_devin_sandbox"
WORKSPACE_DIR = os.path.join(os.getcwd(), "workspace")

# Create the workspace folder if it doesn't exist
if not os.path.exists(WORKSPACE_DIR):
    os.makedirs(WORKSPACE_DIR)

# ==============================================================================
# 2. SETUP DOCKER (The Sandbox)
# ==============================================================================
print(f"[*] Connecting to Docker...")
client = docker.from_env()

try:
    # Check if the container is already running
    container = client.containers.get(CONTAINER_NAME)
    if container.status != "running":
        container.start()
    print(f"[*] Found running sandbox: {container.short_id}")
except docker.errors.NotFound:
    print(f"[*] Creating new sandbox...")
    # Attempt to use our custom image, fallback to python:3.9-slim
    try:
        client.images.get("smol-devin-image")
        image = "smol-devin-image"
    except:
        print("[!] Custom image not found, using python:3.9-slim")
        image = "python:3.9-slim"

    container = client.containers.run(
        image,
        name=CONTAINER_NAME,
        detach=True,
        tty=True,
        # Mount the workspace so you can see the files the agent creates
        volumes={WORKSPACE_DIR: {'bind': '/app', 'mode': 'rw'}},
        working_dir="/app"
    )
    print(f"[*] Sandbox started: {container.short_id}")

# ==============================================================================
# 3. DEFINE SMART TOOLS
# ==============================================================================

@tool
def run_shell_command(command: str) -> str:
    """
    Executes a shell command inside the Docker environment.
    
    Args:
        command: The command to run (e.g., 'ls -la', 'python script.py'). 
                 Do not wrap the command in extra quotes.
    """
    # 1.5B Model Fix: Strip unnecessary quotes that confuse the shell
    clean_command = command.strip("'").strip('"')
    
    print(f"    > Shell: {clean_command}")
    
    try:
        # We use /bin/sh -c to ensure complex commands (like pipes or python args) work
        result = container.exec_run(
            f"/bin/sh -c '{clean_command}'", 
            workdir="/app"
        )
        output = result.output.decode("utf-8")
        
        # If the command works but has no output (like mkdir), return success
        if not output.strip() and result.exit_code == 0:
            return "Success (No output)"
        elif result.exit_code != 0:
            return f"Error (Exit Code {result.exit_code}): {output}"
            
        return output
    except Exception as e:
        return f"System Error: {str(e)}"

@tool
def write_file(filename: str, content: str) -> str:
    """
    Writes content to a file in the workspace.
    
    Args:
        filename: The name of the file (e.g., 'main.py').
        content: The text content to write into the file.
    """
    print(f"    > Write: {filename}")
    try:
        # Write to the local mounted directory
        local_path = os.path.join(WORKSPACE_DIR, filename)
        with open(local_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote {len(content)} bytes to {filename}"
    except Exception as e:
        return f"File Error: {str(e)}"

# ==============================================================================
# 4. INITIALIZE AGENT
# ==============================================================================
print(f"[*] Loading Model: {MODEL_ID}...")

# Connect to Ollama
model = LiteLLMModel(
    model_id=MODEL_ID,
    api_base=API_BASE,
    api_key="ollama", # Dummy key
    num_ctx=4096      # Enough memory for conversation history
)

# Initialize Web Search Tool
search_tool = DuckDuckGoSearchTool()

# We use ToolCallingAgent (JSON Mode) because it is more robust for 1.5B models
agent = ToolCallingAgent(
    tools=[run_shell_command, write_file, search_tool],
    model=model,
    max_steps=12,      # Give it enough steps to think and correct errors
    verbosity_level=1  # 1 = clean logs, 2 = detailed debug
)

# ==============================================================================
# 5. MAIN LOOP
# ==============================================================================
if __name__ == "__main__":
    print("\nDevin (Smart Mode) is Ready!")
    print("   Capabilities: [Shell Execution] [File Writing] [Web Search]")
    print("   Type 'exit' to quit.")
    print("------------------------------------------------------------------")
    
    while True:
        try:
            user_input = input("\n>> Task: ")
            if user_input.lower() in ["exit", "quit"]:
                break
            
            # Tip: Adding this constraint helps the small model stay focused
            prompt = f"{user_input} (IMPORTANT: Do not output the final answer until you have verified the result with a shell command.)"
            
            print("\nDevin is working...")
            agent.run(prompt)
            
        except KeyboardInterrupt:
            print("\n[!] Task interrupted.")
        except Exception as e:
            print(f"\nError: {e}")
## SimpleC2
This is a simple Command & Control (C2) framework built with Python and Flask.  
It features a terminal that allows you to:

- Send and receive shell commands from an agent
- View live system information from the agent
- Upload files to the agent
- Browse the agent’s file system
- View connection status + last ping

## Requirements

- Python 3.7+ (Agent + Server)

## Getting Started

### 1. Run the Server

```bash
python3 server.py
```

### 2. Run the Agent

```
python3 agent.py
```
The agent will:
- Poll for shell commands
- Post system info on request
- Respond to file browser requests
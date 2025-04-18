const terminalBody = document.getElementById('terminal-body');
const prompt = `${terminalHost} ~ %`;

function createLineWithText(text) {
    const line = document.createElement('div');
    line.className = 'line';
    line.innerHTML = `<span class="prompt">${prompt}</span>${text}`;
    terminalBody.appendChild(line);
}

function createResultLine(text) {
    const result = document.createElement('div');
    result.className = 'result';
    result.textContent = text;
    terminalBody.appendChild(result);
}

function createInputLine() {
    const line = document.createElement('div');
    line.className = 'line';

    const promptSpan = document.createElement('span');
    promptSpan.className = 'prompt';
    promptSpan.textContent = prompt;

    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'cmdInput';
    input.autofocus = true;

    line.appendChild(promptSpan);
    line.appendChild(input);
    terminalBody.appendChild(line);

    input.focus();

    input.addEventListener('keydown', async (e) => {
        if (e.key === 'Enter') {
            const command = input.value.trim();
            if (!command) return;

            line.remove();
            createLineWithText(command);

            const spinner = document.createElement('span');
            spinner.className = 'spinner-dots';
            spinner.textContent = '.';
            terminalBody.appendChild(spinner);

            let dotCount = 1;
            const dotInterval = setInterval(() => {
                dotCount = (dotCount % 5) + 1;
                spinner.textContent = '.'.repeat(dotCount);
            }, 500);

            await fetch('/set_command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command })
            });

            let result = "";
            for (let i = 0; i < 20; i++) {
                const res = await fetch('/get_result');
                const text = await res.text();
                if (text !== "pending") {
                    result = text;
                    break;
                }
                await new Promise(r => setTimeout(r, 500));
            }

            clearInterval(dotInterval);
            spinner.remove();
            createResultLine(result);
            createInputLine();
        }
    });

    terminalBody.scrollTop = terminalBody.scrollHeight;
}

terminalBody.innerHTML = '';
createInputLine();

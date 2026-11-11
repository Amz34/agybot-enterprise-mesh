// AgyBot PWA Client Logic: WebSocket, Screencast, Voice & Command Dispatcher

let ws = null;
let isRecording = false;
let recognition = null;
let deferredPrompt = null;

// Register Service Worker for PWA
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/static/sw.js')
    .then(() => console.log('AgyBot Service Worker Registered'))
    .catch(err => console.error('SW Registration Failed:', err));
}

// PWA Install Prompt Listener
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  const installBtn = document.getElementById('pwaInstallBtn');
  if (installBtn) {
    installBtn.classList.remove('hidden');
    installBtn.addEventListener('click', async () => {
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      if (outcome === 'accepted') {
        installBtn.classList.add('hidden');
      }
      deferredPrompt = null;
    });
  }
});

// Tab Switching
function switchTab(tabId) {
  ['chat', 'screen', 'telemetry'].forEach(t => {
    document.getElementById(`view-${t}`).classList.add('hidden');
    document.getElementById(`tab-${t}`).classList.remove('active-tab');
    document.getElementById(`tab-${t}`).classList.add('text-gray-400');
  });
  document.getElementById(`view-${tabId}`).classList.remove('hidden');
  document.getElementById(`tab-${tabId}`).classList.add('active-tab');
  document.getElementById(`tab-${tabId}`).classList.remove('text-gray-400');
}

// WebSocket Connection
function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  let host = window.location.host;
  let proto = protocol;
  if (window.location.hostname.includes('github.io')) {
    host = 'advanced-amd-supplied-removable.trycloudflare.com';
    proto = 'wss:';
  }
  const wsUrl = `${proto}//${host}/ws`;
  ws = new WebSocket(wsUrl);

  const statusDot = document.getElementById('connectionStatus');

  ws.onopen = () => {
    statusDot.className = 'w-3 h-3 rounded-full bg-emerald-500';
    console.log('Connected to AgyBot Mesh Gateway');
    fetchTelemetry();
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'screencast_frame') {
      const img = document.getElementById('liveCanvas');
      if (img) img.src = `data:image/svg+xml;base64,${data.frame}`;
    } else if (data.type === 'chat_response') {
      appendChatMessage('AgyBot', data.response, 'bot');
      if (data.command_result) {
        appendCommandOutput(data.command_result);
      }
    } else if (data.type === 'telemetry') {
      updateTelemetryDisplay(data.payload);
    }
  };

  ws.onclose = () => {
    statusDot.className = 'w-3 h-3 rounded-full bg-amber-500 animate-pulse';
    setTimeout(connectWebSocket, 3000); // Auto reconnect
  };
}

// Append Chat Messages
function appendChatMessage(sender, text, type = 'user') {
  const container = document.getElementById('chatMessages');
  const msgDiv = document.createElement('div');
  const isBot = type === 'bot';

  msgDiv.className = `glass p-3 rounded-xl max-w-xl ${isBot ? 'self-start' : 'self-end bg-sky-900/40 border-sky-700/50'}`;
  msgDiv.innerHTML = `
    <p class="text-xs ${isBot ? 'text-sky-400' : 'text-emerald-400'} font-semibold mb-1">
      <i class="fa-solid ${isBot ? 'fa-brain' : 'fa-user'} mr-1"></i> ${sender}
    </p>
    <p class="text-sm text-gray-200">${text}</p>
  `;
  container.appendChild(msgDiv);
  container.scrollTop = container.scrollHeight;
}

function appendCommandOutput(res) {
  const container = document.getElementById('chatMessages');
  const outDiv = document.createElement('div');
  outDiv.className = 'glass p-3 rounded-xl max-w-xl self-start bg-black/50 border-gray-800';
  outDiv.innerHTML = `
    <p class="text-xs text-amber-400 font-mono mb-1"><i class="fa-solid fa-terminal mr-1"></i> Executed on VM:</p>
    <pre class="text-xs font-mono text-emerald-400 overflow-x-auto">${res.stdout || res.stderr}</pre>
  `;
  container.appendChild(outDiv);
  container.scrollTop = container.scrollHeight;
}

// Send Message Handler
function sendMessage() {
  const input = document.getElementById('userInput');
  const text = input.value.trim();
  if (!text) return;

  appendChatMessage('You', text, 'user');
  input.value = '';

  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'chat_message', message: text }));
  } else {
    // Fallback REST call
    fetch((window.location.hostname.includes('github.io') ? 'https://advanced-amd-supplied-removable.trycloudflare.com' : '') + '/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    })
    .then(r => r.json())
    .then(d => appendChatMessage('AgyBot', d.response, 'bot'));
  }
}

// Quick Actions
function quickAction(text) {
  document.getElementById('userInput').value = text;
  sendMessage();
}

// Direct Command Runner
function runDirectCommand() {
  const cmd = document.getElementById('directCommandInput').value.trim();
  if (!cmd) return;
  const out = document.getElementById('commandOutput');
  out.textContent = `Running: ${cmd}...`;

  fetch((window.location.hostname.includes('github.io') ? 'https://advanced-amd-supplied-removable.trycloudflare.com' : '') + '/api/exec', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ command: cmd })
  })
  .then(r => r.json())
  .then(d => {
    out.textContent = d.stdout || d.stderr || '(No output)';
  })
  .catch(err => {
    out.textContent = `Error: ${err.message}`;
  });
}

// Browser Navigation
function navigateBrowser() {
  const url = document.getElementById('navUrl').value.trim();
  if (!url || !ws) return;
  ws.send(JSON.stringify({ type: 'browser_navigate', url: url }));
}

// Telemetry Fetch
function fetchTelemetry() {
  fetch((window.location.hostname.includes('github.io') ? 'https://advanced-amd-supplied-removable.trycloudflare.com' : '') + '/api/telemetry')
    .then(r => r.json())
    .then(data => updateTelemetryDisplay(data))
    .catch(() => {});
}

function updateTelemetryDisplay(data) {
  if (data.architecture) {
    document.getElementById('tele-arch').textContent = `${data.architecture}`;
    document.getElementById('tele-cores').textContent = `${data.cpu_cores} vCPUs`;
    document.getElementById('tele-disk').textContent = `${data.disk_usage_pct}% (${data.disk_used_gb}G/${data.disk_total_gb}G)`;
    document.getElementById('hostTelemetry').textContent = `Host Load: ${data.load_averages[0].toFixed(2)} | Disk: ${data.disk_usage_pct}%`;
  }
}

// Voice Recognition (Web Speech API Native)
function setupVoice() {
  const voiceBtn = document.getElementById('voiceBtn');
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    voiceBtn.title = "Voice recognition not supported in this browser";
    return;
  }

  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;

  recognition.onstart = () => {
    isRecording = true;
    voiceBtn.className = 'w-10 h-10 rounded-xl bg-red-600 text-white flex items-center justify-center animate-pulse';
  };

  recognition.onresult = (e) => {
    const transcript = e.results[0][0].transcript;
    document.getElementById('userInput').value = transcript;
    sendMessage();
  };

  recognition.onend = () => {
    isRecording = false;
    voiceBtn.className = 'w-10 h-10 rounded-xl bg-gray-800 hover:bg-gray-700 text-gray-300 flex items-center justify-center';
  };

  voiceBtn.addEventListener('click', () => {
    if (isRecording) {
      recognition.stop();
    } else {
      recognition.start();
    }
  });
}

// Event Listeners
document.getElementById('sendBtn').addEventListener('click', sendMessage);
document.getElementById('userInput').addEventListener('keypress', (e) => {
  if (e.key === 'Enter') sendMessage();
});

// Init
window.onload = () => {
  connectWebSocket();
  setupVoice();
  setInterval(fetchTelemetry, 10000);
};

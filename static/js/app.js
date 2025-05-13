// WebSocket forbindelse
let ws;
let isRecording = false;
let mediaRecorder;
let audioChunks = [];

// DOM elementer
const chatContainer = document.getElementById('chat-container');
const textInput = document.getElementById('text-input');
const sendBtn = document.getElementById('send-btn');
const voiceBtn = document.getElementById('voice-btn');
const connectionStatus = document.getElementById('connection-status');
const startTrainingBtn = document.getElementById('start-training');
const exportModelBtn = document.getElementById('export-model');
const importDataBtn = document.getElementById('import-data');

// Visualiserings elementer
const intentConfidence = document.getElementById('intent-confidence');
const tokenViz = document.getElementById('token-viz');
const trainingMetrics = document.getElementById('training-metrics');
const trainingIterations = document.getElementById('training-iterations');
const trainingAccuracy = document.getElementById('training-accuracy');

// System status
const nluStatus = document.getElementById('nlu-status');
const sttStatus = document.getElementById('stt-status');
const ttsStatus = document.getElementById('tts-status');

// Initialiser WebSocket forbindelse
function initWebSocket() {
    // Brug korrekt WebSocket URL baseret på aktuelle side-URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        console.log('WebSocket forbindelse åbnet');
        if (connectionStatus) {
            connectionStatus.textContent = 'Forbundet';
            connectionStatus.className = 'fixed bottom-4 right-4 px-4 py-2 rounded-full text-sm bg-green-500';
        }
    };
    
    ws.onclose = () => {
        console.log('WebSocket forbindelse lukket');
        if (connectionStatus) {
            connectionStatus.textContent = 'Afbrudt - Forsøger at genoprette...';
            connectionStatus.className = 'fixed bottom-4 right-4 px-4 py-2 rounded-full text-sm bg-red-500';
        }
        // Forsøg at genforbinde efter et kort delay
        setTimeout(initWebSocket, 3000);
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket fejl:', error);
        showError('Fejl i WebSocket-forbindelsen');
    };
    
    ws.onmessage = handleWebSocketMessage;
}

// Håndter indkommende WebSocket beskeder
async function handleWebSocketMessage(event) {
    console.log("Modtaget websocket data:", event.data);
    
    try {
        const data = JSON.parse(event.data);
        console.log("Parsed data:", data);
        
        // Håndter forskellige beskedtyper
        switch(data.type) {
            case 'chat_response':
                addChatMessage(data.message, 'assistant');
                if (data.nlu_data) {
                    updateVisualization(data.nlu_data);
                }
                break;
                
            case 'training_update':
                updateTrainingMetrics(data.metrics);
                break;
                
            case 'system_status':
            case 'status':
                updateSystemStatus(data);
                break;
                
            case 'error':
                showError(data.message);
                break;
                
            default:
                console.log('Ukendt beskedtype:', data.type, data);
                // Hvis der er en besked uden specifik type, men med et message felt
                if (data.message && typeof data.message === 'string') {
                    addChatMessage(data.message, 'assistant');
                }
        }
    } catch (error) {
        console.error('Fejl ved parsing af WebSocket besked:', error);
    }
}

// Tilføj besked til chat
function addChatMessage(message, sender) {
    if (!chatContainer) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `mb-4 ${sender === 'user' ? 'text-right' : 'text-left'}`;
    
    const bubble = document.createElement('div');
    bubble.className = `inline-block p-3 rounded-lg ${
        sender === 'user' 
            ? 'bg-blue-500 text-white' 
            : 'bg-gray-700 text-white'
    }`;
    bubble.textContent = message;
    
    messageDiv.appendChild(bubble);
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Send tekstbesked
function sendMessage() {
    if (!textInput || !ws || ws.readyState !== WebSocket.OPEN) return;
    
    const message = textInput.value.trim();
    if (!message) return;
    
    addChatMessage(message, 'user');
    
    console.log("Sender besked:", message);
    
    // Send korrekt formateret besked til serveren
    ws.send(JSON.stringify({
        type: 'chat_message',
        content: message
    }));
    
    textInput.value = '';
    
    // Vis "tænker" indikator
    showThinking();
}

// Vis "tænker" indikator
function showThinking() {
    if (!chatContainer) return;
    
    const thinkingDiv = document.createElement('div');
    thinkingDiv.className = 'thinking mb-4 text-left';
    thinkingDiv.id = 'thinking-indicator';
    
    const bubble = document.createElement('div');
    bubble.className = 'inline-block p-3 rounded-lg bg-gray-700 text-white';
    bubble.innerHTML = '<span class="dots"><span>.</span><span>.</span><span>.</span></span>';
    
    thinkingDiv.appendChild(bubble);
    chatContainer.appendChild(thinkingDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    // Tilføj CSS for animeret "tænker" indikator
    if (!document.getElementById('thinking-style')) {
        const style = document.createElement('style');
        style.id = 'thinking-style';
        style.textContent = `
            .dots span {
                opacity: 0;
                animation: dot-animation 1.4s infinite;
                animation-fill-mode: both;
            }
            
            .dots span:nth-child(2) {
                animation-delay: 0.2s;
            }
            
            .dots span:nth-child(3) {
                animation-delay: 0.4s;
            }
            
            @keyframes dot-animation {
                0% { opacity: 0; }
                25% { opacity: 1; }
                75% { opacity: 1; }
                100% { opacity: 0; }
            }
        `;
        document.head.appendChild(style);
    }
}

// Fjern "tænker" indikator
function hideThinking() {
    const thinkingIndicator = document.getElementById('thinking-indicator');
    if (thinkingIndicator) {
        thinkingIndicator.remove();
    }
}

// Håndter lydoptagelse
async function toggleRecording() {
    if (!isRecording) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            
            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };
            
            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                const formData = new FormData();
                formData.append('audio', audioBlob);
                
                try {
                    const response = await fetch('/api/speech/stt', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    if (data.text) {
                        textInput.value = data.text;
                        sendMessage();
                    }
                } catch (error) {
                    showError('Fejl under behandling af tale: ' + error.message);
                }
            };
            
            mediaRecorder.start();
            voiceBtn.className = 'bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600';
            isRecording = true;
            
        } catch (error) {
            showError('Kunne ikke starte lydoptagelse: ' + error.message);
        }
    } else {
        mediaRecorder.stop();
        voiceBtn.className = 'bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600';
        isRecording = false;
    }
}

// Opdater visualiseringer
function updateVisualization(metadata) {
    if (!metadata) return;
    
    console.log("Opdaterer visualisering med:", metadata);
    
    if (metadata.intent && metadata.confidence) {
        const confidenceValue = metadata.confidence;
        
        // Opdater eventuelt DOM elementer der viser intent og confidence
        if (document.getElementById('detected-intent')) {
            document.getElementById('detected-intent').textContent = metadata.intent;
        }
        
        if (document.getElementById('confidence-value')) {
            document.getElementById('confidence-value').textContent = (confidenceValue * 100).toFixed(1) + '%';
        }
        
        // Hvis vi har Plotly grafer
        if (typeof Plotly !== 'undefined' && intentConfidence) {
            const data = [{
                values: [confidenceValue, 1 - confidenceValue],
                labels: ['Confidence', 'Uncertainty'],
                type: 'pie'
            }];
            
            const layout = {
                height: 160,
                margin: { t: 0, b: 0, l: 0, r: 0 },
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#fff' }
            };
            
            try {
                Plotly.newPlot(intentConfidence, data, layout);
            } catch (e) {
                console.error('Kunne ikke rendere Plotly graf:', e);
            }
        }
    }
}

// Opdater system status
function updateSystemStatus(data) {
    // Fjern "tænker" indikator når vi får status
    hideThinking();
    
    if (data.modules) {
        // Opdater modul-status visninger
        const modules = Array.isArray(data.modules) ? data.modules : 
                        data.modules.loaded ? Object.keys(data.modules.loaded) : [];
        
        console.log("Aktive moduler:", modules);
        
        // Opdater status-indikatorer hvis de findes
        if (nluStatus) {
            nluStatus.textContent = modules.includes('nlu') ? 'Aktiv' : 'Inaktiv';
            nluStatus.className = `text-${modules.includes('nlu') ? 'green' : 'red'}-400`;
        }
        
        if (sttStatus) {
            sttStatus.textContent = modules.includes('speech') ? 'Klar' : 'Ikke tilgængelig';
            sttStatus.className = `text-${modules.includes('speech') ? 'green' : 'red'}-400`;
        }
        
        if (ttsStatus) {
            ttsStatus.textContent = modules.includes('speech') ? 'Klar' : 'Ikke tilgængelig';
            ttsStatus.className = `text-${modules.includes('speech') ? 'green' : 'red'}-400`;
        }
    }
}

// Vis fejlbesked
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'fixed top-4 right-4 bg-red-500 text-white px-6 py-3 rounded shadow-lg';
    errorDiv.textContent = message;
    document.body.appendChild(errorDiv);
    
    console.error("Fejl:", message);
    
    setTimeout(() => {
        errorDiv.style.opacity = 0;
        errorDiv.style.transition = 'opacity 0.5s ease';
        setTimeout(() => errorDiv.remove(), 500);
    }, 5000);
}

// Initialisering ved siden indlæses
document.addEventListener('DOMContentLoaded', function() {
    console.log('Jarvis UI indlæst');
    
    // Initialiser WebSocket forbindelse
    initWebSocket();
    
    // Tilføj event listeners
    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
    }
    
    if (voiceBtn) {
        voiceBtn.addEventListener('click', toggleRecording);
    }
    
    if (textInput) {
        textInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    }
    
    // Training-knapper
    if (startTrainingBtn) {
        startTrainingBtn.addEventListener('click', () => {
            ws.send(JSON.stringify({ type: 'start_training' }));
        });
    }
    
    if (exportModelBtn) {
        exportModelBtn.addEventListener('click', () => {
            ws.send(JSON.stringify({ type: 'export_model' }));
        });
    }
    
    if (importDataBtn) {
        importDataBtn.addEventListener('click', () => {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.json,.csv';
            input.onchange = async (e) => {
                const file = e.target.files[0];
                const formData = new FormData();
                formData.append('data', file);
                
                try {
                    const response = await fetch('/api/import-data', {
                        method: 'POST',
                        body: formData
                    });
                    const result = await response.json();
                    
                    if (result.success) {
                        showMessage('Data importeret');
                    } else {
                        showError(result.error || 'Fejl ved import af data');
                    }
                } catch (error) {
                    showError('Fejl ved import af data: ' + error.message);
                }
            };
            input.click();
        });
    }
});

// Hjælpefunktion til at vise meddelelser
function showMessage(message) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded shadow-lg';
    msgDiv.textContent = message;
    document.body.appendChild(msgDiv);
    setTimeout(() => {
        msgDiv.style.opacity = 0;
        msgDiv.style.transition = 'opacity 0.5s ease';
        setTimeout(() => msgDiv.remove(), 500);
    }, 3000);
}

// Opdater trænings metrikker
function updateTrainingMetrics(metrics) {
    trainingIterations.textContent = metrics.iterations;
    trainingAccuracy.textContent = `${(metrics.accuracy * 100).toFixed(1)}%`;
    
    const data = [{
        y: metrics.history,
        type: 'scatter',
        line: { color: '#4CAF50' }
    }];
    
    const layout = {
        height: 160,
        margin: { t: 0, b: 20, l: 30, r: 10 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#fff' },
        xaxis: { gridcolor: '#444' },
        yaxis: { gridcolor: '#444' }
    };
    
    Plotly.newPlot(trainingMetrics, data, layout);
} 
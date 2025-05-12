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
    ws = new WebSocket('ws://localhost:8000/ws');
    
    ws.onopen = () => {
        connectionStatus.textContent = 'Forbundet';
        connectionStatus.className = 'fixed bottom-4 right-4 px-4 py-2 rounded-full text-sm bg-green-500';
    };
    
    ws.onclose = () => {
        connectionStatus.textContent = 'Afbrudt - Forsøger at genoprette...';
        connectionStatus.className = 'fixed bottom-4 right-4 px-4 py-2 rounded-full text-sm bg-red-500';
        setTimeout(initWebSocket, 1000);
    };
    
    ws.onmessage = handleWebSocketMessage;
}

// Håndter indkommende WebSocket beskeder
async function handleWebSocketMessage(event) {
    const data = JSON.parse(event.data);
    
    switch(data.type) {
        case 'chat_response':
            addChatMessage(data.message, 'assistant');
            updateVisualization(data.metadata);
            break;
            
        case 'training_update':
            updateTrainingMetrics(data.metrics);
            break;
            
        case 'system_status':
            updateSystemStatus(data.status);
            break;
            
        case 'error':
            showError(data.message);
            break;
    }
}

// Tilføj besked til chat
function addChatMessage(message, sender) {
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
    const message = textInput.value.trim();
    if (!message) return;
    
    addChatMessage(message, 'user');
    ws.send(JSON.stringify({
        type: 'chat_message',
        message: message
    }));
    
    textInput.value = '';
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
                    const response = await fetch('/api/speech-to-text', {
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
    if (metadata.intent_confidence) {
        const data = [{
            values: [metadata.intent_confidence, 1 - metadata.intent_confidence],
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
        
        Plotly.newPlot(intentConfidence, data, layout);
    }
    
    if (metadata.tokens) {
        // Token visualisering med TensorFlow.js
        const tokenData = tf.tensor(metadata.tokens);
        // TODO: Implementer token embedding visualisering
    }
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

// Opdater system status
function updateSystemStatus(status) {
    nluStatus.textContent = status.nlu;
    nluStatus.className = `text-${status.nlu === 'Aktiv' ? 'green' : 'red'}-400`;
    
    sttStatus.textContent = status.stt;
    sttStatus.className = `text-${status.stt === 'Klar' ? 'green' : 'red'}-400`;
    
    ttsStatus.textContent = status.tts;
    ttsStatus.className = `text-${status.tts === 'Klar' ? 'green' : 'red'}-400`;
}

// Vis fejlbesked
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'fixed top-4 right-4 bg-red-500 text-white px-6 py-3 rounded shadow-lg';
    errorDiv.textContent = message;
    document.body.appendChild(errorDiv);
    setTimeout(() => errorDiv.remove(), 5000);
}

// Event listeners
sendBtn.addEventListener('click', sendMessage);
voiceBtn.addEventListener('click', toggleRecording);
textInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

startTrainingBtn.addEventListener('click', () => {
    ws.send(JSON.stringify({ type: 'start_training' }));
});

exportModelBtn.addEventListener('click', () => {
    ws.send(JSON.stringify({ type: 'export_model' }));
});

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
                showError('Data importeret succesfuldt');
            }
        } catch (error) {
            showError('Fejl under import af data: ' + error.message);
        }
    };
    input.click();
});

// Start WebSocket forbindelse
initWebSocket(); 
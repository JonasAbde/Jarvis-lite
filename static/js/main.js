/**
 * Jarvis UI - Main JavaScript
 * Håndterer UI interaktion og WebSocket kommunikation
 */

// WebSocket forbindelse
let socket;
let reconnectTimer;
const RECONNECT_DELAY = 3000;

// UI referencer
const statusIndicator = document.createElement('div');
statusIndicator.className = 'status-indicator';
statusIndicator.title = 'WebSocket forbindelse';
document.body.appendChild(statusIndicator);

// WebSocket funktioner
function connectWebSocket() {
    // Ryd eventuelle tidligere forbindelser
    if (socket) {
        socket.close();
    }

    // Opret ny forbindelse
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    socket = new WebSocket(wsUrl);
    
    socket.addEventListener('open', (event) => {
        console.log('WebSocket forbundet');
        statusIndicator.classList.add('connected');
        statusIndicator.classList.remove('disconnected');
        
        // Ryd reconnect timer hvis den kører
        if (reconnectTimer) {
            clearTimeout(reconnectTimer);
            reconnectTimer = null;
        }
        
        // Anmod om status ved forbindelse
        sendMessage({
            type: 'status_request'
        });
    });
    
    socket.addEventListener('message', (event) => {
        try {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        } catch (error) {
            console.error('Fejl ved parsing af websocket besked:', error);
        }
    });
    
    socket.addEventListener('close', (event) => {
        console.log('WebSocket forbindelse lukket');
        statusIndicator.classList.remove('connected');
        statusIndicator.classList.add('disconnected');
        
        // Forsøg at genforbinde efter et kort delay
        reconnectTimer = setTimeout(() => {
            console.log('Forsøger at genforbinde WebSocket...');
            connectWebSocket();
        }, RECONNECT_DELAY);
    });
    
    socket.addEventListener('error', (error) => {
        console.error('WebSocket fejl:', error);
    });
}

function sendMessage(message) {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(message));
    } else {
        console.warn('WebSocket ikke forbundet, kan ikke sende besked');
    }
}

function handleWebSocketMessage(message) {
    console.log('WebSocket besked modtaget:', message);
    
    switch (message.type) {
        case 'status':
            updateStatus(message.status);
            break;
        case 'module_status':
            updateModuleStatus(message.data);
            break;
        case 'response':
            handleResponse(message.message);
            break;
        case 'error':
            showError(message.message);
            break;
        default:
            console.log('Ukendt beskedtype:', message.type);
    }
}

// UI opdatering funktioner
function updateStatus(status) {
    console.log('Status opdateret:', status);
    // Opdater UI elementer baseret på status
    // Dette implementeres specifikt for hver side
}

function updateModuleStatus(data) {
    // Opdater modul status i UI
    const statusGrid = document.getElementById('status-grid');
    if (!statusGrid) return;
    
    // Implementation afhænger af sidens struktur
}

function handleResponse(message) {
    // Håndtér svar på brugerforespørgsel
    // Implementation afhænger af sidens struktur
}

function showError(message) {
    // Vis fejlbesked til brugeren
    console.error('Fejl:', message);
    
    // Implementer fejlbesked-visning passende til UI'en
    const errorToast = document.createElement('div');
    errorToast.className = 'error-toast';
    errorToast.textContent = message;
    document.body.appendChild(errorToast);
    
    // Fjern fejlbesked efter et stykke tid
    setTimeout(() => {
        errorToast.classList.add('fade-out');
        setTimeout(() => {
            document.body.removeChild(errorToast);
        }, 500);
    }, 5000);
}

// Generelle UI hjælpefunktioner
function formatTimestamp(timestamp) {
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString();
}

// Initialiser ved page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Jarvis UI indlæst');
    
    // Start WebSocket forbindelse
    connectWebSocket();
    
    // Tilføj stylesheet til status indikator
    const style = document.createElement('style');
    style.textContent = `
        .status-indicator {
            position: fixed;
            bottom: 10px;
            right: 10px;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            z-index: 9999;
        }
        
        .status-indicator.connected {
            background-color: #2ecc71;
            box-shadow: 0 0 5px #2ecc71;
        }
        
        .status-indicator.disconnected {
            background-color: #e74c3c;
            box-shadow: 0 0 5px #e74c3c;
        }
        
        .error-toast {
            position: fixed;
            top: 20px;
            right: 20px;
            background-color: #e74c3c;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
            z-index: 1000;
            animation: fadeIn 0.3s;
        }
        
        .error-toast.fade-out {
            animation: fadeOut 0.5s;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateX(20px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        @keyframes fadeOut {
            from { opacity: 1; transform: translateX(0); }
            to { opacity: 0; transform: translateX(20px); }
        }
    `;
    document.head.appendChild(style);
}); 
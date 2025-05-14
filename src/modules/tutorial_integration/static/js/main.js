/**
 * Jarvis Web Client Integration
 * Håndterer kommunikation med Jarvis API
 */

// WebSocket forbindelse
let ws = null;
let isConnecting = false;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;
const reconnectInterval = 3000; // 3 sekunder

// DOM Elementer
document.addEventListener('DOMContentLoaded', () => {
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const chatMessages = document.getElementById('chat-messages');
    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');

    // Initialisér WebSocket forbindelse
    initializeWebSocket();

    // Tilføj en "velkommen" besked
    addMessage('Hej! Jeg er Jarvis, din danske assistent. Hvordan kan jeg hjælpe dig i dag?', 'assistant');

    // Event listener til send-knappen
    sendButton.addEventListener('click', () => sendUserMessage());
    
    // Event listener til input-feltet (Enter tast)
    messageInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            sendUserMessage();
        }
    });

    // Funktion til at sende brugerbesked
    function sendUserMessage() {
        const message = messageInput.value.trim();
        
        if (message) {
            addMessage(message, 'user');
            
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'chat',
                    text: message
                }));
                
                // Vis "skriver" indikator
                showTypingIndicator();
            } else {
                addMessage('Beklager, forbindelsen til serveren er afbrudt. Prøver at genoprette forbindelsen...', 'assistant');
                initializeWebSocket();
            }
            
            messageInput.value = '';
            messageInput.focus();
        }
    }
    
    // Funktion til at vise "skriver" indikator
    function showTypingIndicator() {
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'typing-indicator';
        typingIndicator.id = 'typing-indicator';
        typingIndicator.innerHTML = '<span></span><span></span><span></span>';
        chatMessages.appendChild(typingIndicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Funktion til at skjule "skriver" indikator
    function hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    // Funktion til at tilføje besked til chatten
    window.addMessage = function(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = `message-bubble ${sender}-bubble`;
        bubbleDiv.textContent = text;
        
        messageDiv.appendChild(bubbleDiv);
        chatMessages.appendChild(messageDiv);
        
        // Scroll til bunden af chat-vinduet
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    // Funktion til at opdatere forbindelsesstatus
    window.updateConnectionStatus = function(connected) {
        if (connected) {
            statusIndicator.classList.add('connected');
            statusText.textContent = 'Forbundet';
        } else {
            statusIndicator.classList.remove('connected');
            statusText.textContent = 'Afbrudt';
        }
    };
});

// Initialisér WebSocket forbindelse
function initializeWebSocket() {
    if (ws !== null || isConnecting) {
        return;
    }
    
    isConnecting = true;
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Ændrer port til 8080 for at matche API serveren
    const host = window.location.hostname + (window.location.port ? ':8080' : '');
    const wsUrl = `${protocol}//${host}/ws`;
    
    console.log('Forsøger at oprette WebSocket forbindelse til:', wsUrl);
    
    try {
        ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
            console.log('WebSocket forbindelse etableret');
            isConnecting = false;
            reconnectAttempts = 0;
            updateConnectionStatus(true);
            
            // Anmod om status
            ws.send(JSON.stringify({
                type: 'status'
            }));
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Modtaget WebSocket besked:', data);
            
            // Skjul "skriver" indikator
            hideTypingIndicator();
            
            if (data.type === 'response') {
                // Håndter chat-svar
                addMessage(data.text, 'assistant');
                
                // Afspil audio hvis tilgængeligt
                if (data.audio) {
                    playAudio(data.audio);
                }
            } else if (data.type === 'status') {
                // Håndter status-opdateringer
                updateConnectionStatus(data.connected);
            } else if (data.type === 'error') {
                // Håndter fejlbeskeder
                addMessage(`Fejl: ${data.message}`, 'assistant');
            } else if (data.type === 'welcome') {
                // Håndter velkomstbesked
                addMessage(data.message, 'assistant');
            }
        };
        
        ws.onclose = (event) => {
            console.log(`WebSocket forbindelse lukket: ${event.code} ${event.reason}`);
            isConnecting = false;
            ws = null;
            updateConnectionStatus(false);
            
            // Forsøg at genoprette forbindelsen
            if (reconnectAttempts < maxReconnectAttempts) {
                reconnectAttempts++;
                console.log(`Forsøger at genoprette forbindelsen (forsøg ${reconnectAttempts}/${maxReconnectAttempts})...`);
                
                setTimeout(() => {
                    initializeWebSocket();
                }, reconnectInterval);
            } else {
                console.error('Kunne ikke genoprette WebSocket forbindelsen efter flere forsøg');
                addMessage('Kunne ikke genoprette forbindelsen til serveren. Prøv at genindlæse siden.', 'assistant');
            }
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket fejl:', error);
            isConnecting = false;
            updateConnectionStatus(false);
        };
    } catch (error) {
        console.error('Fejl ved oprettelse af WebSocket:', error);
        isConnecting = false;
        updateConnectionStatus(false);
    }
}

// Afspil audio data (base64-encoded)
function playAudio(audioBase64) {
    try {
        // Konvertér base64 til blob
        const byteCharacters = atob(audioBase64);
        const byteNumbers = new Array(byteCharacters.length);
        
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        
        const byteArray = new Uint8Array(byteNumbers);
        const audioBlob = new Blob([byteArray], { type: 'audio/mp3' });
        
        // Opret en URL til blob'en
        const audioUrl = URL.createObjectURL(audioBlob);
        
        // Opret og afspil audio element
        const audio = new Audio(audioUrl);
        audio.play().catch(error => {
            console.error('Fejl ved afspilning af audio:', error);
        });
        
        // Ryd op: frigiv blob URL når lyden er færdig
        audio.onended = () => {
            URL.revokeObjectURL(audioUrl);
        };
    } catch (error) {
        console.error('Fejl ved behandling af audio data:', error);
    }
}
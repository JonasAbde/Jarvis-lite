// Jarvis-Lite Chat UI - App.js

// Konfiguration
const CONFIG = {
    API_URL: 'http://localhost:8000',
    ENDPOINTS: {
        status: '/status',
        listenToggle: '/command/listen_toggle',
        sendChat: '/api/chat/send',
        history: '/api/chat/history',
        clearHistory: '/api/chat/clear_history'
    },
    RECONNECT_DELAY: 5000,
    STATUS_CHECK_INTERVAL: 15000,
    MAX_RETRIES: 3
};

// State
const state = {
    isRecording: false,
    isListening: false,
    isDarkMode: localStorage.getItem('darkMode') === 'true',
    selectedVoice: localStorage.getItem('selectedVoice') || 'david',
    autoSpeak: localStorage.getItem('autoSpeak') === 'true',
    connectionStatus: 'connecting',
    retryCount: 0
};

// DOM Elements
const elements = {
    messageInput: document.getElementById('message-input'),
    sendButton: document.getElementById('send-button'),
    voiceButton: document.getElementById('voice-button'),
    themeToggle: document.getElementById('theme-toggle'),
    settingsButton: document.getElementById('settings-button'),
    closeSettingsButton: document.getElementById('close-settings-button'),
    settingsPanel: document.getElementById('settings-panel'),
    clearHistoryButton: document.getElementById('clear-history-button'),
    autoSpeakToggle: document.getElementById('auto-speak-toggle'),
    voiceSelect: document.getElementById('voice-select'),
    connectionStatus: document.getElementById('connection-status'),
    typingIndicator: document.getElementById('typing-indicator'),
    chatMessages: document.getElementById('chat-messages'),
    recordingIndicator: document.getElementById('recording-indicator'),
    coreStatus: document.getElementById('core-status'),
    nluStatus: document.getElementById('nlu-status'),
    speechStatus: document.getElementById('speech-status'),
    newChatButton: document.getElementById('new-chat-button'),
    chatHistory: document.getElementById('chat-history')
};

// Hjælpefunktioner
const utils = {
    debounce(func, wait) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    },

    async fetchWithTimeout(url, options = {}, timeout = 10000) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);
        
        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal
            });
            clearTimeout(timeoutId);
            return response;
        } catch (error) {
            clearTimeout(timeoutId);
            throw error;
        }
    },

    showError(message, isTemporary = true) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4';
        errorDiv.textContent = message;
        
        elements.chatMessages.insertBefore(errorDiv, elements.chatMessages.firstChild);
        
        if (isTemporary) {
            setTimeout(() => errorDiv.remove(), 5000);
        }
    },

    updateConnectionStatus(status) {
        state.connectionStatus = status;
        elements.connectionStatus.innerHTML = `
            <span class="status-badge ${status}">${
                status === 'online' ? 'Forbundet' :
                status === 'offline' ? 'Afbrudt' :
                'Forbinder...'
            }</span>
        `;
    },

    scrollToBottom() {
        requestAnimationFrame(() => {
            elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
        });
    }
};

// API funktioner
const api = {
    async checkStatus() {
        try {
            const response = await utils.fetchWithTimeout(
                `${CONFIG.API_URL}${CONFIG.ENDPOINTS.status}`,
                { method: 'GET' }
            );
            
            if (!response.ok) throw new Error('API svarer ikke');
            
            const data = await response.json();
            state.isListening = data.status === 'listening';
            utils.updateConnectionStatus('online');
            
            // Opdater komponentstatus
            elements.coreStatus.className = `status-badge ${data.core ? 'online' : 'offline'}`;
            elements.nluStatus.className = `status-badge ${data.nlu ? 'online' : 'offline'}`;
            elements.speechStatus.className = `status-badge ${data.speech ? 'online' : 'offline'}`;
            
            state.retryCount = 0;
        } catch (error) {
            console.error('Status check fejl:', error);
            utils.updateConnectionStatus('offline');
            
            if (state.retryCount < CONFIG.MAX_RETRIES) {
                state.retryCount++;
                setTimeout(() => api.checkStatus(), CONFIG.RECONNECT_DELAY);
            } else {
                utils.showError('Kunne ikke oprette forbindelse til serveren. Prøv at genindlæse siden.');
            }
        }
    },

    async toggleListening() {
        try {
            const response = await utils.fetchWithTimeout(
                `${CONFIG.API_URL}${CONFIG.ENDPOINTS.listenToggle}`,
                { method: 'POST' }
            );
            
            if (!response.ok) throw new Error('Kunne ikke skifte lyttetilstand');
            
            const data = await response.json();
            state.isListening = data.listening_enabled;
            elements.autoSpeakToggle.checked = state.isListening;
        } catch (error) {
            console.error('Toggle listening fejl:', error);
            utils.showError('Kunne ikke ændre lyttetilstand');
            elements.autoSpeakToggle.checked = !elements.autoSpeakToggle.checked;
        }
    },

    async sendMessage(message) {
        if (!message.trim()) return;
        
        try {
            elements.typingIndicator.style.display = 'block';
            elements.messageInput.value = '';
            elements.messageInput.focus();
            
            chatUI.addMessage('user', message);
            
            const response = await utils.fetchWithTimeout(
                `${CONFIG.API_URL}${CONFIG.ENDPOINTS.sendChat}`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message,
                        voice: state.selectedVoice
                    })
                }
            );
            
            if (!response.ok) throw new Error('Serverfejl');
            
            const data = await response.json();
            if (!data.response) throw new Error('Tomt svar fra server');
            
            chatUI.addMessage('jarvis', data.response);
        } catch (error) {
            console.error('Send message fejl:', error);
            utils.showError('Kunne ikke sende besked');
        } finally {
            elements.typingIndicator.style.display = 'none';
            utils.scrollToBottom();
        }
    },

    async loadHistory() {
        try {
            const response = await utils.fetchWithTimeout(
                `${CONFIG.API_URL}${CONFIG.ENDPOINTS.history}`,
                { method: 'GET' }
            );
            
            if (!response.ok) throw new Error('Kunne ikke hente historik');
            
            const data = await response.json();
            chatUI.displayHistory(data);
        } catch (error) {
            console.error('Load history fejl:', error);
            utils.showError('Kunne ikke indlæse chathistorik');
        }
    },

    async clearHistory() {
        try {
            elements.clearHistoryButton.disabled = true;
            
            const response = await utils.fetchWithTimeout(
                `${CONFIG.API_URL}${CONFIG.ENDPOINTS.clearHistory}`,
                { method: 'POST' }
            );
            
            if (!response.ok) throw new Error('Kunne ikke rydde historik');
            
            elements.chatMessages.innerHTML = '';
            chatUI.addMessage('jarvis', 'Chathistorikken er ryddet. Hvordan kan jeg hjælpe dig?');
        } catch (error) {
            console.error('Clear history fejl:', error);
            utils.showError('Kunne ikke rydde chathistorik');
        } finally {
            elements.clearHistoryButton.disabled = false;
        }
    }
};

// Chat UI
const chatUI = {
    addMessage(sender, text) {
        if (!text.trim()) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = sender === 'user' ? 'user-message p-4 mb-4' : 'bot-message p-4 mb-4';
        
        const textContent = document.createElement('p');
        textContent.textContent = text;
        messageDiv.appendChild(textContent);
        
        elements.chatMessages.appendChild(messageDiv);
        utils.scrollToBottom();
    },

    displayHistory(data) {
        elements.chatMessages.innerHTML = '';
        
        if (data?.history?.length) {
            data.history.forEach(entry => {
                if (entry.user) this.addMessage('user', entry.user);
                if (entry.jarvis) this.addMessage('jarvis', entry.jarvis);
            });
        }
        
        utils.scrollToBottom();
    }
};

// WebSocket setup
const ws = {
    instance: null,
    isConnecting: false,
    reconnectAttempts: 0,
    maxReconnectAttempts: 5,
    reconnectDelay: 1000,

    async connect() {
        if (this.isConnecting) return;
        this.isConnecting = true;

        try {
            // Brug relativ sti for WebSocket
            const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`;
            console.log('Forsøger at forbinde til WebSocket:', wsUrl);
            
            this.instance = new WebSocket(wsUrl);
            
            this.instance.onopen = () => {
                console.log('WebSocket forbundet');
                utils.updateConnectionStatus('online');
                this.reconnectAttempts = 0;
                this.isConnecting = false;
            };
            
            this.instance.onclose = (event) => {
                console.log('WebSocket lukket:', event.code, event.reason);
                utils.updateConnectionStatus('offline');
                this.instance = null;
                this.isConnecting = false;
                
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.reconnectAttempts++;
                    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
                    console.log(`Forsøger at genoprette forbindelse om ${delay}ms`);
                    setTimeout(() => this.connect(), delay);
                } else {
                    utils.showError('Kunne ikke oprette forbindelse til serveren. Genindlæs siden for at prøve igen.');
                }
            };
            
            this.instance.onerror = (error) => {
                console.error('WebSocket fejl:', error);
                utils.showError('Forbindelsesfejl - prøver at genoprette forbindelse');
            };
            
            this.instance.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    handlers.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('Fejl ved parsing af WebSocket besked:', error);
                }
            };
            
        } catch (error) {
            console.error('Fejl ved oprettelse af WebSocket:', error);
            this.isConnecting = false;
            utils.showError('Kunne ikke oprette WebSocket forbindelse');
            setTimeout(() => this.connect(), this.reconnectDelay);
        }
    },

    send(data) {
        if (!this.instance || this.instance.readyState !== WebSocket.OPEN) {
            utils.showError('Ingen forbindelse til serveren');
            return false;
        }
        
        try {
            this.instance.send(JSON.stringify(data));
            return true;
        } catch (error) {
            console.error('Fejl ved sending af besked:', error);
            return false;
        }
    }
};

// Audio handling
const audio = {
    stream: null,
    mediaRecorder: null,
    audioChunks: [],
    isRecording: false,

    async requestPermissions() {
        try {
            // Tjek først om browseren understøtter getUserMedia
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('Din browser understøtter ikke mikrofon-optagelse');
            }

            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    channelCount: 1,
                    sampleRate: 16000,
                    echoCancellation: true,
                    noiseSuppression: true
                } 
            });
            
            this.stream = stream;
            return true;
        } catch (error) {
            console.error('Mikrofon adgang fejl:', error);
            let errorMessage = 'Kunne ikke få adgang til mikrofonen. ';
            
            if (error.name === 'NotAllowedError') {
                errorMessage += 'Giv venligst tilladelse til mikrofon i din browser.';
            } else if (error.name === 'NotFoundError') {
                errorMessage += 'Ingen mikrofon fundet.';
            } else {
                errorMessage += 'Tjek browser-tilladelser og mikrofonindstillinger.';
            }
            
            utils.showError(errorMessage);
            return false;
        }
    },

    async startRecording() {
        if (this.isRecording) return;
        
        if (!this.stream) {
            const hasPermission = await this.requestPermissions();
            if (!hasPermission) return;
        }

        try {
            this.audioChunks = [];
            this.mediaRecorder = new MediaRecorder(this.stream, {
                mimeType: 'audio/webm;codecs=opus',
                audioBitsPerSecond: 16000
            });
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                    // Send audio chunk via WebSocket
                    if (ws.instance && ws.instance.readyState === WebSocket.OPEN) {
                        ws.instance.send(event.data);
                    }
                }
            };
            
            this.mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm;codecs=opus' });
                await this.sendAudioToServer(audioBlob);
                elements.recordingIndicator.classList.add('hidden');
            };
            
            // Start optagelse med 100ms intervaller
            this.mediaRecorder.start(100);
            this.isRecording = true;
            elements.recordingIndicator.classList.remove('hidden');
            elements.voiceButton.classList.add('recording-active');
            
        } catch (error) {
            console.error('Fejl ved start af optagelse:', error);
            utils.showError('Kunne ikke starte lydoptagelse');
        }
    },

    stopRecording() {
        if (!this.isRecording || !this.mediaRecorder) return;
        
        try {
            this.mediaRecorder.stop();
            this.isRecording = false;
            elements.voiceButton.classList.remove('recording-active');
        } catch (error) {
            console.error('Fejl ved stop af optagelse:', error);
            utils.showError('Kunne ikke stoppe lydoptagelse');
        }
    },

    async sendAudioToServer(audioBlob) {
        try {
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.wav');
            
            const response = await fetch('/api/transcribe', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) throw new Error('Server fejl');
            
            const data = await response.json();
            if (data.text) {
                elements.messageInput.value = data.text;
                handlers.onSendMessage({ preventDefault: () => {} });
            }
            
        } catch (error) {
            console.error('Fejl ved sending af lydoptagelse:', error);
            utils.showError('Kunne ikke sende lydoptagelse til serveren');
        }
    }
};

// Event handlers
const handlers = {
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'status':
                utils.updateConnectionStatus(data.status);
                state.isListening = data.is_listening;
                elements.autoSpeakToggle.checked = data.is_listening;
                break;
                
            case 'response':
                chatUI.addMessage('jarvis', data.jarvis_response);
                break;
                
            case 'error':
                utils.showError(data.message);
                break;
                
            default:
                console.warn('Ukendt beskedtype:', data.type);
        }
    },
    
    onSettingsToggle() {
        elements.settingsPanel.classList.toggle('hidden');
        elements.settingsPanel.classList.toggle('translate-x-0');
    },
    
    onVoiceButtonClick() {
        if (audio.isRecording) {
            audio.stopRecording();
        } else {
            audio.startRecording();
        }
    },
    
    onSendMessage: utils.debounce((event) => {
        event.preventDefault();
        const message = elements.messageInput.value.trim();
        if (message) api.sendMessage(message);
    }, 300),
    
    onKeyPress(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            handlers.onSendMessage(event);
        }
    },
    
    onAutoSpeakToggle: utils.debounce(() => {
        state.autoSpeak = elements.autoSpeakToggle.checked;
        localStorage.setItem('autoSpeak', state.autoSpeak);
        api.toggleListening();
    }, 300),
    
    onVoiceSelect() {
        state.selectedVoice = elements.voiceSelect.value;
        localStorage.setItem('selectedVoice', state.selectedVoice);
    }
};

// Event Handlers
elements.messageInput.addEventListener('keypress', handlers.onKeyPress);
elements.sendButton.addEventListener('click', handlers.onSendMessage);
elements.voiceButton.addEventListener('click', handlers.onVoiceButtonClick);
elements.themeToggle.addEventListener('click', handlers.onThemeToggle);
elements.settingsButton.addEventListener('click', handlers.onSettingsToggle);
elements.closeSettingsButton.addEventListener('click', handlers.onSettingsToggle);
elements.autoSpeakToggle.addEventListener('change', handlers.onAutoSpeakToggle);
elements.voiceSelect.addEventListener('change', handlers.onVoiceSelect);
elements.clearHistoryButton.addEventListener('click', api.clearHistory);

// Initialisering
function initialize() {
    // Indlæs gemte indstillinger
    document.body.classList.toggle('dark-mode', state.isDarkMode);
    elements.autoSpeakToggle.checked = state.autoSpeak;
    elements.voiceSelect.value = state.selectedVoice;
    
    // Tilføj event listeners
    elements.messageInput.addEventListener('keypress', handlers.onKeyPress);
    elements.sendButton.addEventListener('click', handlers.onSendMessage);
    elements.voiceButton.addEventListener('click', handlers.onVoiceButtonClick);
    elements.themeToggle.addEventListener('click', handlers.onThemeToggle);
    elements.settingsButton.addEventListener('click', handlers.onSettingsToggle);
    elements.closeSettingsButton.addEventListener('click', handlers.onSettingsToggle);
    elements.autoSpeakToggle.addEventListener('change', handlers.onAutoSpeakToggle);
    elements.voiceSelect.addEventListener('change', handlers.onVoiceSelect);
    elements.clearHistoryButton.addEventListener('click', api.clearHistory);
    
    // Start services
    api.checkStatus();
    api.loadHistory();
    ws.connect();
    
    // Start status check interval
    setInterval(() => api.checkStatus(), CONFIG.STATUS_CHECK_INTERVAL);
}

// Start app når DOM er klar
document.addEventListener('DOMContentLoaded', initialize); 
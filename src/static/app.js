// Jarvis-Lite Chat UI - App.js

// Konfiguration
const API_URL = 'http://localhost:8000';
const ENDPOINTS = {
    status: `${API_URL}/status`,
    listenToggle: `${API_URL}/command/listen_toggle`,
    sendChat: `${API_URL}/api/chat/send`,
    history: `${API_URL}/api/chat/history`,
    clearHistory: `${API_URL}/api/chat/clear_history`
};

// DOM-elementer - indlæs kun én gang ved opstart for bedre ydelse
const chatContainer = document.getElementById('chat-container');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const voiceButton = document.getElementById('voice-button');
const themeToggle = document.getElementById('theme-toggle');
const settingsButton = document.getElementById('settings-button');
const closeSettingsButton = document.getElementById('close-settings');
const settingsPanel = document.getElementById('settings-panel');
const clearHistoryButton = document.getElementById('clear-history-btn');
const listenToggle = document.getElementById('listen-toggle');
const listenToggleLabel = document.getElementById('listen-toggle-label');
const voiceSelection = document.getElementById('voice-selection');
const statusText = document.getElementById('status-text');
const statusIndicator = document.getElementById('status-indicator');
const typingIndicator = document.getElementById('typing-indicator');

// State
let isRecording = false;
let isListening = false;
let isDarkMode = false;
let wsConnection = null;
let wsConnected = false;
let selectedVoice = localStorage.getItem('selectedVoice') || 'david';
let statusCheckInterval = null;
let lastStatusCheck = 0;
let recognitionInstance = null;

// Hjælpefunktioner
function debounce(func, wait) {
    let timeout;
    return function() {
        const context = this;
        const args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
}

// Cache for at reducere API-kald
const apiCache = {
    status: { data: null, timestamp: 0 },
    history: { data: null, timestamp: 0 }
};

// Indlæs eller genindlæs alle DOM-referencer
function cacheDOMElements() {
    // De vigtigste DOM elementer er allerede cachet øverst
}

// Initialisering
document.addEventListener('DOMContentLoaded', () => {
    initializeChatApp();
});

async function initializeChatApp() {
    try {
        // Cachede DOM elementer ved opstart
        cacheDOMElements();
        
        // Tjek forbindelse til API
        await checkApiStatus(true); // force check første gang
        
        // Hent chat-historik
        await loadChatHistory();
        
        // Indlæs indstillinger (hvis gemt i localStorage)
        loadSettings();
        
        // Indstil event listeners
        setupEventListeners();
        
        // Start statusopdateringsloop - mindre hyppig polling
        statusCheckInterval = setInterval(() => checkApiStatus(false), 15000); // 15 sekunder i stedet for 10
    } catch (error) {
        console.error('Fejl under initialisering:', error);
        updateStatusUI(false, 'Forbindelsesfejl');
    }
}

// API funktioner
async function checkApiStatus(force = false) {
    // Undgå for hyppige API-kald
    const now = Date.now();
    if (!force && now - lastStatusCheck < 5000) return; // max én gang hver 5. sekund
    
    lastStatusCheck = now;
    
    try {
        const response = await fetch(ENDPOINTS.status);
        if (!response.ok) throw new Error('API svarer ikke');
        
        const data = await response.json();
        isListening = data.status === 'lytter';
        
        // Opdater UI baseret på status - kun hvis status har ændret sig
        if (!apiCache.status.data || apiCache.status.data.status !== data.status) {
            updateStatusUI(true, data.status === 'lytter' ? 'Lytter aktivt' : 'Forbundet');
            if (listenToggle) listenToggle.checked = data.status === 'lytter';
        }
        
        // Opdater cache
        apiCache.status = { data, timestamp: now };
    } catch (error) {
        console.error('Status API fejl:', error);
        updateStatusUI(false, 'Forbindelsesfejl');
    }
}

async function toggleListening() {
    try {
        const response = await fetch(ENDPOINTS.listenToggle, {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Kunne ikke skifte lyttetilstand');
        
        const data = await response.json();
        isListening = data.listening_enabled;
        
        updateStatusUI(true, data.listening_enabled ? 'Lytter aktivt' : 'Forbundet');
        listenToggle.checked = data.listening_enabled;
    } catch (error) {
        console.error('Fejl ved skift af lyttetilstand:', error);
        // Nulstil til modsat værdi, da ændringen fejlede
        listenToggle.checked = !listenToggle.checked;
    }
}

async function sendChatMessage(message) {
    try {
        // Opdater UI først for bedre responsivitet
        addMessageToChat('user', message);
        
        // Nulstil input feltet
        if (userInput) {
            userInput.value = '';
            userInput.focus();
        }
        
        // Vis indikator på, at Jarvis "tænker"
        if (typingIndicator) {
            typingIndicator.classList.add('active');
        }
        
        // Send til API med timeout for at undgå uendelig ventetid
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);  // 10 sekunder timeout
        
        const response = await fetch(ENDPOINTS.sendChat, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                message: message,
                voice: selectedVoice 
            }),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            console.error('Server fejl:', errorData);
            throw new Error(`Kunne ikke sende besked: ${response.status} ${errorData.detail || ''}`);
        }
        
        const data = await response.json();
        
        // Fjern "tænker" indikator
        if (typingIndicator) {
            typingIndicator.classList.remove('active');
        }
        
        // Vis jarvis svar
        if (data && data.response) {
            addMessageToChat('jarvis', data.response);
        } else {
            throw new Error('Modtog tomt svar fra serveren');
        }
    } catch (error) {
        console.error('Fejl ved sending af besked:', error);
        
        // Fjern "tænker" indikator
        if (typingIndicator) {
            typingIndicator.classList.remove('active');
        }
        
        // Vis fejlbesked til brugeren
        addMessageToChat('jarvis', 'Beklager, jeg kunne ikke behandle din besked. Prøv igen senere.');
    }
}

async function loadChatHistory() {
    try {
        // Tjek om der allerede er cachet historik, der er mindre end 30 sekunder gammel
        const now = Date.now();
        if (apiCache.history.data && now - apiCache.history.timestamp < 30000) {
            displayChatHistory(apiCache.history.data);
            return;
        }
        
        const response = await fetch(ENDPOINTS.history);
        if (!response.ok) throw new Error('Kunne ikke hente chathistorik');
        
        const data = await response.json();
        
        // Opdater cache
        apiCache.history = { data, timestamp: now };
        
        // Vis historik
        displayChatHistory(data);
    } catch (error) {
        console.error('Fejl ved indlæsning af chathistorik:', error);
        // Vi viser ikke fejlen til brugeren, vi viser bare velkommen-beskeden
        chatContainer.innerHTML = '';
        addMessageToChat('jarvis', 'Hej, jeg er Jarvis! Jeg er din personlige stemmeassistent. Hvordan kan jeg hjælpe dig i dag?');
    }
}

// Separat funktion til visning af historik - bedre separation af ansvar
function displayChatHistory(data) {
    // Ryd eksisterende beskeder
    if (chatContainer) {
        chatContainer.innerHTML = '';
    }
    
    // Tilføj velkomstbesked
    addMessageToChat('jarvis', 'Hej, jeg er Jarvis! Jeg er din personlige stemmeassistent. Hvordan kan jeg hjælpe dig i dag?');
    
    // Tilføj historik
    if (data && data.history && data.history.length > 0) {
        // Brug fragment for batch DOM-opdatering
        const fragment = document.createDocumentFragment();
        
        data.history.forEach(entry => {
            if (entry.user && entry.user.trim()) {
                const userDiv = document.createElement('div');
                userDiv.className = 'user-message p-3 max-w-3/4 self-end my-1';
                userDiv.textContent = entry.user;
                fragment.appendChild(userDiv);
            }
            
            if (entry.jarvis && entry.jarvis.trim()) {
                const jarvisDiv = document.createElement('div');
                jarvisDiv.className = 'bot-message p-3 max-w-3/4 my-1';
                jarvisDiv.textContent = entry.jarvis;
                fragment.appendChild(jarvisDiv);
            }
        });
        
        // Tilføj alle elementer på én gang
        if (chatContainer) {
            chatContainer.appendChild(fragment);
        }
    }
    
    // Scroll til bunden
    requestAnimationFrame(() => {
        scrollToBottom();
    });
}

// UI funktioner
function addMessageToChat(sender, text) {
    if (!text || !text.trim()) return; // Undgå tomme beskeder
    
    // Brug dokumentfragment for at undgå reflow
    const fragment = document.createDocumentFragment();
    
    // Opret besked-element
    const messageDiv = document.createElement('div');
    messageDiv.className = sender === 'user' 
        ? 'user-message p-3 max-w-3/4 self-end my-1'
        : 'bot-message p-3 max-w-3/4 my-1';
    
    const messageText = document.createElement('p');
    messageText.textContent = text;
    messageDiv.appendChild(messageText);
    
    // Tilføj til fragment
    fragment.appendChild(messageDiv);
    
    // Tilføj alt på én gang til DOM
    chatContainer.appendChild(fragment);
    
    // Brug requestAnimationFrame for at sikre jævn scroll animation
    requestAnimationFrame(() => {
        scrollToBottom();
    });
}

function updateStatusUI(isConnected, statusMsg) {
    statusText.textContent = statusMsg;
    
    if (isConnected) {
        statusIndicator.classList.remove('error');
        statusIndicator.classList.add('connected');
    } else {
        statusIndicator.classList.remove('connected');
        statusIndicator.classList.add('error');
    }
}

function scrollToBottom() {
    if (!chatContainer) return;
    
    // Brug translate3d for hardwareacceleration
    chatContainer.style.transform = 'translate3d(0,0,0)';
    
    // Brug scrollTo med behavior: smooth for jævn scrolling
    chatContainer.scrollTo({
        top: chatContainer.scrollHeight,
        behavior: 'smooth'
    });
}

function toggleRecording() {
    if (!isRecording) {
        startVoiceRecognition();
    } else {
        stopVoiceRecognition();
    }
}

// Talegenkendelse
function setupSpeechRecognition() {
    // Tjek om browseren understøtter talegenkendelse
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        addMessageToChat('jarvis', 'Din browser understøtter ikke stemmegenkendelses-API. Prøv at skrive i stedet.');
        voiceButton.disabled = true;
        return null;
    }
    
    // Opret ny talegenkendelsesinstans
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    
    // Konfigurer talegenkendelsen
    recognition.lang = 'da-DK';
    recognition.continuous = false;
    recognition.interimResults = false;
    
    // Event handlers
    recognition.onstart = () => {
        isRecording = true;
        document.body.classList.add('recording-active');
        addMessageToChat('jarvis', 'Lytter...');
    };
    
    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        if (transcript.trim()) {
            userInput.value = transcript;
            isRecording = false;
            document.body.classList.remove('recording-active');
            sendChatMessage(transcript);
        }
    };
    
    recognition.onerror = (event) => {
        console.error('Talegenkendelse fejl:', event.error);
        addMessageToChat('jarvis', 'Jeg kunne ikke høre dig. Prøv igen.');
        isRecording = false;
        document.body.classList.remove('recording-active');
    };
    
    recognition.onend = () => {
        isRecording = false;
        document.body.classList.remove('recording-active');
    };
    
    return recognition;
}

function startVoiceRecognition() {
    if (!recognitionInstance) {
        recognitionInstance = setupSpeechRecognition();
        if (!recognitionInstance) return;
    }
    
    try {
        recognitionInstance.start();
    } catch (error) {
        console.error('Fejl ved start af talegenkendelse:', error);
    }
}

function stopVoiceRecognition() {
    if (recognitionInstance) {
        try {
            recognitionInstance.stop();
        } catch (error) {
            console.error('Fejl ved stop af talegenkendelse:', error);
        }
    }
}

// Indstillinger
function loadSettings() {
    // Indlæs indstillinger fra localStorage
    if (voiceSelection) {
        voiceSelection.value = selectedVoice;
    }
}

function saveSettings() {
    // Gem stemmevalg
    localStorage.setItem('selectedVoice', voiceSelection.value);
}

// Event listeners
function setupEventListeners() {
    // Send besked via formularen - brug debounce
    if (sendButton) {
        sendButton.addEventListener('click', debounce(() => {
            const message = userInput.value.trim();
            if (message) {
                sendChatMessage(message);
            }
        }, 300));
    }
    
    // Send besked ved at trykke enter
    if (userInput) {
        userInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                event.preventDefault();
                const message = userInput.value.trim();
                if (message) {
                    sendChatMessage(message);
                }
            }
        });
    }
    
    // Talegenkendelse - brug debounce for at undgå dobbeltklik
    if (voiceButton) {
        voiceButton.addEventListener('click', debounce(toggleRecording, 500));
    }
    
    // Lyttetilstand - brug debounce for at undgå hurtige skift
    if (listenToggle) {
        listenToggle.addEventListener('change', debounce(toggleListening, 300));
    }
    
    // Stemmevalg - brug debounce for at undgå multiple callback
    if (voiceSelection) {
        voiceSelection.addEventListener('change', debounce(() => {
            selectedVoice = voiceSelection.value;
            saveSettings();
        }, 300));
    }
    
    // Ryd historik
    if (clearHistoryButton) {
        clearHistoryButton.addEventListener('click', debounce(async () => {
            try {
                // Deaktiver knappen under behandling
                clearHistoryButton.disabled = true;
                
                // Send anmodning om at rydde historikken
                const response = await fetch(ENDPOINTS.clearHistory, {
                    method: 'POST'
                });
                
                if (!response.ok) throw new Error('Kunne ikke rydde chathistorik');
                
                // Ryd UI
                chatContainer.innerHTML = '';
                addMessageToChat('jarvis', 'Chathistorikken er ryddet. Hvordan kan jeg hjælpe dig?');
            } catch (error) {
                console.error('Fejl ved rydning af chathistorik:', error);
                addMessageToChat('jarvis', 'Beklager, jeg kunne ikke rydde chathistorikken på grund af en fejl.');
            } finally {
                // Genaktiver knappen
                clearHistoryButton.disabled = false;
            }
        }, 300));
    }
    
    // Theme toggle - brug throttle for at undgå flimren
    if (themeToggle) {
        themeToggle.addEventListener('click', debounce(() => {
            isDarkMode = !isDarkMode;
            document.body.classList.toggle('dark-mode');
            localStorage.setItem('darkMode', isDarkMode.toString());
        }, 300));
    }
    
    // Settings button
    if (settingsButton) {
        settingsButton.addEventListener('click', debounce(() => {
            settingsPanel.classList.add('visible');
        }, 300));
    }
    
    // Close settings button
    if (closeSettingsButton) {
        closeSettingsButton.addEventListener('click', debounce(() => {
            settingsPanel.classList.remove('visible');
        }, 300));
    }
} 
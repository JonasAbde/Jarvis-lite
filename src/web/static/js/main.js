const { createApp } = Vue

createApp({
    data() {
        return {
            messages: [],
            userInput: '',
            isRecording: false,
            ws: null,
            nluConfidence: 0,
            activeModel: 'Danish GPT-2',
            systemLoad: 0,
            isConnected: false,
            reconnectAttempts: 0,
            maxReconnectAttempts: 5
        }
    },
    mounted() {
        this.connectWebSocket()
    },
    methods: {
        connectWebSocket() {
            if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                console.error('Maksimalt antal reconnect forsøg nået')
                return
            }

            this.ws = new WebSocket(`ws://${window.location.host}/ws`)
            
            this.ws.onopen = () => {
                this.isConnected = true
                this.reconnectAttempts = 0
                console.log('WebSocket forbundet')
            }
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data)
                    this.handleWebSocketMessage(data)
                } catch (error) {
                    console.error('Fejl ved parsing af WebSocket besked:', error)
                }
            }
            
            this.ws.onclose = () => {
                this.isConnected = false
                this.reconnectAttempts++
                console.log(`WebSocket lukket - forsøger at reconnecte (forsøg ${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
                setTimeout(() => this.connectWebSocket(), Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000))
            }

            this.ws.onerror = (error) => {
                console.error('WebSocket fejl:', error)
            }
        },
        
        handleWebSocketMessage(data) {
            switch(data.type) {
                case 'message':
                    this.messages.push({
                        type: 'assistant',
                        content: data.content
                    })
                    if (data.nlu_data) {
                        this.nluConfidence = Math.round(data.nlu_data.confidence * 100)
                        this.updateSystemStatus(data.nlu_data)
                    }
                    break
                case 'error':
                    console.error('Server fejl:', data.content)
                    this.messages.push({
                        type: 'error',
                        content: 'Der opstod en fejl: ' + data.content
                    })
                    break
                case 'system_update':
                    this.systemLoad = data.load
                    break
                default:
                    console.log('Ukendt beskedtype:', data.type)
            }
            
            this.$nextTick(() => {
                const chatMessages = document.getElementById('chat-messages')
                chatMessages.scrollTop = chatMessages.scrollHeight
            })
        },
        
        updateSystemStatus(nluData) {
            // Opdater system status baseret på NLU data
            if (nluData.confidence < 0.55) {
                this.systemLoad += 10 // Simuler øget load ved lav confidence
            }
            // Hold load inden for rimelige grænser
            this.systemLoad = Math.min(Math.max(this.systemLoad, 0), 100)
        },
        
        sendMessage() {
            if (!this.userInput.trim()) return
            
            if (!this.isConnected) {
                this.messages.push({
                    type: 'error',
                    content: 'Ikke forbundet til serveren. Prøver at reconnecte...'
                })
                this.connectWebSocket()
                return
            }
            
            // Tilføj brugerens besked til chat
            this.messages.push({
                type: 'user',
                content: this.userInput
            })
            
            // Send til backend via WebSocket
            try {
                this.ws.send(JSON.stringify({
                    type: 'user_message',
                    content: this.userInput
                }))
            } catch (error) {
                console.error('Fejl ved afsendelse af besked:', error)
                this.messages.push({
                    type: 'error',
                    content: 'Kunne ikke sende beskeden. Prøv igen.'
                })
            }
            
            this.userInput = ''
        },
        
        startRecording() {
            if (!navigator.mediaDevices) {
                console.error('MediaDevices API ikke tilgængelig')
                return
            }

            this.isRecording = !this.isRecording
            if (this.isRecording) {
                navigator.mediaDevices.getUserMedia({ audio: true })
                    .then(stream => {
                        const mediaRecorder = new MediaRecorder(stream)
                        const audioChunks = []
                        
                        mediaRecorder.ondataavailable = (event) => {
                            audioChunks.push(event.data)
                        }
                        
                        mediaRecorder.onstop = () => {
                            const audioBlob = new Blob(audioChunks)
                            this.sendAudioToServer(audioBlob)
                        }
                        
                        mediaRecorder.start()
                        setTimeout(() => {
                            mediaRecorder.stop()
                            this.isRecording = false
                            stream.getTracks().forEach(track => track.stop())
                        }, 5000)
                    })
                    .catch(error => {
                        console.error('Fejl ved adgang til mikrofon:', error)
                        this.isRecording = false
                    })
            }
        },
        
        async sendAudioToServer(audioBlob) {
            const formData = new FormData()
            formData.append('audio', audioBlob)
            
            try {
                const response = await fetch('/process-audio', {
                    method: 'POST',
                    body: formData
                })
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`)
                }
                
                const result = await response.json()
                if (result.text) {
                    this.userInput = result.text
                    this.sendMessage()
                }
            } catch (error) {
                console.error('Fejl ved afsendelse af audio:', error)
                this.messages.push({
                    type: 'error',
                    content: 'Kunne ikke behandle lydoptagelsen. Prøv igen.'
                })
            }
        }
    }
}).mount('#app') 
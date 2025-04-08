const messagesDiv = document.getElementById('messages');
const userInput = document.getElementById('user-input');
const pdfUpload = document.getElementById('pdf-upload');
const loadingScreen = document.getElementById('loading');
const historyList = document.getElementById('history-list');
const newChatBtn = document.getElementById('new-chat-btn');

// Chat history management
let currentChatId = null;
let chatHistory = JSON.parse(localStorage.getItem('chatHistory')) || [];

function saveChatHistory() {
    localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
}

function loadChatHistory() {
    historyList.innerHTML = '';
    chatHistory.forEach((chat, index) => {
        const historyItem = document.createElement('div');
        historyItem.classList.add('history-item');
        if (chat.id === currentChatId) {
            historyItem.classList.add('active');
        }
        historyItem.textContent = chat.title || `Chat ${index + 1}`;
        historyItem.addEventListener('click', () => loadChat(chat.id));
        historyList.appendChild(historyItem);
    });
}

function loadChat(chatId) {
    currentChatId = chatId;
    const chat = chatHistory.find(c => c.id === chatId);
    messagesDiv.innerHTML = '';
    if (chat) {
        chat.messages.forEach(msg => {
            addMessage(msg.content, msg.isUser);
        });
    }
    loadChatHistory();
}

function newChat() {
    currentChatId = Date.now().toString();
    chatHistory.push({
        id: currentChatId,
        title: null,
        messages: []
    });
    messagesDiv.innerHTML = '';
    saveChatHistory();
    loadChatHistory();
}

newChatBtn.addEventListener('click', newChat);

// Initialize with a new chat if none exists
if (chatHistory.length === 0) {
    newChat();
} else {
    currentChatId = chatHistory[chatHistory.length - 1].id;
    loadChat(currentChatId);
}

function addMessage(content, isUser = false) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    messageDiv.classList.add(isUser ? 'user-message' : 'bot-message');
    messageDiv.textContent = content;
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;

    // Save to current chat
    const currentChat = chatHistory.find(c => c.id === currentChatId);
    if (currentChat) {
        // Skip "Listening..." messages for chat history title
        if (content !== 'Listening...') {
            currentChat.messages.push({ content, isUser });
            if (isUser && !currentChat.title && content !== 'Listening...') {
                currentChat.title = content.substring(0, 30);
            }
            saveChatHistory();
            loadChatHistory();
        }
    }

    return messageDiv;
}

function addLoadingMessage() {
    const loadingDiv = document.createElement('div');
    loadingDiv.classList.add('loading-message');
    loadingDiv.innerHTML = '<div class="spinner"></div>Loading...';
    messagesDiv.appendChild(loadingDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return loadingDiv;
}

function replaceLoadingWithResponse(loadingDiv, response) {
    const responseDiv = document.createElement('div');
    responseDiv.classList.add('message', 'bot-message');
    responseDiv.textContent = response;
    messagesDiv.replaceChild(responseDiv, loadingDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;

    // Save bot response to current chat
    const currentChat = chatHistory.find(c => c.id === currentChatId);
    if (currentChat) {
        currentChat.messages.push({ content: response, isUser: false });
        saveChatHistory();
        loadChatHistory();
    }

    return responseDiv;
}

function showLoading() {
    loadingScreen.classList.add('active');
}

function hideLoading() {
    loadingScreen.classList.remove('active');
}

function speakText(text) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    utterance.volume = 1.0;
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    window.speechSynthesis.speak(utterance);
}

function uploadPDFs() {
    const files = pdfUpload.files;
    if (files.length === 0) {
        alert('Please select at least one PDF file.');
        return;
    }
    showLoading();
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            return response.text().then(text => {
                throw new Error(`Server error (${response.status}): ${text}`);
            });
        }
        return response.json();
    })
    .then(data => {
        hideLoading();
        if (data.error) {
            addMessage(data.error);
        } else {
            addMessage(data.message);
        }
    })
    .catch(error => {
        hideLoading();
        addMessage('Error uploading PDFs: ' + error.message);
    });
}

function sendMessage() {
    const query = userInput.value.trim();
    if (!query) return;
    addMessage(query, true);
    userInput.value = '';
    const loadingDiv = addLoadingMessage();

    fetch('/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query })
    })
    .then(response => {
        if (!response.ok) {
            return response.text().then(text => {
                throw new Error(`Server error (${response.status}): ${text}`);
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            replaceLoadingWithResponse(loadingDiv, data.error);
        } else {
            replaceLoadingWithResponse(loadingDiv, data.response);
        }
    })
    .catch(error => {
        replaceLoadingWithResponse(loadingDiv, 'Error: ' + error.message);
    });
}

function startSpeech() {
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'en-US';
    recognition.onstart = () => addMessage('Listening...');
    recognition.onresult = (event) => {
        const query = event.results[0][0].transcript;
        addMessage(query, true);
        const loadingDiv = addLoadingMessage();
        fetch('/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        })
        .then(response => {
            if (!response.ok) {
                return response.text().then(text => {
                    throw new Error(`Server error (${response.status}): ${text}`);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                replaceLoadingWithResponse(loadingDiv, data.error);
            } else {
                const responseDiv = replaceLoadingWithResponse(loadingDiv, data.response);
                speakText(data.response);
            }
        })
        .catch(error => {
            replaceLoadingWithResponse(loadingDiv, 'Error: ' + error.message);
        });
    };
    recognition.onerror = (event) => addMessage('Speech recognition error: ' + event.error);
    recognition.start();
}

userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Auto-resize textarea
userInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = `${this.scrollHeight}px`;
});
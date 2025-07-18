document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const statusText = document.getElementById('status-text');
    const statusDot = document.getElementById('status-dot');
    
    // Auto-resize the textarea as content grows
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        
        // Reset if empty
        if (this.value === '') {
            this.style.height = 'auto';
        }
    });
    
    // Send message on button click
    sendButton.addEventListener('click', function() {
        sendMessage();
    });
    
    // Send message on Enter key (but allow Shift+Enter for new lines)
    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Function to send message
    function sendMessage() {
        const message = userInput.value.trim();
        if (message === '') return;
        
        // Add user message to chat
        addMessage(message, 'user');
        
        // Clear input
        userInput.value = '';
        userInput.style.height = 'auto';
        
        // Update status
        updateStatus('thinking', 'Processing query...');
        
        // Disable input while processing
        userInput.disabled = true;
        sendButton.disabled = true;
        
        // Add loading indicator
        const loadingElement = createLoadingElement();
        chatMessages.appendChild(loadingElement);
        
        // Scroll to bottom
        scrollToBottom();
        
        // Send to backend
        fetch('/api/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: message })
        })
        .then(response => response.json())
        .then(data => {
            // Remove loading indicator
            chatMessages.removeChild(loadingElement);
            
            if (data.status === 'success') {
                // Add assistant response to chat
                addMessage(data.result, 'assistant');
            } else {
                // Add error message
                addMessage('Sorry, I encountered an error: ' + data.message, 'system');
            }
            
            // Re-enable input
            userInput.disabled = false;
            sendButton.disabled = false;
            userInput.focus();
            
            // Update status
            updateStatus('online', 'Ready');
            
            // Scroll to bottom
            scrollToBottom();
        })
        .catch(error => {
            // Remove loading indicator
            if (loadingElement.parentNode === chatMessages) {
                chatMessages.removeChild(loadingElement);
            }
            
            // Add error message
            addMessage('Sorry, there was a network error. Please try again.', 'system');
            
            // Re-enable input
            userInput.disabled = false;
            sendButton.disabled = false;
            userInput.focus();
            
            // Update status
            updateStatus('offline', 'Offline - Check connection');
            
            console.error('Error:', error);
            
            // Scroll to bottom
            scrollToBottom();
        });
    }
    
    // Function to add a message to the chat
    function addMessage(content, type) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${type}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // Format code blocks if any
        content = formatCodeBlocks(content);
        
        messageContent.innerHTML = content;
        
        // Add timestamp
        const timestamp = document.createElement('div');
        timestamp.className = 'timestamp';
        timestamp.textContent = getCurrentTime();
        
        messageElement.appendChild(messageContent);
        messageElement.appendChild(timestamp);
        
        chatMessages.appendChild(messageElement);
        
        // Scroll to bottom
        scrollToBottom();
    }
    
    // Function to create loading indicator
    function createLoadingElement() {
        const loadingElement = document.createElement('div');
        loadingElement.className = 'message assistant loading';
        
        const loadingContent = document.createElement('div');
        loadingContent.className = 'loading-dots';
        
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('span');
            loadingContent.appendChild(dot);
        }
        
        loadingElement.appendChild(loadingContent);
        
        return loadingElement;
    }
    
    // Function to update status indicator
    function updateStatus(state, text) {
        statusText.textContent = text;
        statusDot.className = `status-dot ${state}`;
    }
    
    // Function to get current time
    function getCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    // Function to format code blocks in messages
    function formatCodeBlocks(text) {
        // Simple markdown-like formatting for code blocks
        // Replace ```code``` with <pre><code>code</code></pre>
        let formattedText = text;
        
        // Replace ```code``` blocks
        formattedText = formattedText.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        
        // Replace line breaks with <br>
        formattedText = formattedText.replace(/\n/g, '<br>');
        
        return formattedText;
    }
    
    // Function to scroll to bottom of chat
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Initial focus
    userInput.focus();
}); 
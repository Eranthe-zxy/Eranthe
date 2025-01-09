// Message handling functionality
class MessageHandler {
    constructor() {
        this.messageForm = document.getElementById('messageForm');
        this.messageInput = document.getElementById('messageInput');
        this.messageList = document.getElementById('messageList');
        this.lastUpdateTime = null;
        
        // Bind event handlers
        this.messageForm.addEventListener('submit', this.handleSubmit.bind(this));
        
        // Start periodic updates
        this.startPeriodicUpdates();
    }
    
    async handleSubmit(event) {
        event.preventDefault();
        
        const message = this.messageInput.value.trim();
        if (!message) return;
        
        try {
            const response = await this.sendMessage(message);
            if (response.status === 'success') {
                this.messageInput.value = '';
                await this.fetchAndDisplayMessages();
            }
        } catch (error) {
            this.showError('Failed to send message. Please try again.');
            console.error('Error sending message:', error);
        }
    }
    
    async sendMessage(message) {
        const response = await fetch('/messages', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
    
    async fetchAndDisplayMessages() {
        try {
            const response = await fetch('/messages');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.updateMessageList(data.messages);
            this.lastUpdateTime = new Date();
        } catch (error) {
            this.showError('Failed to fetch messages. Please refresh the page.');
            console.error('Error fetching messages:', error);
        }
    }
    
    updateMessageList(messages) {
        // Clear existing messages
        this.messageList.innerHTML = '';
        
        if (!messages || messages.length === 0) {
            this.messageList.innerHTML = '<div class="message">No messages yet. Be the first to send one!</div>';
            return;
        }
        
        // Add messages in reverse chronological order
        messages.forEach(msg => {
            const messageElement = this.createMessageElement(msg);
            this.messageList.appendChild(messageElement);
        });
    }
    
    createMessageElement(message) {
        const div = document.createElement('div');
        div.className = 'message';
        
        const timestamp = new Date(message.timestamp).toLocaleString();
        const author = message.author || 'Anonymous';
        
        div.innerHTML = `
            <div class="message-header">
                <span class="author">${this.escapeHtml(author)}</span>
                <span class="timestamp">${timestamp}</span>
            </div>
            <div class="message-content">${this.escapeHtml(message.content)}</div>
            ${message.github_url ? `
                <div class="message-footer">
                    <a href="${this.escapeHtml(message.github_url)}" target="_blank" rel="noopener noreferrer">
                        View on GitHub
                    </a>
                </div>
            ` : ''}
        `;
        
        return div;
    }
    
    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error';
        errorDiv.textContent = message;
        
        // Remove after 5 seconds
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
        
        // Insert at top of message list
        this.messageList.insertBefore(errorDiv, this.messageList.firstChild);
    }
    
    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
    
    startPeriodicUpdates() {
        // Initial fetch
        this.fetchAndDisplayMessages();
        
        // Update every 30 seconds
        setInterval(() => {
            this.fetchAndDisplayMessages();
        }, 30000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.messageHandler = new MessageHandler();
});

class BankingChatbot {
    constructor() {
        this.currentUser = null;
        this.pendingTransfer = null;
        this.init();
    }

    init() {
        // Check if user is already logged in
        const userInfo = sessionStorage.getItem('userInfo');
        if (userInfo) {
            this.currentUser = JSON.parse(userInfo);
            this.showChatInterface();
        }
    }

    async login(event) {
        event.preventDefault();
        
        const name = document.getElementById('loginName').value.trim();
        const accountNumber = document.getElementById('loginAccount').value.trim();
        const authCode = document.getElementById('loginAuth').value.trim();

        if (!name || !accountNumber || !authCode) {
            this.showAlert('Please fill in all fields', 'error');
            return;
        }

        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: name,
                    account_number: accountNumber,
                    auth_code: authCode
                })
            });

            const data = await response.json();

            if (data.success) {
                this.currentUser = data.user;
                sessionStorage.setItem('userInfo', JSON.stringify(data.user));
                sessionStorage.setItem('token', data.token);
                this.showChatInterface();
                this.showAlert('Login successful!', 'success');
            } else {
                this.showAlert(data.error || 'Login failed', 'error');
            }
        } catch (error) {
            this.showAlert('Network error. Please try again.', 'error');
        }
    }

    async logout() {
        try {
            await fetch('/api/auth/logout', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${sessionStorage.getItem('token')}`
                }
            });
        } catch (error) {
            console.error('Logout error:', error);
        }

        this.currentUser = null;
        sessionStorage.clear();
        this.showLoginForm();
        this.showAlert('Logged out successfully', 'success');
    }

    showLoginForm() {
        document.getElementById('loginForm').classList.remove('hidden');
        document.getElementById('chatInterface').classList.add('hidden');
        document.getElementById('userInfo').classList.add('hidden');
        
        // Clear form
        document.getElementById('loginName').value = '';
        document.getElementById('loginAccount').value = '';
        document.getElementById('loginAuth').value = '';
    }

    showChatInterface() {
        document.getElementById('loginForm').classList.add('hidden');
        document.getElementById('chatInterface').classList.remove('hidden');
        document.getElementById('userInfo').classList.remove('hidden');
        
        // Update user info display
        document.getElementById('userName').textContent = this.currentUser.name;
        document.getElementById('userBalance').textContent = this.currentUser.balance.toFixed(2);
    }

    async sendMessage(event) {
        event.preventDefault();
        
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();
        
        if (!message) return;

        // Add user message to chat
        this.addMessage(message, 'user');
        messageInput.value = '';

        // Show typing indicator
        this.showTypingIndicator();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${sessionStorage.getItem('token')}`
                },
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();
            this.hideTypingIndicator();

            if (data.error) {
                this.addMessage(data.error, 'bot', 'error');
                return;
            }

            // Handle different response types
            if (data.requires_confirmation && data.intent === 'TRANSFER_MONEY') {
                this.pendingTransfer = data.transfer_data;
                this.showTransferModal(data.transfer_data);
                this.addMessage('Please confirm the transfer details in the modal.', 'bot');
            } else {
                this.addMessage(data.message, 'bot');
                
                // Update balance if it changed
                if (data.new_balance !== undefined) {
                    this.currentUser.balance = data.new_balance;
                    document.getElementById('userBalance').textContent = data.new_balance.toFixed(2);
                    sessionStorage.setItem('userInfo', JSON.stringify(this.currentUser));
                }
            }
        } catch (error) {
            this.hideTypingIndicator();
            this.addMessage('Sorry, I encountered an error. Please try again.', 'bot', 'error');
        }
    }

    addMessage(text, sender, type = 'normal') {
        const messagesContainer = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message flex items-start space-x-2';

        const isUser = sender === 'user';
        const iconClass = isUser ? 'fas fa-user' : 'fas fa-robot';
        const bgColor = isUser ? 'bg-green-600' : (type === 'error' ? 'bg-red-600' : 'bg-blue-600');
        const messageBg = isUser ? 'bg-green-100' : (type === 'error' ? 'bg-red-100' : 'bg-blue-100');

        messageDiv.innerHTML = `
            <div class="${bgColor} text-white rounded-full w-8 h-8 flex items-center justify-center text-sm">
                <i class="${iconClass}"></i>
            </div>
            <div class="${messageBg} rounded-lg p-3 max-w-xs">
                <p class="text-sm">${text}</p>
            </div>
        `;

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    showTypingIndicator() {
        document.getElementById('typingIndicator').classList.add('show');
        const chatContainer = document.getElementById('chatMessages');
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    hideTypingIndicator() {
        document.getElementById('typingIndicator').classList.remove('show');
    }

    showTransferModal(transferData) {
        const modal = document.getElementById('transferModal');
        const detailsDiv = document.getElementById('transferDetails');
        
        detailsDiv.innerHTML = `
            <div class="space-y-2">
                <div class="flex justify-between">
                    <span class="text-gray-600">To Account:</span>
                    <span class="font-semibold">${transferData.to_account}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-600">Amount:</span>
                    <span class="font-semibold text-green-600">$${transferData.amount.toFixed(2)}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-600">From:</span>
                    <span class="font-semibold">${this.currentUser.account_number}</span>
                </div>
            </div>
        `;
        
        modal.classList.remove('hidden');
    }

    closeTransferModal() {
        document.getElementById('transferModal').classList.add('hidden');
        this.pendingTransfer = null;
    }

    async confirmTransfer() {
        if (!this.pendingTransfer) return;

        try {
            const response = await fetch('/api/transfer/confirm', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${sessionStorage.getItem('token')}`
                },
                body: JSON.stringify(this.pendingTransfer)
            });

            const data = await response.json();
            this.closeTransferModal();

            if (data.success) {
                this.addMessage(data.message, 'bot');
                this.currentUser.balance = data.new_balance;
                document.getElementById('userBalance').textContent = data.new_balance.toFixed(2);
                sessionStorage.setItem('userInfo', JSON.stringify(this.currentUser));
                this.showAlert('Transfer completed successfully!', 'success');
            } else {
                this.addMessage(data.error, 'bot', 'error');
                this.showAlert(data.error, 'error');
            }
        } catch (error) {
            this.closeTransferModal();
            this.addMessage('Transfer failed. Please try again.', 'bot', 'error');
            this.showAlert('Transfer failed', 'error');
        }
    }

    showAlert(message, type = 'info') {
        const alertContainer = document.getElementById('alertContainer');
        const alertDiv = document.createElement('div');
        
        const colors = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            info: 'bg-blue-500',
            warning: 'bg-yellow-500'
        };

        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            info: 'fas fa-info-circle',
            warning: 'fas fa-exclamation-triangle'
        };

        alertDiv.className = `${colors[type]} text-white px-4 py-3 rounded-lg shadow-lg mb-2 flex items-center space-x-2 transform transition-all duration-300 translate-x-full`;
        alertDiv.innerHTML = `
            <i class="${icons[type]}"></i>
            <span>${message}</span>
            <button onclick="this.parentElement.remove()" class="ml-2 text-white hover:text-gray-200">
                <i class="fas fa-times"></i>
            </button>
        `;

        alertContainer.appendChild(alertDiv);

        // Animate in
        setTimeout(() => {
            alertDiv.classList.remove('translate-x-full');
        }, 100);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentElement) {
                alertDiv.classList.add('translate-x-full');
                setTimeout(() => alertDiv.remove(), 300);
            }
        }, 5000);
    }
}

// Initialize the chatbot
const chatbot = new BankingChatbot();

// Global functions for HTML event handlers
function login(event) {
    chatbot.login(event);
}

function logout() {
    chatbot.logout();
}

function sendMessage(event) {
    chatbot.sendMessage(event);
}

function confirmTransfer() {
    chatbot.confirmTransfer();
}

function closeTransferModal() {
    chatbot.closeTransferModal();
}
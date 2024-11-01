class ChatManager {
    constructor(groupId) {
        this.groupId = groupId;
        this.chatMessages = document.getElementById('chatMessages');
        this.chatForm = document.getElementById('chatForm');
        this.lastMessageId = null;
        this.isRefreshing = false;

        this.initialize();
    }

    initialize() {
        // Set up form submission handler
        this.chatForm.addEventListener('submit', (e) => this.handleSubmit(e));

        // Get initial messages and start refresh cycle
        this.refreshMessages();

        // Set up auto-refresh
        this.startAutoRefresh();
    }

    async handleSubmit(e) {
        e.preventDefault();
        const form = e.target;
        const input = form.querySelector('input[name="message"]');
        const message = input.value.trim();

        if (!message) return;

        const formData = new FormData(form);
        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                input.value = '';
                await this.refreshMessages();
            }
        } catch (error) {
            console.error('Error sending message:', error);
        }
    }

    async refreshMessages() {
        if (this.isRefreshing) return;
        this.isRefreshing = true;

        try {
            const response = await fetch(`/groups/${this.groupId}/get_messages`);
            const messages = await response.json();

            if (messages && messages.length > 0) {
                const latestMessageId = messages[0].id;

                // Only update if we have new messages
                if (latestMessageId !== this.lastMessageId) {
                    this.lastMessageId = latestMessageId;
                    this.updateMessageDisplay(messages);
                }
            }
        } catch (error) {
            console.error('Error refreshing messages:', error);
        } finally {
            this.isRefreshing = false;
        }
    }

    updateMessageDisplay(messages) {
        const messagesHtml = messages
            .reverse()
            .map(message => this.createMessageHTML(message))
            .join('');

        this.chatMessages.innerHTML = `<div class="messages-container">${messagesHtml}</div>`;
        this.scrollToBottom();
    }

    createMessageHTML(message) {
        return `
            <div class="chat-message ${message.is_own ? 'chat-message-own' : ''}" data-message-id="${message.id}">
                <div class="chat-message-content">
                    <div class="chat-message-header">
                        <strong>${message.username}</strong>
                        <small class="text-muted ms-2">${message.timestamp}</small>
                    </div>
                    <div class="chat-message-text">
                        ${message.content}
                    </div>
                </div>
            </div>
        `;
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    startAutoRefresh() {
        setInterval(() => this.refreshMessages(), 1000);
    }
}
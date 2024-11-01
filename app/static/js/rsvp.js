class RSVPManager {
    constructor() {
        this.initializeRSVPButtons();
    }

    initializeRSVPButtons() {
        document.querySelectorAll('.rsvp-button').forEach(button => {
            button.addEventListener('click', (e) => this.handleRSVP(e));
        });
    }

    formatStatus(status) {
        switch(status) {
            case 'going':
                return 'Going';
            case 'not_going':
                return 'Not Going';
            case 'maybe':
                return 'Maybe';
            default:
                return status;
        }
    }

    async handleRSVP(event) {
        event.preventDefault();
        const button = event.currentTarget;
        const sessionId = button.dataset.sessionId;
        const status = button.dataset.status;
        const comment = prompt('Add a comment (optional):');

        try {
            const response = await fetch(`/sessions/${sessionId}/rsvp`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    status: status,
                    comment: comment || ''
                })
            });

            const data = await response.json();

            if (response.ok) {
                // Update RSVP counts
                this.updateRSVPCounts(sessionId, data.counts);

                // Update button states
                this.updateRSVPButtons(sessionId, status);

                // Immediately fetch and update RSVP list
                await this.loadRSVPList(sessionId);

                // Show success message (optional)
                this.showNotification('RSVP updated successfully!', 'success');
            } else {
                this.showNotification(data.error || 'Error updating RSVP', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showNotification('Error updating RSVP', 'error');
        }
    }

    updateRSVPCounts(sessionId, counts) {
        const container = document.querySelector(`#session-${sessionId} .rsvp-counts`);
        if (container) {
            container.innerHTML = `
                <span class="badge bg-success me-2">Going: ${counts.going}</span>
                <span class="badge bg-danger me-2">Not Going: ${counts.not_going}</span>
                <span class="badge bg-warning">Maybe: ${counts.maybe}</span>
            `;
        }
    }

    updateRSVPButtons(sessionId, selectedStatus) {
        const buttons = document.querySelectorAll(`#session-${sessionId} .rsvp-button`);
        buttons.forEach(button => {
            button.classList.remove('active');
            if (button.dataset.status === selectedStatus) {
                button.classList.add('active');
            }
        });
    }

    async loadRSVPList(sessionId) {
        try {
            const response = await fetch(`/sessions/${sessionId}/rsvps`);
            const rsvps = await response.json();

            const container = document.querySelector(`#session-${sessionId} .rsvp-list`);
            if (container) {
                container.innerHTML = rsvps.map(rsvp => `
                    <div class="rsvp-item">
                        <strong>${rsvp.user}</strong>
                        <span class="rsvp-status ${rsvp.status}">${this.formatStatus(rsvp.status)}</span>
                        ${rsvp.comment ? `<p class="rsvp-comment">${rsvp.comment}</p>` : ''}
                        <small class="text-muted">${rsvp.timestamp}</small>
                    </div>
                `).join('');
            }
        } catch (error) {
            console.error('Error loading RSVPs:', error);
        }
    }

    showNotification(message, type = 'success') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
        notification.style.zIndex = '1050';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        // Add to document
        document.body.appendChild(notification);

        // Remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}
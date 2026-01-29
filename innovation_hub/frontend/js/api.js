/**
 * API Client for Innovation Hub
 * Handles all communication with the backend API
 */

class ApiClient {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
    }

    /**
     * Make HTTP request with error handling
     */
    async request(endpoint, options = {}) {
        const url = this.baseUrl + endpoint;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    }

    // Health check
    async healthCheck() {
        return this.request('/api/health');
    }

    // Ideas endpoints
    async getIdeas(filters = {}) {
        const params = new URLSearchParams();

        Object.entries(filters).forEach(([key, value]) => {
            if (value !== null && value !== undefined && value !== '') {
                params.append(key, value);
            }
        });

        const queryString = params.toString();
        const endpoint = queryString ? `/api/ideas?${queryString}` : '/api/ideas';

        return this.request(endpoint);
    }

    async getIdea(id) {
        return this.request(`/api/ideas/${id}`);
    }

    async createIdea(ideaData) {
        return this.request('/api/ideas', {
            method: 'POST',
            body: JSON.stringify(ideaData)
        });
    }

    async updateIdea(id, updates) {
        return this.request(`/api/ideas/${id}`, {
            method: 'PUT',
            body: JSON.stringify(updates)
        });
    }

    async deleteIdea(id) {
        return this.request(`/api/ideas/${id}`, {
            method: 'DELETE'
        });
    }

    async getIdeaStats() {
        return this.request('/api/ideas/stats');
    }

    // Analysis endpoints
    async getAnalysisStats() {
        return this.request('/api/analysis/stats');
    }

    // Categories endpoints
    async getCategories() {
        return this.request('/api/categories');
    }

    async createCategory(categoryData) {
        return this.request('/api/categories', {
            method: 'POST',
            body: JSON.stringify(categoryData)
        });
    }

    // Tags endpoints
    async getTags() {
        return this.request('/api/tags');
    }

    // Comments endpoints
    async getIdeaComments(ideaId) {
        return this.request(`/api/ideas/${ideaId}/comments`);
    }

    async addComment(ideaId, commentData) {
        return this.request(`/api/ideas/${ideaId}/comments`, {
            method: 'POST',
            body: JSON.stringify(commentData)
        });
    }
}

// Create global API client instance
window.api = new ApiClient();

// Helper functions for common operations
window.apiHelpers = {
    /**
     * Process form data and convert to API format
     */
    processIdeaForm(formData) {
        const data = {
            title: formData.get('title').trim(),
            description: formData.get('description').trim(),
            type: formData.get('type'),
            target_group: formData.get('target_group'),
            submitter_email: formData.get('submitter_email').trim(),
            tags: []
        };

        // Process tags
        const tagsInput = formData.get('tags');
        if (tagsInput && tagsInput.trim()) {
            data.tags = tagsInput
                .split(',')
                .map(tag => tag.trim().toLowerCase())
                .filter(tag => tag.length > 0);
        }

        return data;
    },

    /**
     * Format date for display
     */
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString('sv-SE', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    /**
     * Get status display name
     */
    getStatusDisplayName(status) {
        const statusNames = {
            'ny': 'Ny',
            'granskning': 'Granskning',
            'godkänd': 'Godkänd',
            'utveckling': 'Utveckling',
            'implementerad': 'Implementerad',
            'avvisad': 'Avvisad'
        };
        return statusNames[status] || status;
    },

    /**
     * Get type display name
     */
    getTypeDisplayName(type) {
        const typeNames = {
            'idé': 'Idé',
            'problem': 'Problem',
            'behov': 'Behov',
            'förbättring': 'Förbättring'
        };
        return typeNames[type] || type;
    },

    /**
     * Get priority display name
     */
    getPriorityDisplayName(priority) {
        const priorityNames = {
            'låg': 'Låg',
            'medel': 'Medel',
            'hög': 'Hög'
        };
        return priorityNames[priority] || priority;
    },

    /**
     * Get target group display name
     */
    getTargetGroupDisplayName(targetGroup) {
        const targetGroupNames = {
            'medborgare': 'Medborgare',
            'företag': 'Företag',
            'medarbetare': 'Medarbetare',
            'andra organisationer': 'Andra organisationer'
        };
        return targetGroupNames[targetGroup] || targetGroup;
    },

    /**
     * Truncate text for display
     */
    truncateText(text, maxLength = 150) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength).trim() + '...';
    },

    /**
     * Debounce function for search
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};
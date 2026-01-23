/**
 * UI Components and Rendering Logic
 */

window.UI = {
    /**
     * Render statistics cards
     */
    renderStats(stats) {
        const statsGrid = document.getElementById('statsGrid');

        const statusCards = stats.status_distribution.map(item => `
            <div class="stat-card">
                <div class="stat-number">${item.count}</div>
                <div class="stat-label">${apiHelpers.getStatusDisplayName(item.status)}</div>
            </div>
        `).join('');

        const totalCard = `
            <div class="stat-card">
                <div class="stat-number">${stats.total_ideas}</div>
                <div class="stat-label">Totalt Idéer</div>
            </div>
        `;

        statsGrid.innerHTML = totalCard + statusCards;
    },

    /**
     * Render recent ideas
     */
    renderRecentIdeas(ideas) {
        const container = document.getElementById('recentIdeas');

        if (ideas.length === 0) {
            container.innerHTML = '<p style="color: var(--neutral-gray); text-align: center;">Inga idéer att visa</p>';
            return;
        }

        const ideasHtml = ideas.map(idea => this.createIdeaCard(idea, false)).join('');
        container.innerHTML = ideasHtml;

        console.log(`[UI] Rendered ${ideas.length} recent ideas`);

        // Check vote status for all rendered ideas
        setTimeout(() => {
            console.log(`[UI] Checking vote status for ${ideas.length} recent ideas`);

            // First reapply cached vote styles
            if (typeof window.reapplyAllVoteStyles === 'function') {
                window.reapplyAllVoteStyles();
            }

            // Then check for any votes not in cache
            ideas.forEach(idea => {
                if (typeof window.checkVoteStatus === 'function') {
                    window.checkVoteStatus(idea.id);
                } else {
                    console.error('[UI] checkVoteStatus function not found on window!');
                }
            });
        }, 200);
    },

    /**
     * Render ideas list
     */
    renderIdeasList(ideas, containerId = 'ideasList') {
        const container = document.getElementById(containerId);

        if (ideas.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: var(--space-2xl); color: var(--neutral-gray);">
                    <i class="fas fa-search" style="font-size: 3rem; margin-bottom: var(--space-md);"></i>
                    <p>Inga idéer hittades med de valda filtren.</p>
                </div>
            `;
            return;
        }

        const showManageButtons = containerId === 'manageIdeasList';
        const ideasHtml = ideas.map(idea => this.createIdeaCard(idea, showManageButtons)).join('');
        container.innerHTML = ideasHtml;

        console.log(`[UI] Rendered ${ideas.length} ideas in ${containerId}`);

        // Check vote status for all rendered ideas
        setTimeout(() => {
            console.log(`[UI] Checking vote status for ${ideas.length} ideas in ${containerId}`);

            // First reapply cached vote styles
            if (typeof window.reapplyAllVoteStyles === 'function') {
                window.reapplyAllVoteStyles();
            }

            // Then check for any votes not in cache
            ideas.forEach(idea => {
                if (typeof window.checkVoteStatus === 'function') {
                    window.checkVoteStatus(idea.id);
                } else {
                    console.error('[UI] checkVoteStatus function not found on window!');
                }
            });
        }, 200);
    },

    /**
     * Create individual idea card
     */
    createIdeaCard(idea, showManageButtons = false) {
        const tags = idea.tags ? idea.tags.map(tag =>
            `<span class="tag">${tag.name}</span>`
        ).join('') : '';

        const category = idea.category ?
            `<span style="color: ${idea.category.color}"><i class="fas fa-folder"></i> ${idea.category.name}</span>` : '';

        // Always show edit button, only show manage dropdowns when showManageButtons is true
        const editButton = `
            <button class="btn btn-primary" onclick="openEditModal(${idea.id})" style="margin-left: auto;">
                <i class="fas fa-edit"></i> Redigera
            </button>
        `;

        // Voting section
        const voteCount = idea.vote_count || 0;
        const votingSection = `
            <div style="display: flex; align-items: center; gap: var(--space-sm);">
                <button class="btn-vote" onclick="toggleVote(${idea.id})" id="vote-btn-${idea.id}" title="Rösta på denna idé">
                    <i class="fas fa-thumbs-up"></i>
                </button>
                <span id="vote-count-${idea.id}" style="font-weight: bold; color: var(--primary-blue);">${voteCount}</span>
            </div>
        `;

        // Comments button
        const commentsButton = `
            <button class="btn btn-secondary" onclick="toggleComments(${idea.id})" style="padding: var(--space-xs) var(--space-sm);">
                <i class="fas fa-comment"></i> <span id="comment-count-${idea.id}">${idea.comments?.length || 0}</span> kommentarer
            </button>
        `;

        const manageButtons = `
            <div style="margin-top: var(--space-md); padding-top: var(--space-md); border-top: 1px solid var(--light-gray);">
                <div style="display: flex; gap: var(--space-md); align-items: center; flex-wrap: wrap;">
                    ${votingSection}
                    ${commentsButton}
                    ${showManageButtons ? `
                        <select class="form-control" style="width: auto;" onchange="updateIdeaStatus(${idea.id}, this.value)">
                            <option value="">Ändra status</option>
                            <option value="ny" ${idea.status === 'ny' ? 'selected' : ''}>Ny</option>
                            <option value="granskning" ${idea.status === 'granskning' ? 'selected' : ''}>Granskning</option>
                            <option value="godkänd" ${idea.status === 'godkänd' ? 'selected' : ''}>Godkänd</option>
                            <option value="utveckling" ${idea.status === 'utveckling' ? 'selected' : ''}>Utveckling</option>
                            <option value="implementerad" ${idea.status === 'implementerad' ? 'selected' : ''}>Implementerad</option>
                            <option value="avvisad" ${idea.status === 'avvisad' ? 'selected' : ''}>Avvisad</option>
                        </select>
                        <select class="form-control" style="width: auto;" onchange="updateIdeaPriority(${idea.id}, this.value)">
                            <option value="">Ändra prioritet</option>
                            <option value="låg" ${idea.priority === 'låg' ? 'selected' : ''}>Låg</option>
                            <option value="medel" ${idea.priority === 'medel' ? 'selected' : ''}>Medel</option>
                            <option value="hög" ${idea.priority === 'hög' ? 'selected' : ''}>Hög</option>
                        </select>
                    ` : ''}
                    ${editButton}
                </div>

                <!-- Comments section (hidden by default) -->
                <div id="comments-section-${idea.id}" style="display: none; margin-top: var(--space-md);">
                    <div id="comments-list-${idea.id}"></div>
                    <div style="margin-top: var(--space-md);">
                        <textarea
                            id="comment-input-${idea.id}"
                            class="form-control"
                            placeholder="Skriv en kommentar..."
                            rows="3"
                            style="width: 100%; margin-bottom: var(--space-sm);"
                        ></textarea>
                        <button class="btn btn-primary" onclick="submitComment(${idea.id})">
                            <i class="fas fa-paper-plane"></i> Skicka kommentar
                        </button>
                    </div>
                </div>
            </div>
        `;

        return `
            <div class="idea-item">
                <div class="idea-header">
                    <h3 class="idea-title">${idea.title}</h3>
                    <div style="display: flex; gap: var(--space-sm);">
                        <span class="badge badge-${idea.status}">${apiHelpers.getStatusDisplayName(idea.status)}</span>
                        <span class="priority-${idea.priority}">${apiHelpers.getPriorityDisplayName(idea.priority)}</span>
                    </div>
                </div>

                <div class="idea-meta">
                    <span><i class="fas fa-user"></i> ${idea.submitter.name}</span>
                    <span><i class="fas fa-users"></i> ${apiHelpers.getTargetGroupDisplayName(idea.target_group)}</span>
                    <span><i class="fas fa-tag"></i> ${apiHelpers.getTypeDisplayName(idea.type)}</span>
                    <span><i class="fas fa-clock"></i> ${apiHelpers.formatDate(idea.created_at)}</span>
                    ${category}
                </div>

                <div class="idea-description">
                    ${apiHelpers.truncateText(idea.description)}
                </div>

                ${tags ? `<div class="idea-tags">${tags}</div>` : ''}

                ${manageButtons}
            </div>
        `;
    },

    /**
     * Show loading state
     */
    showLoading(containerId) {
        const container = document.getElementById(containerId);
        container.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
            </div>
        `;
    },

    /**
     * Show error message
     */
    showError(containerId, message) {
        const container = document.getElementById(containerId);
        container.innerHTML = `
            <div class="error">
                <i class="fas fa-exclamation-triangle"></i>
                ${message}
            </div>
        `;
    },

    /**
     * Show success message
     */
    showSuccess(elementId, message, autoHide = true) {
        const element = document.getElementById(elementId);
        element.innerHTML = `<i class="fas fa-check-circle"></i> ${message}`;
        element.style.display = 'block';

        if (autoHide) {
            setTimeout(() => {
                element.style.display = 'none';
            }, 5000);
        }
    },

    /**
     * Show error message
     */
    showErrorMessage(elementId, message, autoHide = true) {
        const element = document.getElementById(elementId);
        element.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${message}`;
        element.style.display = 'block';

        if (autoHide) {
            setTimeout(() => {
                element.style.display = 'none';
            }, 8000);
        }
    },

    /**
     * Clear form
     */
    clearForm(formId) {
        const form = document.getElementById(formId);
        form.reset();

        // Clear any validation states
        const controls = form.querySelectorAll('.form-control');
        controls.forEach(control => {
            control.classList.remove('error');
        });
    },

    /**
     * Validate form field
     */
    validateField(fieldId, validator, errorMessage) {
        const field = document.getElementById(fieldId);
        const value = field.value.trim();

        if (!validator(value)) {
            field.classList.add('error');
            return false;
        } else {
            field.classList.remove('error');
            return true;
        }
    },

    /**
     * Tab switching
     */
    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update content sections
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(tabName).classList.add('active');

        // Load content if needed
        this.loadTabContent(tabName);
    },

    /**
     * Load content for specific tabs
     */
    async loadTabContent(tabName) {
        switch (tabName) {
            case 'dashboard':
                await this.loadDashboard();
                break;
            case 'browse':
                await this.loadBrowseIdeas();
                break;
            case 'analysis':
                if (typeof loadAnalysisData === 'function') {
                    await loadAnalysisData();
                }
                break;
            case 'projects':
                if (typeof loadProjectsTab === 'function') {
                    await loadProjectsTab();
                }
                break;
            case 'documents':
                if (typeof loadDocumentsData === 'function') {
                    await loadDocumentsData();
                }
                break;
            case 'strategy':
                if (typeof loadStrategyTab === 'function') {
                    await loadStrategyTab();
                }
                break;
            case 'funding':
                if (typeof loadFundingTab === 'function') {
                    await loadFundingTab();
                }
                break;
        }
    },

    /**
     * Load dashboard content
     */
    async loadDashboard() {
        try {
            // Load 20 most recent ideas
            const ideas = await api.getIdeas({ limit: 20 });
            this.renderRecentIdeas(ideas);
        } catch (error) {
            console.error('Failed to load dashboard:', error);
            this.showError('recentIdeas', 'Kunde inte ladda senaste idéer');
        }
    },

    /**
     * Load browse ideas content
     */
    async loadBrowseIdeas() {
        this.showLoading('ideasList');
        try {
            const ideas = await api.getIdeas();
            this.renderIdeasList(ideas);
        } catch (error) {
            console.error('Failed to load ideas:', error);
            this.showError('ideasList', 'Kunde inte ladda idéer');
        }
    },

    /**
     * Load manage ideas content
     */
    async loadManageIdeas() {
        this.showLoading('manageIdeasList');
        try {
            const ideas = await api.getIdeas();
            this.renderIdeasList(ideas, 'manageIdeasList');
        } catch (error) {
            console.error('Failed to load ideas for management:', error);
            this.showError('manageIdeasList', 'Kunde inte ladda idéer för hantering');
        }
    }
};
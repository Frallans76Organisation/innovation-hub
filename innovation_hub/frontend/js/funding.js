/**
 * Funding Module - Hantering av finansieringsutlysningar
 */

// State
let currentFundingFilters = {
    source: null,
    status: null,
    search: null
};

// =============================================================================
// Tab Loading
// =============================================================================

async function loadFundingTab() {
    console.log('Loading funding tab...');
    await Promise.all([
        loadFundingStats(),
        loadFundingCalls()
    ]);
}

// =============================================================================
// Statistics
// =============================================================================

async function loadFundingStats() {
    try {
        const response = await fetch('/api/funding/stats');
        if (!response.ok) throw new Error('Failed to load funding stats');

        const stats = await response.json();

        // Update stat cards
        const statsContainer = document.getElementById('funding-stats');
        if (statsContainer) {
            statsContainer.innerHTML = `
                <div class="stat-card">
                    <div class="stat-value">${stats.open_calls}</div>
                    <div class="stat-label">Öppna utlysningar</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${stats.upcoming_calls}</div>
                    <div class="stat-label">Kommande</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${formatCurrency(stats.total_budget_available)}</div>
                    <div class="stat-label">Tillgänglig budget</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${stats.total_calls}</div>
                    <div class="stat-label">Totalt</div>
                </div>
            `;
        }

        // Update upcoming deadlines
        const deadlinesContainer = document.getElementById('upcoming-deadlines');
        if (deadlinesContainer) {
            if (stats.upcoming_deadlines && stats.upcoming_deadlines.length > 0) {
                deadlinesContainer.innerHTML = `
                    <h4>Kommande deadlines</h4>
                    <ul class="deadline-list">
                        ${stats.upcoming_deadlines.map(d => `
                            <li class="deadline-item">
                                <span class="deadline-title">${d.title}</span>
                                <span class="deadline-date ${isDeadlineSoon(d.deadline) ? 'deadline-soon' : ''}">${formatDate(d.deadline)}</span>
                                <span class="badge badge-${getSourceColor(d.source)}">${getSourceLabel(d.source)}</span>
                            </li>
                        `).join('')}
                    </ul>
                `;
            } else {
                deadlinesContainer.innerHTML = `
                    <h4>Kommande deadlines</h4>
                    <p style="color: var(--neutral-gray); padding: var(--space-md);">Inga kommande deadlines de närmaste 30 dagarna.</p>
                `;
            }
        }

    } catch (error) {
        console.error('Error loading funding stats:', error);
        // Show error state in stats
        const statsContainer = document.getElementById('funding-stats');
        if (statsContainer) {
            statsContainer.innerHTML = '<div class="error">Kunde inte ladda statistik</div>';
        }
        const deadlinesContainer = document.getElementById('upcoming-deadlines');
        if (deadlinesContainer) {
            deadlinesContainer.innerHTML = `
                <h4>Kommande deadlines</h4>
                <p style="color: var(--error-red);">Kunde inte ladda deadlines</p>
            `;
        }
    }
}

// =============================================================================
// Funding Calls List
// =============================================================================

async function loadFundingCalls(filters = currentFundingFilters) {
    const listContainer = document.getElementById('funding-list');
    if (!listContainer) return;

    listContainer.innerHTML = '<div class="loading">Laddar utlysningar...</div>';

    try {
        // Build query string
        const params = new URLSearchParams();
        if (filters.source) params.append('source', filters.source);
        if (filters.status) params.append('status', filters.status);
        if (filters.search) params.append('search', filters.search);

        const response = await fetch(`/api/funding/?${params.toString()}`);
        if (!response.ok) throw new Error('Failed to load funding calls');

        const calls = await response.json();

        if (calls.length === 0) {
            listContainer.innerHTML = '<div class="empty-state">Inga utlysningar hittades</div>';
            return;
        }

        listContainer.innerHTML = calls.map(call => renderFundingCard(call)).join('');

    } catch (error) {
        console.error('Error loading funding calls:', error);
        listContainer.innerHTML = '<div class="error">Kunde inte ladda utlysningar</div>';
    }
}

function renderFundingCard(call) {
    const statusClass = getStatusClass(call.status);
    const sourceLabel = getSourceLabel(call.source);
    const sourceColor = getSourceColor(call.source);

    return `
        <div class="card funding-card" data-id="${call.id}">
            <div class="card-header">
                <div class="card-title">
                    <h3>${escapeHtml(call.title)}</h3>
                    <div class="card-badges">
                        <span class="badge badge-${sourceColor}">${sourceLabel}</span>
                        <span class="badge badge-${statusClass}">${getStatusLabel(call.status)}</span>
                    </div>
                </div>
                <div class="card-actions">
                    <button class="btn btn-sm btn-secondary" onclick="viewFundingDetails(${call.id})">
                        Detaljer
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteFundingCall(${call.id})">
                        Ta bort
                    </button>
                </div>
            </div>
            <div class="card-body">
                <p class="card-description">${escapeHtml(call.description || 'Ingen beskrivning')}</p>
                <div class="card-meta">
                    ${call.deadline ? `
                        <span class="meta-item ${isDeadlineSoon(call.deadline) ? 'deadline-soon' : ''}">
                            <strong>Deadline:</strong> ${formatDate(call.deadline)}
                        </span>
                    ` : ''}
                    ${call.total_budget ? `
                        <span class="meta-item">
                            <strong>Budget:</strong> ${formatCurrency(call.total_budget)}
                        </span>
                    ` : ''}
                    ${call.min_grant || call.max_grant ? `
                        <span class="meta-item">
                            <strong>Bidrag:</strong> ${formatGrantRange(call.min_grant, call.max_grant)}
                        </span>
                    ` : ''}
                    ${call.co_funding_requirement ? `
                        <span class="meta-item">
                            <strong>Medfinansiering:</strong> ${call.co_funding_requirement}%
                        </span>
                    ` : ''}
                </div>
                ${call.focus_areas && call.focus_areas.length > 0 ? `
                    <div class="card-tags">
                        ${call.focus_areas.map(area => `<span class="tag">${escapeHtml(area)}</span>`).join('')}
                    </div>
                ` : ''}
                ${call.match_count > 0 ? `
                    <div class="card-matches">
                        <span class="match-count">${call.match_count} matchningar</span>
                    </div>
                ` : ''}
            </div>
            ${call.external_url ? `
                <div class="card-footer">
                    <a href="${call.external_url}" target="_blank" class="btn btn-link">
                        Öppna extern länk
                    </a>
                </div>
            ` : ''}
        </div>
    `;
}

// =============================================================================
// CRUD Operations
// =============================================================================

async function createFundingCall(formData) {
    try {
        const data = {
            title: formData.get('title'),
            description: formData.get('description'),
            source: formData.get('source'),
            status: formData.get('status') || 'kommande',
            external_url: formData.get('external_url') || null,
            deadline: formData.get('deadline') || null,
            total_budget: formData.get('total_budget') ? parseFloat(formData.get('total_budget')) : null,
            min_grant: formData.get('min_grant') ? parseFloat(formData.get('min_grant')) : null,
            max_grant: formData.get('max_grant') ? parseFloat(formData.get('max_grant')) : null,
            co_funding_requirement: formData.get('co_funding_requirement') ? parseFloat(formData.get('co_funding_requirement')) : null,
            focus_areas: formData.get('focus_areas') ? formData.get('focus_areas').split(',').map(s => s.trim()).filter(s => s) : [],
            keywords: formData.get('keywords') ? formData.get('keywords').split(',').map(s => s.trim()).filter(s => s) : []
        };

        const response = await fetch('/api/funding/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create funding call');
        }

        // Refresh list and stats
        await Promise.all([loadFundingStats(), loadFundingCalls()]);

        // Reset form
        document.getElementById('funding-form')?.reset();

        showNotification('Utlysning skapad', 'success');

    } catch (error) {
        console.error('Error creating funding call:', error);
        showNotification(`Fel: ${error.message}`, 'error');
    }
}

async function deleteFundingCall(callId) {
    if (!confirm('Är du säker på att du vill ta bort denna utlysning?')) return;

    try {
        const response = await fetch(`/api/funding/${callId}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Failed to delete funding call');

        // Refresh list and stats
        await Promise.all([loadFundingStats(), loadFundingCalls()]);

        showNotification('Utlysning borttagen', 'success');

    } catch (error) {
        console.error('Error deleting funding call:', error);
        showNotification('Kunde inte ta bort utlysning', 'error');
    }
}

async function viewFundingDetails(callId) {
    try {
        const response = await fetch(`/api/funding/${callId}`);
        if (!response.ok) throw new Error('Failed to load funding details');

        const call = await response.json();

        // Show modal with details
        showFundingModal(call);

    } catch (error) {
        console.error('Error loading funding details:', error);
        showNotification('Kunde inte ladda detaljer', 'error');
    }
}

function showFundingModal(call) {
    const modal = document.getElementById('funding-modal');
    if (!modal) return;

    const content = modal.querySelector('.modal-content');
    if (!content) return;

    content.innerHTML = `
        <div class="modal-header">
            <h2>${escapeHtml(call.title)}</h2>
            <button class="modal-close" onclick="closeFundingModal()">&times;</button>
        </div>
        <div class="modal-body">
            <div class="detail-section">
                <h4>Grundinformation</h4>
                <p><strong>Källa:</strong> ${getSourceLabel(call.source)}</p>
                <p><strong>Status:</strong> ${getStatusLabel(call.status)}</p>
                ${call.description ? `<p><strong>Beskrivning:</strong> ${escapeHtml(call.description)}</p>` : ''}
            </div>

            <div class="detail-section">
                <h4>Datum</h4>
                ${call.open_date ? `<p><strong>Öppnar:</strong> ${formatDate(call.open_date)}</p>` : ''}
                ${call.deadline ? `<p><strong>Deadline:</strong> ${formatDate(call.deadline)}</p>` : ''}
                ${call.decision_date ? `<p><strong>Beslut:</strong> ${formatDate(call.decision_date)}</p>` : ''}
            </div>

            <div class="detail-section">
                <h4>Budget</h4>
                ${call.total_budget ? `<p><strong>Total budget:</strong> ${formatCurrency(call.total_budget)}</p>` : ''}
                ${call.min_grant || call.max_grant ? `<p><strong>Bidragsbelopp:</strong> ${formatGrantRange(call.min_grant, call.max_grant)}</p>` : ''}
                ${call.co_funding_requirement ? `<p><strong>Medfinansiering:</strong> ${call.co_funding_requirement}%</p>` : ''}
            </div>

            ${call.focus_areas && call.focus_areas.length > 0 ? `
                <div class="detail-section">
                    <h4>Fokusområden</h4>
                    <div class="tags">${call.focus_areas.map(a => `<span class="tag">${escapeHtml(a)}</span>`).join('')}</div>
                </div>
            ` : ''}

            ${call.eligible_applicants && call.eligible_applicants.length > 0 ? `
                <div class="detail-section">
                    <h4>Berättigade sökande</h4>
                    <ul>${call.eligible_applicants.map(a => `<li>${escapeHtml(a)}</li>`).join('')}</ul>
                </div>
            ` : ''}

            ${call.matches && call.matches.length > 0 ? `
                <div class="detail-section">
                    <h4>Matchningar (${call.matches.length})</h4>
                    <ul class="match-list">
                        ${call.matches.map(m => `
                            <li class="match-item">
                                <span class="match-entity">${m.entity_type === 'idea' ? 'Idé' : 'Projekt'}: ${escapeHtml(m.entity_title || 'Okänd')}</span>
                                ${m.match_score ? `<span class="match-score">${Math.round(m.match_score * 100)}%</span>` : ''}
                            </li>
                        `).join('')}
                    </ul>
                </div>
            ` : ''}

            ${call.external_url ? `
                <div class="detail-section">
                    <a href="${call.external_url}" target="_blank" class="btn btn-primary">Öppna extern länk</a>
                </div>
            ` : ''}
        </div>
    `;

    modal.style.display = 'flex';
}

function closeFundingModal() {
    const modal = document.getElementById('funding-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// =============================================================================
// Filtering
// =============================================================================

function filterFundingBySource(source) {
    currentFundingFilters.source = source || null;
    loadFundingCalls();
    updateFilterButtons('source', source);
}

function filterFundingByStatus(status) {
    currentFundingFilters.status = status || null;
    loadFundingCalls();
    updateFilterButtons('status', status);
}

function searchFunding(query) {
    currentFundingFilters.search = query || null;
    loadFundingCalls();
}

function updateFilterButtons(filterType, activeValue) {
    const buttons = document.querySelectorAll(`.filter-btn[data-filter="${filterType}"]`);
    buttons.forEach(btn => {
        const value = btn.dataset.value;
        btn.classList.toggle('active', value === activeValue || (!activeValue && !value));
    });
}

// =============================================================================
// Helper Functions
// =============================================================================

function formatCurrency(amount) {
    if (!amount) return 'Ej specificerat';
    return new Intl.NumberFormat('sv-SE', {
        style: 'currency',
        currency: 'SEK',
        maximumFractionDigits: 0
    }).format(amount);
}

function formatGrantRange(min, max) {
    if (min && max) {
        return `${formatCurrency(min)} - ${formatCurrency(max)}`;
    } else if (min) {
        return `Från ${formatCurrency(min)}`;
    } else if (max) {
        return `Upp till ${formatCurrency(max)}`;
    }
    return 'Ej specificerat';
}

function formatDate(dateStr) {
    if (!dateStr) return 'Ej specificerat';
    const date = new Date(dateStr);
    return date.toLocaleDateString('sv-SE');
}

function isDeadlineSoon(dateStr) {
    if (!dateStr) return false;
    const deadline = new Date(dateStr);
    const today = new Date();
    const daysUntil = Math.ceil((deadline - today) / (1000 * 60 * 60 * 24));
    return daysUntil <= 14 && daysUntil >= 0;
}

function getSourceLabel(source) {
    const labels = {
        'vinnova': 'Vinnova',
        'eu_horizon': 'EU Horizon',
        'eu_digital': 'EU Digital',
        'regional': 'Regional',
        'other': 'Övrig'
    };
    return labels[source] || source || 'Okänd';
}

function getSourceColor(source) {
    const colors = {
        'vinnova': 'blue',
        'eu_horizon': 'purple',
        'eu_digital': 'green',
        'regional': 'orange',
        'other': 'gray'
    };
    return colors[source] || 'gray';
}

function getStatusLabel(status) {
    const labels = {
        'kommande': 'Kommande',
        'öppen': 'Öppen',
        'stänger_snart': 'Stänger snart',
        'stängd': 'Stängd'
    };
    return labels[status] || status || 'Okänd';
}

function getStatusClass(status) {
    const classes = {
        'kommande': 'info',
        'öppen': 'success',
        'stänger_snart': 'warning',
        'stängd': 'secondary'
    };
    return classes[status] || 'secondary';
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showNotification(message, type = 'info') {
    // Use existing notification system or create simple one
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => notification.remove(), 3000);
}

// =============================================================================
// Initialization
// =============================================================================

function initFunding() {
    // Form submission
    const form = document.getElementById('funding-form');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await createFundingCall(new FormData(form));
        });
    }

    // Search input
    const searchInput = document.getElementById('funding-search');
    if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                searchFunding(e.target.value);
            }, 300);
        });
    }

    // Filter buttons
    document.querySelectorAll('.filter-btn[data-filter="source"]').forEach(btn => {
        btn.addEventListener('click', () => filterFundingBySource(btn.dataset.value));
    });

    document.querySelectorAll('.filter-btn[data-filter="status"]').forEach(btn => {
        btn.addEventListener('click', () => filterFundingByStatus(btn.dataset.value));
    });

    // Close modal on click outside
    const modal = document.getElementById('funding-modal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeFundingModal();
        });
    }
}

// Export functions for global access
window.loadFundingTab = loadFundingTab;
window.loadFundingStats = loadFundingStats;
window.loadFundingCalls = loadFundingCalls;
window.createFundingCall = createFundingCall;
window.deleteFundingCall = deleteFundingCall;
window.viewFundingDetails = viewFundingDetails;
window.closeFundingModal = closeFundingModal;
window.filterFundingBySource = filterFundingBySource;
window.filterFundingByStatus = filterFundingByStatus;
window.searchFunding = searchFunding;

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', initFunding);

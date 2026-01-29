/**
 * Main application logic
 */

// Global state
let currentFilters = {};

// DOM Content Loaded
document.addEventListener('DOMContentLoaded', async function() {
    console.log('Innovation Hub Frontend Loading...');

    // Initialize the application
    try {
        await initializeApp();
        console.log('✅ Frontend loaded successfully');
    } catch (error) {
        console.error('❌ Failed to initialize app:', error);
        showGlobalError('Kunde inte starta applikationen. Kontrollera att API:et körs.');
    }
});

/**
 * Initialize the application
 */
async function initializeApp() {
    // Check API health
    try {
        await api.healthCheck();
        console.log('✅ API is healthy');
    } catch (error) {
        throw new Error(`API är inte tillgängligt: ${error.message}`);
    }

    // Set up event listeners
    setupEventListeners();

    // Load initial dashboard content
    await UI.loadDashboard();

    console.log('🚀 Innovation Hub ready!');
}

/**
 * Set up all event listeners
 */
function setupEventListeners() {
    // Tab navigation
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.addEventListener('click', (e) => {
            const tabName = e.target.closest('.nav-tab').dataset.tab;
            UI.switchTab(tabName);
        });
    });

    // Idea submission form
    const ideaForm = document.getElementById('ideaForm');
    if (ideaForm) {
        ideaForm.addEventListener('submit', handleIdeaSubmission);
    }

    // Filter application
    const applyFiltersBtn = document.getElementById('applyFilters');
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', handleFilterApplication);
    }

    // Search debouncing
    const searchInput = document.getElementById('filterSearch');
    if (searchInput) {
        searchInput.addEventListener('input',
            apiHelpers.debounce(() => handleFilterApplication(), 500)
        );
    }

    // Clear filters on Enter
    const filterInputs = ['filterStatus', 'filterType', 'filterSearch'];
    filterInputs.forEach(inputId => {
        const input = document.getElementById(inputId);
        if (input) {
            input.addEventListener('change', () => {
                // Auto-apply filters when dropdown changes
                if (input.type === 'select-one') {
                    setTimeout(handleFilterApplication, 100);
                }
            });
        }
    });
}

/**
 * Handle idea form submission
 */
async function handleIdeaSubmission(event) {
    event.preventDefault();

    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const successMsg = document.getElementById('submitSuccess');
    const errorMsg = document.getElementById('submitError');

    // Hide previous messages
    successMsg.style.display = 'none';
    errorMsg.style.display = 'none';

    // Validate form
    const isValid = validateIdeaForm(form);
    if (!isValid) {
        UI.showErrorMessage('submitError', 'Vänligen fyll i alla obligatoriska fält korrekt.');
        return;
    }

    // Show loading state
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Skickar...';

    try {
        // Prepare data
        const formData = new FormData(form);
        const ideaData = apiHelpers.processIdeaForm(formData);

        console.log('Submitting idea:', ideaData);

        // Submit to API
        const response = await api.createIdea(ideaData);

        console.log('✅ Idea created:', response);

        // Show success
        UI.showSuccess('submitSuccess', 'Din idé har lämnats in framgångsrikt! Tack för ditt bidrag.');

        // Clear form
        UI.clearForm('ideaForm');

        // Refresh dashboard if it's visible
        if (document.getElementById('dashboard').classList.contains('active')) {
            await UI.loadDashboard();
        }

    } catch (error) {
        console.error('❌ Failed to submit idea:', error);
        UI.showErrorMessage('submitError', `Ett fel uppstod: ${error.message}`);
    } finally {
        // Restore button
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

/**
 * Validate idea submission form
 */
function validateIdeaForm(form) {
    const validators = [
        {
            field: 'title',
            validator: (value) => value.length >= 5 && value.length <= 200,
            error: 'Titel måste vara mellan 5-200 tecken'
        },
        {
            field: 'description',
            validator: (value) => value.length >= 10 && value.length <= 5000,
            error: 'Beskrivning måste vara mellan 10-5000 tecken'
        },
        {
            field: 'type',
            validator: (value) => ['idé', 'problem', 'behov', 'förbättring'].includes(value),
            error: 'Välj en giltig typ'
        },
        {
            field: 'targetGroup',
            validator: (value) => ['medborgare', 'företag', 'medarbetare', 'andra organisationer'].includes(value),
            error: 'Välj en giltig målgrupp'
        },
        {
            field: 'submitterEmail',
            validator: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
            error: 'Ange en giltig e-postadress'
        }
    ];

    let isValid = true;

    validators.forEach(({ field, validator, error }) => {
        const fieldElement = form.querySelector(`[name="${field}"], #${field}`);
        if (fieldElement) {
            const value = fieldElement.value.trim();
            if (!validator(value)) {
                fieldElement.classList.add('error');
                isValid = false;
            } else {
                fieldElement.classList.remove('error');
            }
        }
    });

    return isValid;
}

/**
 * Handle filter application
 */
async function handleFilterApplication() {
    const filters = {
        status: document.getElementById('filterStatus')?.value || '',
        type: document.getElementById('filterType')?.value || '',
        search: document.getElementById('filterSearch')?.value || ''
    };

    currentFilters = filters;

    UI.showLoading('ideasList');

    try {
        const ideas = await api.getIdeas(filters);
        UI.renderIdeasList(ideas);

        // Check vote status for all loaded ideas
        setTimeout(() => {
            // First reapply cached vote styles
            if (typeof window.reapplyAllVoteStyles === 'function') {
                window.reapplyAllVoteStyles();
            }

            // Then check for any votes not in cache
            ideas.forEach(idea => {
                if (typeof window.checkVoteStatus === 'function') {
                    window.checkVoteStatus(idea.id);
                }
            });
        }, 100);
    } catch (error) {
        console.error('Failed to apply filters:', error);
        UI.showError('ideasList', 'Kunde inte tillämpa filter');
    }
}

/**
 * Update idea status (called from manage section)
 */
async function updateIdeaStatus(ideaId, newStatus) {
    if (!newStatus) return;

    try {
        const response = await api.updateIdea(ideaId, { status: newStatus });
        console.log('✅ Status updated:', response);

        // Show success feedback
        showTemporaryMessage(`Status uppdaterad till "${apiHelpers.getStatusDisplayName(newStatus)}"`, 'success');

        // Refresh the manage list
        await UI.loadManageIdeas();

        // Refresh dashboard if visible
        if (document.getElementById('dashboard').classList.contains('active')) {
            await UI.loadDashboard();
        }

    } catch (error) {
        console.error('❌ Failed to update status:', error);
        showTemporaryMessage(`Kunde inte uppdatera status: ${error.message}`, 'error');
    }
}

/**
 * Update idea priority (called from manage section)
 */
async function updateIdeaPriority(ideaId, newPriority) {
    if (!newPriority) return;

    try {
        const response = await api.updateIdea(ideaId, { priority: newPriority });
        console.log('✅ Priority updated:', response);

        // Show success feedback
        showTemporaryMessage(`Prioritet uppdaterad till "${apiHelpers.getPriorityDisplayName(newPriority)}"`, 'success');

        // Refresh the manage list
        await UI.loadManageIdeas();

    } catch (error) {
        console.error('❌ Failed to update priority:', error);
        showTemporaryMessage(`Kunde inte uppdatera prioritet: ${error.message}`, 'error');
    }
}

/**
 * Show temporary message
 */
function showTemporaryMessage(message, type = 'success') {
    const messageDiv = document.createElement('div');
    messageDiv.className = type === 'success' ? 'success' : 'error';
    messageDiv.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'}"></i> ${message}`;
    messageDiv.style.position = 'fixed';
    messageDiv.style.top = '20px';
    messageDiv.style.right = '20px';
    messageDiv.style.zIndex = '1000';
    messageDiv.style.maxWidth = '300px';

    document.body.appendChild(messageDiv);

    setTimeout(() => {
        messageDiv.remove();
    }, 3000);
}

/**
 * Show global error message
 */
function showGlobalError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error';
    errorDiv.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${message}`;
    errorDiv.style.margin = '20px';
    errorDiv.style.textAlign = 'center';

    const main = document.querySelector('.main .container');
    if (main) {
        main.insertAdjacentElement('afterbegin', errorDiv);
    }
}

// Make functions available globally for HTML onclick handlers
window.updateIdeaStatus = updateIdeaStatus;
window.updateIdeaPriority = updateIdeaPriority;
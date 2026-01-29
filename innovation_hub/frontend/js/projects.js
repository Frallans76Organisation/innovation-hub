/**
 * Projects Module
 * Hanterar utvecklingsprojekt och kopplingar till idéer
 */

// =============================================================================
// Project Management
// =============================================================================

/**
 * Ladda projektstatistik
 */
async function loadProjectStats() {
    const container = document.getElementById('projectStats');
    if (!container) return;

    try {
        const response = await fetch('/api/projects/stats');
        if (!response.ok) throw new Error('Kunde inte hämta statistik');

        const stats = await response.json();

        // Formatera budget
        const budgetFormatted = stats.total_budget
            ? new Intl.NumberFormat('sv-SE', { style: 'currency', currency: 'SEK', maximumFractionDigits: 0 }).format(stats.total_budget)
            : '0 kr';

        container.innerHTML = `
            <div class="stat-card">
                <div class="stat-value">${stats.total_projects}</div>
                <div class="stat-label">Totalt antal projekt</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${stats.by_status['pågående'] || 0}</div>
                <div class="stat-label">Pågående projekt</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${stats.ideas_linked}</div>
                <div class="stat-label">Kopplade idéer</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${budgetFormatted}</div>
                <div class="stat-label">Total budget</div>
            </div>
        `;
    } catch (error) {
        console.error('Fel vid laddning av projektstatistik:', error);
        container.innerHTML = `
            <div class="error">
                <i class="fas fa-exclamation-triangle"></i>
                Kunde inte ladda statistik
            </div>
        `;
    }
}

/**
 * Ladda projektlista
 */
async function loadProjects(filters = {}) {
    const container = document.getElementById('projectList');
    if (!container) return;

    container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

    try {
        // Bygg query string
        const params = new URLSearchParams();
        if (filters.status) params.append('status', filters.status);
        if (filters.project_type) params.append('project_type', filters.project_type);
        if (filters.search) params.append('search', filters.search);

        const response = await fetch(`/api/projects/?${params.toString()}`);
        if (!response.ok) throw new Error('Kunde inte hämta projekt');

        const projects = await response.json();

        if (projects.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-folder-open" style="font-size: 3rem; color: var(--neutral-gray); margin-bottom: var(--space-md);"></i>
                    <p>Inga projekt hittades</p>
                    <p style="color: var(--neutral-gray); font-size: 0.9rem;">Skapa ett nytt projekt ovan för att komma igång.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = projects.map(project => createProjectCard(project)).join('');

    } catch (error) {
        console.error('Fel vid laddning av projekt:', error);
        container.innerHTML = `
            <div class="error">
                <i class="fas fa-exclamation-triangle"></i>
                Kunde inte ladda projekt: ${error.message}
            </div>
        `;
    }
}

/**
 * Skapa projektkort
 */
function createProjectCard(project) {
    const statusColors = {
        'föreslagen': '#9b59b6',
        'planering': '#3498db',
        'pågående': '#27ae60',
        'pausad': '#f39c12',
        'avslutad': '#95a5a6',
        'avbruten': '#e74c3c'
    };

    const typeLabels = {
        'intern_utveckling': 'Intern',
        'vinnova': 'Vinnova',
        'eu_finansierad': 'EU',
        'externt_samarbete': 'Externt',
        'förvaltning': 'Förvaltning'
    };

    const statusColor = statusColors[project.status] || '#95a5a6';
    const typeLabel = typeLabels[project.project_type] || project.project_type;

    // Formatera budget
    const budgetDisplay = project.estimated_budget
        ? new Intl.NumberFormat('sv-SE', { style: 'currency', currency: 'SEK', maximumFractionDigits: 0 }).format(project.estimated_budget)
        : '';

    // Formatera datum
    const dateRange = [];
    if (project.planned_start) {
        dateRange.push(new Date(project.planned_start).toLocaleDateString('sv-SE'));
    }
    if (project.planned_end) {
        dateRange.push(new Date(project.planned_end).toLocaleDateString('sv-SE'));
    }

    return `
        <div class="project-card" data-project-id="${project.id}">
            <div class="project-header">
                <div class="project-title-section">
                    <h4 class="project-title">${escapeHtml(project.name)}</h4>
                    <div class="project-badges">
                        <span class="badge" style="background-color: ${statusColor}; color: white;">
                            ${capitalizeFirst(project.status)}
                        </span>
                        <span class="badge badge-outline">${typeLabel}</span>
                        ${project.linked_ideas_count > 0 ? `
                            <span class="badge badge-info">
                                <i class="fas fa-lightbulb"></i> ${project.linked_ideas_count} idéer
                            </span>
                        ` : ''}
                    </div>
                </div>
                <div class="project-actions">
                    <button class="btn btn-sm btn-secondary" onclick="viewProjectDetails(${project.id})" title="Visa detaljer">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-secondary" onclick="editProject(${project.id})" title="Redigera">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteProject(${project.id})" title="Ta bort">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>

            <p class="project-description">${truncateText(project.description, 200)}</p>

            <div class="project-meta">
                ${project.owner_department ? `
                    <span class="meta-item">
                        <i class="fas fa-building"></i> ${escapeHtml(project.owner_department)}
                    </span>
                ` : ''}
                ${project.project_manager ? `
                    <span class="meta-item">
                        <i class="fas fa-user"></i> ${escapeHtml(project.project_manager)}
                    </span>
                ` : ''}
                ${budgetDisplay ? `
                    <span class="meta-item">
                        <i class="fas fa-coins"></i> ${budgetDisplay}
                    </span>
                ` : ''}
                ${dateRange.length > 0 ? `
                    <span class="meta-item">
                        <i class="fas fa-calendar"></i> ${dateRange.join(' - ')}
                    </span>
                ` : ''}
            </div>

            ${project.funding_source ? `
                <div class="project-funding">
                    <i class="fas fa-hand-holding-usd"></i> ${escapeHtml(project.funding_source)}
                </div>
            ` : ''}
        </div>
    `;
}

/**
 * Skapa nytt projekt
 */
async function createProject(formData) {
    const successEl = document.getElementById('projectSuccess');
    const errorEl = document.getElementById('projectError');

    // Dölj tidigare meddelanden
    successEl.style.display = 'none';
    errorEl.style.display = 'none';

    try {
        // Bygg projektdata
        const projectData = {
            name: formData.get('name'),
            description: formData.get('description'),
            project_type: formData.get('project_type'),
            owner_department: formData.get('owner_department') || null,
            project_manager: formData.get('project_manager') || null,
            contact_email: formData.get('contact_email') || null,
            estimated_budget: formData.get('estimated_budget') ? parseFloat(formData.get('estimated_budget')) : null,
            funding_source: formData.get('funding_source') || null,
            planned_start: formData.get('planned_start') || null,
            planned_end: formData.get('planned_end') || null
        };

        const response = await fetch('/api/projects/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(projectData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Kunde inte skapa projekt');
        }

        const project = await response.json();

        // Visa framgångsmeddelande
        successEl.style.display = 'block';

        // Rensa formuläret
        document.getElementById('projectForm').reset();

        // Ladda om projektlistan och statistik
        loadProjects();
        loadProjectStats();

        // Dölj meddelande efter 3 sekunder
        setTimeout(() => {
            successEl.style.display = 'none';
        }, 3000);

        return project;

    } catch (error) {
        console.error('Fel vid skapande av projekt:', error);
        errorEl.textContent = error.message;
        errorEl.style.display = 'block';
        throw error;
    }
}

/**
 * Ta bort projekt
 */
async function deleteProject(projectId) {
    if (!confirm('Är du säker på att du vill ta bort detta projekt? Detta kan inte ångras.')) {
        return;
    }

    try {
        const response = await fetch(`/api/projects/${projectId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Kunde inte ta bort projektet');
        }

        // Ladda om listan och statistik
        loadProjects();
        loadProjectStats();

    } catch (error) {
        console.error('Fel vid borttagning av projekt:', error);
        alert('Kunde inte ta bort projektet: ' + error.message);
    }
}

/**
 * Visa projektdetaljer (placeholder - kan utökas med modal)
 */
async function viewProjectDetails(projectId) {
    try {
        const response = await fetch(`/api/projects/${projectId}`);
        if (!response.ok) throw new Error('Kunde inte hämta projektdetaljer');

        const project = await response.json();

        // Enkel alert för nu - kan ersättas med modal
        let details = `
Projekt: ${project.name}
Status: ${project.status}
Typ: ${project.project_type}
Beskrivning: ${project.description}

Avdelning: ${project.owner_department || 'Ej angiven'}
Projektledare: ${project.project_manager || 'Ej angiven'}
Budget: ${project.estimated_budget ? project.estimated_budget.toLocaleString('sv-SE') + ' SEK' : 'Ej angiven'}

Antal kopplade idéer: ${project.linked_ideas_count}
        `;

        if (project.linked_ideas && project.linked_ideas.length > 0) {
            details += '\n\nKopplade idéer:\n';
            project.linked_ideas.forEach(idea => {
                details += `- ${idea.idea_title} (${idea.relationship_type})\n`;
            });
        }

        alert(details);

    } catch (error) {
        console.error('Fel vid hämtning av projektdetaljer:', error);
        alert('Kunde inte hämta projektdetaljer');
    }
}

/**
 * Redigera projekt (placeholder)
 */
function editProject(projectId) {
    alert('Redigeringsfunktion kommer i nästa version. Projekt-ID: ' + projectId);
}

// =============================================================================
// Hjälpfunktioner
// =============================================================================

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return escapeHtml(text);
    return escapeHtml(text.substring(0, maxLength)) + '...';
}

function capitalizeFirst(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// =============================================================================
// Initialization
// =============================================================================

/**
 * Initialisera projekt-modulen
 */
function initProjects() {
    // Projektformulär
    const projectForm = document.getElementById('projectForm');
    if (projectForm) {
        projectForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(projectForm);
            await createProject(formData);
        });
    }

    // Filter-knapp
    const applyFiltersBtn = document.getElementById('applyProjectFilters');
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', () => {
            const filters = {
                status: document.getElementById('projectFilterStatus')?.value,
                project_type: document.getElementById('projectFilterType')?.value,
                search: document.getElementById('projectFilterSearch')?.value
            };
            loadProjects(filters);
        });
    }

    // Sökfält med debounce
    const searchInput = document.getElementById('projectFilterSearch');
    if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                const filters = {
                    status: document.getElementById('projectFilterStatus')?.value,
                    project_type: document.getElementById('projectFilterType')?.value,
                    search: searchInput.value
                };
                loadProjects(filters);
            }, 500);
        });
    }
}

/**
 * Ladda projektinnehåll
 */
function loadProjectsTab() {
    loadProjectStats();
    loadProjects();
}

// Exportera funktioner globalt
window.loadProjectStats = loadProjectStats;
window.loadProjects = loadProjects;
window.createProject = createProject;
window.deleteProject = deleteProject;
window.viewProjectDetails = viewProjectDetails;
window.editProject = editProject;
window.initProjects = initProjects;
window.loadProjectsTab = loadProjectsTab;

// Initialisera när DOM är redo
document.addEventListener('DOMContentLoaded', initProjects);

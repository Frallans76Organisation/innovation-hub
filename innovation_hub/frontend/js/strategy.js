/**
 * Strategy Module
 * Hanterar strategidokument och alignment-visualisering
 */

// =============================================================================
// Strategy Management
// =============================================================================

/**
 * Ladda strategistatistik
 */
async function loadStrategyStats() {
    const container = document.getElementById('strategyStats');
    if (!container) return;

    try {
        const response = await fetch('/api/strategy/stats');
        if (!response.ok) throw new Error('Kunde inte hämta statistik');

        const stats = await response.json();

        container.innerHTML = `
            <div class="stat-card">
                <div class="stat-value">${stats.total_documents}</div>
                <div class="stat-label">Strategidokument</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${stats.active_count}</div>
                <div class="stat-label">Aktiva mål</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${stats.total_alignments}</div>
                <div class="stat-label">Kopplingar</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${stats.ideas_aligned + stats.projects_aligned}</div>
                <div class="stat-label">Alignade entiteter</div>
            </div>
        `;
    } catch (error) {
        console.error('Fel vid laddning av strategistatistik:', error);
        container.innerHTML = `
            <div class="error">
                <i class="fas fa-exclamation-triangle"></i>
                Kunde inte ladda statistik
            </div>
        `;
    }
}

/**
 * Ladda strategiträd
 */
async function loadStrategyTree() {
    const container = document.getElementById('strategyTree');
    if (!container) return;

    container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

    try {
        const response = await fetch('/api/strategy/tree');
        if (!response.ok) throw new Error('Kunde inte hämta strategiträd');

        const tree = await response.json();

        if (tree.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-sitemap" style="font-size: 3rem; color: var(--neutral-gray); margin-bottom: var(--space-md);"></i>
                    <p>Inga strategidokument hittades</p>
                    <p style="color: var(--neutral-gray); font-size: 0.9rem;">Skapa ett nytt strategidokument ovan för att komma igång.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = renderStrategyTree(tree);

    } catch (error) {
        console.error('Fel vid laddning av strategiträd:', error);
        container.innerHTML = `
            <div class="error">
                <i class="fas fa-exclamation-triangle"></i>
                Kunde inte ladda strategiträd: ${error.message}
            </div>
        `;
    }
}

/**
 * Rendera strategiträd rekursivt
 */
function renderStrategyTree(nodes, level = 0) {
    if (!nodes || nodes.length === 0) return '';

    return nodes.map(node => {
        const typeIcon = getDocumentTypeIcon(node.document_type);
        const levelClass = `level-${node.level}`;
        const hasChildren = node.children && node.children.length > 0;
        const alignmentBadge = node.alignment_count > 0
            ? `<span class="alignment-badge">${node.alignment_count} kopplingar</span>`
            : '';

        return `
            <div class="strategy-node ${levelClass}" data-id="${node.id}">
                <div class="strategy-node-header" onclick="toggleStrategyNode(${node.id})">
                    ${hasChildren ? '<i class="fas fa-chevron-right expand-icon"></i>' : '<span style="width: 20px;"></span>'}
                    <span class="type-icon">${typeIcon}</span>
                    <span class="node-title">${escapeHtml(node.title)}</span>
                    ${alignmentBadge}
                    <div class="node-actions">
                        <button class="btn btn-sm btn-secondary" onclick="viewStrategyDetails(${node.id}, event)" title="Visa detaljer">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-sm btn-secondary" onclick="editStrategy(${node.id}, event)" title="Redigera">
                            <i class="fas fa-edit"></i>
                        </button>
                    </div>
                </div>
                ${hasChildren ? `
                    <div class="strategy-children" id="children-${node.id}" style="display: none;">
                        ${renderStrategyTree(node.children, level + 1)}
                    </div>
                ` : ''}
            </div>
        `;
    }).join('');
}

/**
 * Toggle strateginod (visa/dölj barn)
 */
function toggleStrategyNode(nodeId) {
    const children = document.getElementById(`children-${nodeId}`);
    const node = document.querySelector(`.strategy-node[data-id="${nodeId}"]`);
    const icon = node.querySelector('.expand-icon');

    if (children) {
        const isVisible = children.style.display !== 'none';
        children.style.display = isVisible ? 'none' : 'block';
        if (icon) {
            icon.classList.toggle('expanded', !isVisible);
        }
    }
}

/**
 * Expandera/kollappera alla
 */
function expandAllNodes() {
    document.querySelectorAll('.strategy-children').forEach(el => {
        el.style.display = 'block';
    });
    document.querySelectorAll('.expand-icon').forEach(el => {
        el.classList.add('expanded');
    });
}

function collapseAllNodes() {
    document.querySelectorAll('.strategy-children').forEach(el => {
        el.style.display = 'none';
    });
    document.querySelectorAll('.expand-icon').forEach(el => {
        el.classList.remove('expanded');
    });
}

/**
 * Hämta ikon för dokumenttyp
 */
function getDocumentTypeIcon(docType) {
    const icons = {
        'stratsys_mål': '<i class="fas fa-bullseye" style="color: #3498db;"></i>',
        'policy': '<i class="fas fa-file-contract" style="color: #9b59b6;"></i>',
        'riktlinje': '<i class="fas fa-list-check" style="color: #27ae60;"></i>',
        'vision': '<i class="fas fa-eye" style="color: #e74c3c;"></i>',
        'handlingsplan': '<i class="fas fa-tasks" style="color: #f39c12;"></i>',
        'budgetmål': '<i class="fas fa-coins" style="color: #1abc9c;"></i>'
    };
    return icons[docType] || '<i class="fas fa-file"></i>';
}

/**
 * Visa strategidetaljer
 */
async function viewStrategyDetails(docId, event) {
    if (event) event.stopPropagation();

    try {
        const response = await fetch(`/api/strategy/${docId}`);
        if (!response.ok) throw new Error('Kunde inte hämta detaljer');

        const doc = await response.json();

        // Bygg detaljvy
        let details = `
Titel: ${doc.title}
Typ: ${doc.document_type}
Nivå: ${doc.level}

Beskrivning:
${doc.description || 'Ingen beskrivning'}

Ansvarig avdelning: ${doc.responsible_department || 'Ej angiven'}
Ansvarig person: ${doc.responsible_person || 'Ej angiven'}
Tidsperiod: ${doc.time_period || 'Ej angiven'}

Nyckelord: ${doc.keywords?.join(', ') || 'Inga'}

Antal kopplingar: ${doc.alignment_count}
Antal undermål: ${doc.children_count}
        `;

        if (doc.alignments && doc.alignments.length > 0) {
            details += '\n\nKopplade idéer/projekt:\n';
            doc.alignments.forEach(a => {
                details += `- ${a.entity_type}: ${a.entity_id} (score: ${a.alignment_score?.toFixed(2) || 'N/A'})\n`;
            });
        }

        alert(details);

    } catch (error) {
        console.error('Fel vid hämtning av strategidetaljer:', error);
        alert('Kunde inte hämta detaljer');
    }
}

/**
 * Redigera strategi (placeholder)
 */
function editStrategy(docId, event) {
    if (event) event.stopPropagation();
    alert('Redigeringsfunktion kommer i nästa version. Dokument-ID: ' + docId);
}

/**
 * Skapa nytt strategidokument
 */
async function createStrategyDocument(formData) {
    const successEl = document.getElementById('strategySuccess');
    const errorEl = document.getElementById('strategyError');

    successEl.style.display = 'none';
    errorEl.style.display = 'none';

    try {
        const docData = {
            title: formData.get('title'),
            description: formData.get('description') || null,
            document_type: formData.get('document_type'),
            level: parseInt(formData.get('level')) || 1,
            responsible_department: formData.get('responsible_department') || null,
            responsible_person: formData.get('responsible_person') || null,
            time_period: formData.get('time_period') || null,
            parent_id: formData.get('parent_id') ? parseInt(formData.get('parent_id')) : null,
            keywords: formData.get('keywords')
                ? formData.get('keywords').split(',').map(k => k.trim()).filter(k => k)
                : []
        };

        const response = await fetch('/api/strategy/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(docData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Kunde inte skapa dokument');
        }

        successEl.textContent = 'Strategidokument skapat!';
        successEl.style.display = 'block';

        document.getElementById('strategyForm').reset();

        loadStrategyTree();
        loadStrategyStats();

        setTimeout(() => {
            successEl.style.display = 'none';
        }, 3000);

    } catch (error) {
        console.error('Fel vid skapande av strategidokument:', error);
        errorEl.textContent = error.message;
        errorEl.style.display = 'block';
    }
}

/**
 * Ladda exempelstrategi
 */
async function loadSampleStrategy() {
    if (!confirm('Vill du ladda exempelstrategi? Detta kommer skapa demomål för testning.')) {
        return;
    }

    try {
        // Vi skapar exempeldata via JSON-import
        const sampleData = [
            {
                title: "Vision 2030 - En hållbar och digital kommun",
                description: "Kommunens övergripande vision för de kommande åren",
                document_type: "vision",
                level: 1,
                time_period: "2024-2030",
                responsible_department: "Kommunledning",
                keywords: ["vision", "hållbarhet", "digitalisering", "2030"]
            },
            {
                title: "Strategiskt mål 1: Digital tillgänglighet",
                description: "Alla kommuninvånare ska ha tillgång till digitala tjänster",
                document_type: "stratsys_mål",
                level: 1,
                responsible_department: "IT-avdelningen",
                keywords: ["digitalisering", "tillgänglighet", "e-tjänster"]
            },
            {
                title: "Strategiskt mål 2: Effektiv förvaltning",
                description: "Effektivisera intern administration genom automatisering",
                document_type: "stratsys_mål",
                level: 1,
                responsible_department: "Förvaltningsstöd",
                keywords: ["effektivitet", "automatisering", "administration"]
            },
            {
                title: "IT-policy",
                description: "Riktlinjer för informationssäkerhet och IT-användning",
                document_type: "policy",
                level: 1,
                responsible_department: "IT-avdelningen",
                time_period: "2024-2026",
                keywords: ["IT", "säkerhet", "policy"]
            }
        ];

        let created = 0;
        for (const doc of sampleData) {
            try {
                const response = await fetch('/api/strategy/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(doc)
                });
                if (response.ok) created++;
            } catch (e) {
                console.error('Kunde inte skapa:', doc.title, e);
            }
        }

        alert(`Skapade ${created} exempeldokument!`);
        loadStrategyTree();
        loadStrategyStats();

    } catch (error) {
        console.error('Fel vid laddning av exempelstrategi:', error);
        alert('Kunde inte ladda exempelstrategi: ' + error.message);
    }
}

/**
 * Ladda täckningsrapport
 */
async function loadCoverageReport() {
    const container = document.getElementById('coverageReport');
    if (!container) return;

    try {
        const response = await fetch('/api/strategy/coverage');
        if (!response.ok) throw new Error('Kunde inte hämta täckningsrapport');

        const report = await response.json();

        container.innerHTML = `
            <div class="coverage-summary">
                <div class="coverage-meter">
                    <div class="coverage-bar" style="width: ${report.coverage_percentage}%"></div>
                    <span class="coverage-label">${report.coverage_percentage}% täckning</span>
                </div>
                <p>${report.goals_with_alignments} av ${report.total_goals} mål har kopplingar</p>
            </div>

            ${report.uncovered_goals.length > 0 ? `
                <div class="uncovered-goals">
                    <h4>Mål utan kopplingar</h4>
                    <ul>
                        ${report.uncovered_goals.slice(0, 5).map(g => `
                            <li><span class="level-badge">Nivå ${g.level}</span> ${escapeHtml(g.title)}</li>
                        `).join('')}
                    </ul>
                </div>
            ` : '<p class="success-message">Alla mål har kopplingar!</p>'}
        `;

    } catch (error) {
        console.error('Fel vid laddning av täckningsrapport:', error);
        container.innerHTML = '<p class="error">Kunde inte ladda täckningsrapport</p>';
    }
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

// =============================================================================
// Initialization
// =============================================================================

function initStrategy() {
    // Strategiformulär
    const strategyForm = document.getElementById('strategyForm');
    if (strategyForm) {
        strategyForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(strategyForm);
            await createStrategyDocument(formData);
        });
    }
}

function loadStrategyTab() {
    loadStrategyStats();
    loadStrategyTree();
    loadCoverageReport();
}

// Exportera funktioner globalt
window.loadStrategyStats = loadStrategyStats;
window.loadStrategyTree = loadStrategyTree;
window.toggleStrategyNode = toggleStrategyNode;
window.expandAllNodes = expandAllNodes;
window.collapseAllNodes = collapseAllNodes;
window.viewStrategyDetails = viewStrategyDetails;
window.editStrategy = editStrategy;
window.createStrategyDocument = createStrategyDocument;
window.loadSampleStrategy = loadSampleStrategy;
window.loadCoverageReport = loadCoverageReport;
window.initStrategy = initStrategy;
window.loadStrategyTab = loadStrategyTab;

// Initialisera när DOM är redo
document.addEventListener('DOMContentLoaded', initStrategy);

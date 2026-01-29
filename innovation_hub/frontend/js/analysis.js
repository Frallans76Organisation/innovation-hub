/**
 * Analysis page functionality
 * Handles loading and displaying AI analysis and service mapping statistics
 */

// Load analysis data when analysis tab is activated
async function loadAnalysisData() {
    try {
        console.log('Loading analysis data...');

        if (!window.api) {
            throw new Error('API client not initialized');
        }

        const stats = await window.api.getAnalysisStats();
        console.log('Analysis stats received:', stats);

        if (!stats) {
            throw new Error('No stats returned from API');
        }

        renderServiceMappingOverview(stats.overview);
        renderDevelopmentMatrix(stats.development_needs);
        renderTopMatchedServices(stats.top_matched_services);
        renderGapAnalysis(stats.gaps);
        renderAIConfidence(stats.ai_confidence_avg);

        // Load ideas with AI analysis details for transparency
        const ideas = await window.api.getIdeas({ limit: 20 });
        renderAITransparency(ideas);

        console.log('✅ Analysis data loaded successfully');

    } catch (error) {
        console.error('Failed to load analysis data:', error);
        showAnalysisError('Kunde inte ladda analysdata: ' + error.message);
    }
}

// Render service mapping overview with color-coded cards
function renderServiceMappingOverview(overview) {
    const container = document.getElementById('serviceMappingOverview');

    if (!container) {
        console.error('Container serviceMappingOverview not found');
        return;
    }

    if (!overview) {
        container.innerHTML = '<p class="no-data">Ingen översiktsdata tillgänglig</p>';
        return;
    }

    const html = `
        <div class="service-overview-card existing-service">
            <div class="service-icon">🟢</div>
            <div class="service-count">${overview.existing_service_count}</div>
            <div class="service-label">Befintlig Tjänst</div>
            <div class="service-description">Idéer som kan mötas med befintliga tjänster</div>
        </div>

        <div class="service-overview-card develop-service">
            <div class="service-icon">🟡</div>
            <div class="service-count">${overview.develop_existing_count}</div>
            <div class="service-label">Utveckla Befintlig</div>
            <div class="service-description">Idéer som kräver utveckling av befintliga tjänster</div>
        </div>

        <div class="service-overview-card new-service">
            <div class="service-icon">🔴</div>
            <div class="service-count">${overview.new_service_count}</div>
            <div class="service-label">Ny Tjänst Behövs</div>
            <div class="service-description">Idéer som kräver helt nya tjänster</div>
        </div>

        <div class="service-overview-card total">
            <div class="service-icon">📊</div>
            <div class="service-count">${overview.total_ideas_analyzed}</div>
            <div class="service-label">Totalt Analyserade</div>
            <div class="service-description">Antal idéer med AI-analys</div>
        </div>
    `;

    container.innerHTML = html;
}

// Render development needs matrix
function renderDevelopmentMatrix(needs) {
    const container = document.getElementById('developmentMatrix');

    if (!needs || needs.length === 0) {
        container.innerHTML = '<p class="no-data">Ingen data tillgänglig än</p>';
        return;
    }

    // Group by recommendation and priority
    const matrix = {
        high: { existing: [], develop: [], new: [] },
        medium: { existing: [], develop: [], new: [] },
        low: { existing: [], develop: [], new: [] }
    };

    // Priority mapping from Swedish to English
    const priorityMap = {
        'hög': 'high',
        'medel': 'medium',
        'låg': 'low',
        'high': 'high',
        'medium': 'medium',
        'low': 'low'
    };

    needs.forEach(need => {
        const priorityValue = need.priority || 'medium';
        const priority = priorityMap[priorityValue] || 'medium';
        const rec = need.service_recommendation === 'existing_service' ? 'existing' :
                    need.service_recommendation === 'develop_existing' ? 'develop' : 'new';

        if (matrix[priority] && matrix[priority][rec]) {
            matrix[priority][rec].push(need);
        }
    });

    const html = `
        <div class="matrix-container">
            <div class="matrix-grid">
                <div class="matrix-header"></div>
                <div class="matrix-header">🟢 Befintlig</div>
                <div class="matrix-header">🟡 Utveckla</div>
                <div class="matrix-header">🔴 Ny Tjänst</div>

                <div class="matrix-label">🔥 Hög Prioritet</div>
                <div class="matrix-cell priority-high">${renderMatrixCell(matrix.high.existing)}</div>
                <div class="matrix-cell priority-high">${renderMatrixCell(matrix.high.develop)}</div>
                <div class="matrix-cell priority-high">${renderMatrixCell(matrix.high.new)}</div>

                <div class="matrix-label">⚡ Medel Prioritet</div>
                <div class="matrix-cell priority-medium">${renderMatrixCell(matrix.medium.existing)}</div>
                <div class="matrix-cell priority-medium">${renderMatrixCell(matrix.medium.develop)}</div>
                <div class="matrix-cell priority-medium">${renderMatrixCell(matrix.medium.new)}</div>

                <div class="matrix-label">📋 Låg Prioritet</div>
                <div class="matrix-cell priority-low">${renderMatrixCell(matrix.low.existing)}</div>
                <div class="matrix-cell priority-low">${renderMatrixCell(matrix.low.develop)}</div>
                <div class="matrix-cell priority-low">${renderMatrixCell(matrix.low.new)}</div>
            </div>
        </div>
    `;

    container.innerHTML = html;
}

function renderMatrixCell(ideas) {
    if (!ideas || ideas.length === 0) {
        return '<span class="matrix-empty">0</span>';
    }

    const titles = ideas.slice(0, 3).map(i => `• ${i.title}`).join('<br>');
    const more = ideas.length > 3 ? `<br><small>+${ideas.length - 3} fler</small>` : '';

    return `
        <div class="matrix-bubble">
            <strong>${ideas.length}</strong>
            <div class="matrix-tooltip">
                ${titles}${more}
            </div>
        </div>
    `;
}

// Render top matched services
function renderTopMatchedServices(services) {
    const container = document.getElementById('topMatchedServices');

    if (!services || services.length === 0) {
        container.innerHTML = '<p class="no-data">Ingen data tillgänglig än</p>';
        return;
    }

    const html = services.map((service, index) => `
        <div class="service-match-item">
            <div class="service-rank">#${index + 1}</div>
            <div class="service-details">
                <h4>${service.service_name}</h4>
                <p class="service-category">
                    <i class="fas fa-tag"></i> ${service.service_category || 'Okänd kategori'}
                </p>
                <div class="service-stats">
                    <span class="stat">
                        <i class="fas fa-lightbulb"></i> ${service.idea_count} idéer
                    </span>
                    <span class="stat">
                        <i class="fas fa-percentage"></i> ${(service.avg_match_score * 100).toFixed(0)}% match
                    </span>
                </div>
                ${service.ideas && service.ideas.length > 0 ? `
                    <div class="service-ideas">
                        <strong>Exempel på idéer:</strong>
                        <ul>
                            ${service.ideas.slice(0, 3).map(idea => `
                                <li>
                                    <span class="priority-badge priority-${idea.priority}">${idea.priority}</span>
                                    ${idea.title}
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        </div>
    `).join('');

    container.innerHTML = html;
}

// Render gap analysis
function renderGapAnalysis(gaps) {
    const container = document.getElementById('gapAnalysis');

    if (!gaps || gaps.length === 0) {
        container.innerHTML = '<p class="no-data">Inga gap identifierade - bra jobbat! 🎉</p>';
        return;
    }

    const html = gaps.map(gap => `
        <div class="gap-item">
            <div class="gap-header">
                <div class="gap-keywords">
                    ${gap.area_keywords.map(kw => `<span class="keyword-tag">${kw}</span>`).join('')}
                </div>
                <div class="gap-count">
                    <strong>${gap.idea_count}</strong> idéer
                </div>
            </div>
            <div class="gap-ideas">
                <strong>Exempel på idéer i detta område:</strong>
                <ul>
                    ${gap.sample_ideas.map(idea => `
                        <li>
                            <span class="priority-badge priority-${idea.priority}">${idea.priority}</span>
                            ${idea.title}
                        </li>
                    `).join('')}
                </ul>
            </div>
            <div class="gap-recommendation">
                <i class="fas fa-exclamation-circle"></i>
                <strong>Rekommendation:</strong> Överväg att utveckla en ny tjänst inom detta område
            </div>
        </div>
    `).join('');

    container.innerHTML = html;
}

// Render AI confidence meter
function renderAIConfidence(confidence) {
    const container = document.getElementById('aiConfidence');

    const percentage = (confidence * 100).toFixed(0);
    const level = confidence >= 0.8 ? 'high' : confidence >= 0.6 ? 'medium' : 'low';
    const label = confidence >= 0.8 ? 'Hög tillförlitlighet' :
                  confidence >= 0.6 ? 'Medel tillförlitlighet' : 'Låg tillförlitlighet';
    const color = confidence >= 0.8 ? '#27ae60' : confidence >= 0.6 ? '#f39c12' : '#e74c3c';

    const html = `
        <div class="confidence-meter">
            <div class="confidence-circle" style="border-color: ${color};">
                <div class="confidence-percentage" style="color: ${color};">
                    ${percentage}%
                </div>
                <div class="confidence-label">${label}</div>
            </div>
            <div class="confidence-description">
                <p>
                    AI-analysens genomsnittliga tillförlitlighet baserat på ${confidence >= 0.8 ? 'stark' : 'moderat'} matchning
                    mellan idébeskrivningar och kategoriseringsmönster.
                </p>
                ${confidence < 0.8 ? `
                    <p class="confidence-note">
                        <i class="fas fa-info-circle"></i>
                        Tips: Mer detaljerade idébeskrivningar ger högre analysförtroende.
                    </p>
                ` : ''}
            </div>
        </div>
    `;

    container.innerHTML = html;
}

// Render AI transparency - show how AI analyzed each idea
function renderAITransparency(ideas) {
    const container = document.getElementById('aiTransparency');

    if (!container) {
        console.error('Container aiTransparency not found');
        return;
    }

    if (!ideas || ideas.length === 0) {
        container.innerHTML = '<p class="no-data">Inga idéer med AI-analys tillgängliga än</p>';
        return;
    }

    // Filter ideas that have AI analysis
    const analyzedIdeas = ideas.filter(idea =>
        idea.ai_confidence || idea.service_recommendation
    );

    if (analyzedIdeas.length === 0) {
        container.innerHTML = '<p class="no-data">Inga idéer har AI-analys än</p>';
        return;
    }

    const html = analyzedIdeas.map(idea => {
        const serviceRec = {
            'existing_service': '🟢 Befintlig tjänst kan användas',
            'develop_existing': '🟡 Befintlig tjänst kan utvecklas',
            'new_service': '🔴 Ny tjänst behövs'
        }[idea.service_recommendation] || 'Ej analyserad';

        const impactBadge = {
            'low': '<span class="impact-badge impact-low">Låg påverkan</span>',
            'medium': '<span class="impact-badge impact-medium">Medel påverkan</span>',
            'high': '<span class="impact-badge impact-high">Hög påverkan</span>'
        }[idea.development_impact] || '';

        const confidencePercent = idea.ai_confidence ? (idea.ai_confidence * 100).toFixed(0) : 0;
        const serviceConfidencePercent = idea.service_confidence ? (idea.service_confidence * 100).toFixed(0) : 0;

        // Show top 3 matching services
        let matchingServicesHtml = '';
        if (idea.matching_services && idea.matching_services.length > 0) {
            matchingServicesHtml = `
                <div class="transparency-section">
                    <strong>Matchande tjänster:</strong>
                    <ul class="matching-services-list">
                        ${idea.matching_services.slice(0, 3).map(service => `
                            <li>
                                <span class="service-name">${service.name}</span>
                                <span class="match-score">${(service.match_score * 100).toFixed(0)}% match</span>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            `;
        }

        return `
            <div class="transparency-card">
                <div class="transparency-header">
                    <h4>${idea.title}</h4>
                    <span class="priority-badge priority-${idea.priority}">${idea.priority}</span>
                </div>

                <div class="transparency-body">
                    <div class="transparency-section">
                        <strong>Kategori:</strong>
                        <span>${idea.category ? idea.category.name : 'Ej kategoriserad'}</span>
                    </div>

                    <div class="transparency-section">
                        <strong>AI-genererade taggar:</strong>
                        <div class="tag-list">
                            ${idea.tags.map(tag => `<span class="tag">${tag.name}</span>`).join('')}
                        </div>
                    </div>

                    ${idea.ai_sentiment ? `
                        <div class="transparency-section">
                            <strong>Sentiment:</strong>
                            <span class="sentiment-${idea.ai_sentiment}">${idea.ai_sentiment}</span>
                        </div>
                    ` : ''}

                    <div class="transparency-section">
                        <strong>AI-tillförlitlighet:</strong>
                        <div class="confidence-bar-container">
                            <div class="confidence-bar" style="width: ${confidencePercent}%"></div>
                            <span class="confidence-text">${confidencePercent}%</span>
                        </div>
                    </div>

                    <div class="transparency-section">
                        <strong>Tjänsterekommendation:</strong>
                        <p>${serviceRec}</p>
                        ${impactBadge}
                    </div>

                    ${idea.service_confidence ? `
                        <div class="transparency-section">
                            <strong>Mappning tillförlitlighet:</strong>
                            <div class="confidence-bar-container">
                                <div class="confidence-bar service" style="width: ${serviceConfidencePercent}%"></div>
                                <span class="confidence-text">${serviceConfidencePercent}%</span>
                            </div>
                        </div>
                    ` : ''}

                    ${idea.service_reasoning ? `
                        <div class="transparency-section reasoning">
                            <strong>AI-resonemang:</strong>
                            <p class="reasoning-text">${idea.service_reasoning}</p>
                        </div>
                    ` : ''}

                    ${matchingServicesHtml}

                    ${idea.ai_analysis_notes ? `
                        <div class="transparency-section notes">
                            <strong>Analysnoteringar:</strong>
                            <p class="notes-text">${idea.ai_analysis_notes}</p>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('');

    container.innerHTML = html;
}

// Utility: Show error message
function showAnalysisError(message) {
    const containers = [
        'serviceMappingOverview',
        'developmentMatrix',
        'topMatchedServices',
        'gapAnalysis',
        'aiConfidence',
        'aiTransparency'
    ];

    containers.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.innerHTML = `<p class="error-message"><i class="fas fa-exclamation-triangle"></i> ${message}</p>`;
        }
    });
}

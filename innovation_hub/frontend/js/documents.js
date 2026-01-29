/**
 * Document Management functionality
 * Handles file upload and RAG system interaction
 */

// Load documents data when documents tab is activated
async function loadDocumentsData() {
    try {
        console.log('Loading documents data...');

        await Promise.all([
            loadRAGStats(),
            loadDocumentList()
        ]);

        console.log('✅ Documents data loaded successfully');

    } catch (error) {
        console.error('Failed to load documents data:', error);
        showDocumentsError('Kunde inte ladda dokumentdata: ' + error.message);
    }
}

// Load RAG statistics
async function loadRAGStats() {
    try {
        const response = await fetch('/api/documents/stats');
        const stats = await response.json();

        renderRAGStats(stats);
    } catch (error) {
        console.error('Failed to load RAG stats:', error);
        document.getElementById('ragStats').innerHTML = '<p class="error-message">Kunde inte ladda statistik</p>';
    }
}

// Render RAG statistics
function renderRAGStats(stats) {
    const container = document.getElementById('ragStats');

    const fileTypesHtml = Object.entries(stats.file_types || {})
        .map(([type, count]) => `<li><strong>${type}:</strong> ${count} chunks</li>`)
        .join('');

    const html = `
        <div class="stats-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--space-md);">
            <div class="stat-card">
                <div class="stat-value">${stats.total_chunks}</div>
                <div class="stat-label">Totalt chunks</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${stats.unique_documents}</div>
                <div class="stat-label">Unika dokument</div>
            </div>
        </div>

        ${fileTypesHtml ? `
            <div style="margin-top: var(--space-lg);">
                <strong>Filtyper:</strong>
                <ul style="margin-top: var(--space-sm);">
                    ${fileTypesHtml}
                </ul>
            </div>
        ` : ''}
    `;

    container.innerHTML = html;
}

// Load list of documents
async function loadDocumentList() {
    try {
        const response = await fetch('/api/documents/files');
        const files = await response.json();

        renderDocumentList(files);
    } catch (error) {
        console.error('Failed to load document list:', error);
        document.getElementById('documentList').innerHTML = '<p class="error-message">Kunde inte ladda dokumentlista</p>';
    }
}

// Render document list
function renderDocumentList(files) {
    const container = document.getElementById('documentList');

    if (!files || files.length === 0) {
        container.innerHTML = '<p class="no-data">Inga dokument uppladdade än</p>';
        return;
    }

    // Add "delete all" button at the top
    const headerHtml = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-md);">
            <p style="margin: 0; color: var(--neutral-gray);">
                <strong>${files.length}</strong> filer i databasen
            </p>
            <button class="btn btn-danger" onclick="deleteAllDocuments()" style="padding: var(--space-sm) var(--space-md); opacity: 1; visibility: visible;">
                <i class="fas fa-trash-alt"></i> Rensa alla
            </button>
        </div>
    `;

    const filesHtml = files.map(file => {
        const timestamp = file.first_seen ? new Date(file.first_seen).toLocaleString('sv-SE') : 'Okänd';
        const sourceLabel = file.source === 'service_catalog' ? '🏛️ Tjänstekatalog' : '📄 Dokument';
        const typeLabel = file.service_type === 'municipal_service' ? 'Kommunal tjänst' : file.file_type || 'okänd typ';

        return `
            <div class="document-item" style="background: white; border: 1px solid var(--light-gray); border-radius: var(--border-radius-md); padding: var(--space-md); margin-bottom: var(--space-md);">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex: 1;">
                        <h4 style="margin: 0 0 var(--space-sm) 0;">
                            <i class="fas fa-file-alt"></i> ${file.filename}
                        </h4>
                        <p style="color: var(--neutral-gray); font-size: var(--font-size-sm); margin: 0;">
                            ${sourceLabel} • <strong>${file.chunk_count}</strong> chunks • ${typeLabel}
                            ${timestamp !== 'Okänd' ? `• Uppladdad: ${timestamp}` : ''}
                        </p>
                    </div>
                    <button class="btn btn-danger" onclick="deleteDocument('${file.filename.replace(/'/g, "\\\'")}')" style="padding: var(--space-sm) var(--space-md); white-space: nowrap; opacity: 1; visibility: visible;">
                        <i class="fas fa-trash"></i> Ta bort
                    </button>
                </div>
            </div>
        `;
    }).join('');

    container.innerHTML = headerHtml + filesHtml;
}

// Setup drag and drop
function setupDragAndDrop() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // Highlight drop area when dragging over
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.style.borderColor = 'var(--primary-blue)';
            uploadArea.style.backgroundColor = 'rgba(52, 152, 219, 0.1)';
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.style.borderColor = 'var(--light-gray)';
            uploadArea.style.backgroundColor = 'var(--background-gray)';
        });
    });

    // Handle dropped files
    uploadArea.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        handleFiles(files);
    });

    // Handle file input change
    fileInput.addEventListener('change', (e) => {
        const files = e.target.files;
        handleFiles(files);
    });
}

// Handle file upload
async function handleFiles(files) {
    const progressDiv = document.getElementById('uploadProgress');
    const resultsDiv = document.getElementById('uploadResults');
    const fileNameSpan = document.getElementById('uploadFileName');
    const statusSpan = document.getElementById('uploadStatus');
    const progressBar = document.getElementById('uploadProgressBar');

    resultsDiv.innerHTML = '';

    for (let i = 0; i < files.length; i++) {
        const file = files[i];

        // Validate file size (10MB max)
        if (file.size > 10 * 1024 * 1024) {
            resultsDiv.innerHTML += `
                <div class="error-message" style="margin-bottom: var(--space-md);">
                    <i class="fas fa-exclamation-triangle"></i> ${file.name}: Filen är för stor (max 10MB)
                </div>
            `;
            continue;
        }

        // Show progress
        progressDiv.style.display = 'block';
        fileNameSpan.textContent = file.name;
        statusSpan.textContent = 'Laddar upp...';
        progressBar.style.width = '30%';

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/api/documents/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Upload failed: ${response.statusText}`);
            }

            progressBar.style.width = '70%';
            statusSpan.textContent = 'Bearbetar...';

            const result = await response.json();

            progressBar.style.width = '100%';
            statusSpan.textContent = 'Klar!';

            // Show success message
            resultsDiv.innerHTML += `
                <div class="success-message" style="margin-bottom: var(--space-md);">
                    <i class="fas fa-check-circle"></i> <strong>${result.filename}</strong> uppladdad framgångsrikt!
                    <br><small>${result.chunk_count} chunks • ${(result.file_size / 1024).toFixed(1)} KB</small>
                </div>
            `;

            // Wait a bit before hiding progress
            setTimeout(() => {
                progressDiv.style.display = 'none';
            }, 1000);

        } catch (error) {
            console.error('Upload error:', error);
            progressBar.style.width = '0%';
            statusSpan.textContent = 'Fel uppstod';

            resultsDiv.innerHTML += `
                <div class="error-message" style="margin-bottom: var(--space-md);">
                    <i class="fas fa-exclamation-triangle"></i> ${file.name}: ${error.message}
                </div>
            `;

            setTimeout(() => {
                progressDiv.style.display = 'none';
            }, 2000);
        }
    }

    // Reload document list and stats
    setTimeout(() => {
        loadRAGStats();
        loadDocumentList();
    }, 1500);

    // Reset file input
    document.getElementById('fileInput').value = '';
}

// Delete document
async function deleteDocument(filename) {
    if (!confirm(`Är du säker på att du vill ta bort "${filename}"?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/documents/${encodeURIComponent(filename)}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Failed to delete document');
        }

        const result = await response.json();

        if (result.status === 'success') {
            alert(`✅ ${filename} har tagits bort (${result.chunks_deleted} chunks)`);
            // Reload lists
            loadRAGStats();
            loadDocumentList();
        } else {
            alert(`⚠️ ${filename} kunde inte hittas`);
        }

    } catch (error) {
        console.error('Delete error:', error);
        alert('❌ Kunde inte ta bort dokumentet: ' + error.message);
    }
}

// Delete all documents
async function deleteAllDocuments() {
    if (!confirm('⚠️ Är du säker på att du vill ta bort ALLA dokument från RAG-databasen?\n\nDetta inkluderar tjänstekatalogen och alla uppladdade filer.\n\nDenna åtgärd kan inte ångras!')) {
        return;
    }

    // Double confirmation for safety
    if (!confirm('🚨 SISTA VARNINGEN: Alla dokument kommer att raderas permanent!\n\nKlicka OK för att fortsätta, eller Avbryt för att behålla dokumenten.')) {
        return;
    }

    try {
        const response = await fetch('/api/documents/clear', {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error('Failed to clear documents');
        }

        const result = await response.json();

        if (result.status === 'success') {
            alert('✅ Alla dokument har tagits bort från RAG-databasen');
            // Reload lists
            loadRAGStats();
            loadDocumentList();
        }

    } catch (error) {
        console.error('Clear error:', error);
        alert('❌ Kunde inte ta bort dokumenten: ' + error.message);
    }
}

// Show error message
function showDocumentsError(message) {
    const containers = ['ragStats', 'documentList'];

    containers.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.innerHTML = `<p class="error-message"><i class="fas fa-exclamation-triangle"></i> ${message}</p>`;
        }
    });
}

// Initialize drag and drop when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupDragAndDrop);
} else {
    setupDragAndDrop();
}

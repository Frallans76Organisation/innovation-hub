/**
 * Edit Idea functionality
 * Handles editing existing ideas and triggering re-analysis
 */

// Open edit modal and load idea data
async function openEditModal(ideaId) {
    const modal = document.getElementById('editModal');
    const form = document.getElementById('editIdeaForm');

    // Show modal
    modal.style.display = 'flex';

    // Clear previous messages
    document.getElementById('editError').style.display = 'none';
    document.getElementById('editSuccess').style.display = 'none';

    try {
        // Fetch idea details
        const response = await fetch(`/api/ideas/${ideaId}`);
        if (!response.ok) {
            throw new Error('Failed to load idea');
        }

        const idea = await response.json();

        // Populate form
        document.getElementById('editIdeaId').value = idea.id;
        document.getElementById('editTitle').value = idea.title;
        document.getElementById('editDescription').value = idea.description;
        document.getElementById('editType').value = idea.type;
        document.getElementById('editTargetGroup').value = idea.target_group;
        document.getElementById('editReanalyze').checked = true;

    } catch (error) {
        console.error('Error loading idea:', error);
        const errorDiv = document.getElementById('editError');
        errorDiv.innerHTML = `<i class="fas fa-exclamation-triangle"></i> Kunde inte ladda idén: ${error.message}`;
        errorDiv.style.display = 'block';
    }
}

// Close edit modal
function closeEditModal() {
    const modal = document.getElementById('editModal');
    modal.style.display = 'none';

    // Reset form
    document.getElementById('editIdeaForm').reset();
}

// Close modal when clicking outside
document.addEventListener('click', (e) => {
    const modal = document.getElementById('editModal');
    if (e.target === modal) {
        closeEditModal();
    }
});

// Close modal with Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const modal = document.getElementById('editModal');
        if (modal && modal.style.display === 'flex') {
            closeEditModal();
        }
    }
});

// Handle edit form submission
document.getElementById('editIdeaForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const ideaId = document.getElementById('editIdeaId').value;
    const reanalyze = document.getElementById('editReanalyze').checked;

    const data = {
        title: document.getElementById('editTitle').value,
        description: document.getElementById('editDescription').value,
        type: document.getElementById('editType').value,
        target_group: document.getElementById('editTargetGroup').value
    };

    const errorDiv = document.getElementById('editError');
    const successDiv = document.getElementById('editSuccess');
    const submitBtn = e.target.querySelector('button[type="submit"]');

    try {
        // Disable submit button
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sparar...';

        // Hide previous messages
        errorDiv.style.display = 'none';
        successDiv.style.display = 'none';

        // Update idea
        const response = await fetch(`/api/ideas/${ideaId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update idea');
        }

        // If reanalyze is checked, trigger AI analysis
        if (reanalyze) {
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyserar...';

            const analysisResponse = await fetch(`/api/ideas/${ideaId}/analyze`, {
                method: 'POST'
            });

            if (!analysisResponse.ok) {
                throw new Error('Idea updated but AI analysis failed');
            }
        }

        // Show success message
        successDiv.innerHTML = `
            <i class="fas fa-check-circle"></i>
            Idén har uppdaterats!
            ${reanalyze ? 'AI-analys genomförd.' : ''}
        `;
        successDiv.style.display = 'block';

        // Reset button
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-save"></i> Spara ändringar';

        // Close modal after delay
        setTimeout(() => {
            closeEditModal();
            // Reload ideas list if we're on browse page
            const browseSection = document.getElementById('browse');
            if (browseSection && browseSection.classList.contains('active')) {
                loadIdeasWithFilters();
            }
        }, 1500);

    } catch (error) {
        console.error('Error updating idea:', error);
        errorDiv.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${error.message}`;
        errorDiv.style.display = 'block';

        // Reset button
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-save"></i> Spara ändringar';
    }
});

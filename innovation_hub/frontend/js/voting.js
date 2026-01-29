/**
 * Voting and Comments functionality
 */

// Simple user session (in production, use proper authentication)
const CURRENT_USER_ID = 1; // Mock user ID

// Track voting in progress to prevent double-clicks
const votingInProgress = new Set();

// Track which ideas the user has voted on (client-side cache)
const votedIdeas = new Set();

/**
 * Toggle vote for an idea
 */
async function toggleVote(ideaId) {
    console.log(`[VOTE] Toggling vote for idea ${ideaId}`);

    // Prevent double-voting while request is in progress
    if (votingInProgress.has(ideaId)) {
        console.log(`[VOTE] Already voting on idea ${ideaId}, ignoring`);
        return;
    }

    votingInProgress.add(ideaId);

    try {
        const response = await fetch(`/api/ideas/${ideaId}/vote?user_id=${CURRENT_USER_ID}`, {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error('Failed to toggle vote');
        }

        const result = await response.json();
        console.log(`[VOTE] Result for idea ${ideaId}:`, result);

        // Update vote count immediately
        const voteCountEl = document.getElementById(`vote-count-${ideaId}`);
        if (voteCountEl) {
            voteCountEl.textContent = result.vote_count;
            console.log(`[VOTE] Updated count for idea ${ideaId}: ${result.vote_count}`);
        } else {
            console.warn(`[VOTE] Count element not found for idea ${ideaId}`);
        }

        // Update client-side cache
        if (result.status === 'added') {
            votedIdeas.add(ideaId);
        } else {
            votedIdeas.delete(ideaId);
        }

        // Update button style immediately
        applyVoteButtonStyle(ideaId, result.status === 'added');

        // Note: Removed refreshIdeaFromServer() call as it was causing visual state issues
        // The vote_count is already updated from the toggle API response above

    } catch (error) {
        console.error('[VOTE] Error:', error);
        alert('Kunde inte rösta: ' + error.message);
    } finally {
        // Always remove the lock when done
        votingInProgress.delete(ideaId);
        console.log(`[VOTE] Finished voting on idea ${ideaId}`);
    }
}

/**
 * Refresh a single idea's display from server data
 */
async function refreshIdeaFromServer(ideaId) {
    try {
        console.log(`[VOTE] Refreshing idea ${ideaId} from server`);
        const response = await fetch(`/api/ideas/${ideaId}`);
        if (!response.ok) return;

        const idea = await response.json();

        // Update vote count from fresh server data
        const voteCountEl = document.getElementById(`vote-count-${ideaId}`);
        if (voteCountEl && idea.vote_count !== undefined) {
            voteCountEl.textContent = idea.vote_count;
            console.log(`[VOTE] Synced count for idea ${ideaId}: ${idea.vote_count}`);
        }
    } catch (error) {
        console.error(`[VOTE] Failed to refresh idea ${ideaId}:`, error);
    }
}

/**
 * Apply vote button styling
 */
function applyVoteButtonStyle(ideaId, isVoted) {
    const voteBtn = document.getElementById(`vote-btn-${ideaId}`);
    if (!voteBtn) {
        console.warn(`[VOTE] Button element not found for idea ${ideaId}`);
        return;
    }

    if (isVoted) {
        voteBtn.classList.add('voted');
        // Force inline styles with actual colors (not CSS variables)
        voteBtn.style.setProperty('background', '#004b87', 'important');
        voteBtn.style.setProperty('color', '#ffffff', 'important');
        voteBtn.style.setProperty('border-color', '#004b87', 'important');
        console.log(`[VOTE] Applied voted style to button ${ideaId}`);
    } else {
        voteBtn.classList.remove('voted');
        // Remove inline styles
        voteBtn.style.removeProperty('background');
        voteBtn.style.removeProperty('color');
        voteBtn.style.removeProperty('border-color');
        console.log(`[VOTE] Removed voted style from button ${ideaId}`);
    }
}

/**
 * Check if user has voted and update UI
 */
async function checkVoteStatus(ideaId) {
    console.log(`[VOTE] Checking vote status for idea ${ideaId}`);

    // First check client-side cache
    if (votedIdeas.has(ideaId)) {
        console.log(`[VOTE] Found idea ${ideaId} in client cache as voted`);
        applyVoteButtonStyle(ideaId, true);
        return;
    }

    try {
        const response = await fetch(`/api/ideas/${ideaId}/vote/status?user_id=${CURRENT_USER_ID}`);
        if (!response.ok) {
            console.warn(`[VOTE] Failed to check status for idea ${ideaId}`);
            return;
        }

        const result = await response.json();
        console.log(`[VOTE] Status for idea ${ideaId}:`, result);

        // Update client-side cache
        if (result.has_voted) {
            votedIdeas.add(ideaId);
        }

        // Apply styling
        applyVoteButtonStyle(ideaId, result.has_voted);

    } catch (error) {
        console.error(`[VOTE] Error checking status for idea ${ideaId}:`, error);
    }
}

/**
 * Toggle comments section visibility
 */
async function toggleComments(ideaId) {
    const commentsSection = document.getElementById(`comments-section-${ideaId}`);

    if (commentsSection.style.display === 'none') {
        // Load and show comments
        commentsSection.style.display = 'block';
        await loadComments(ideaId);
    } else {
        // Hide comments
        commentsSection.style.display = 'none';
    }
}

/**
 * Load comments for an idea
 */
async function loadComments(ideaId) {
    try {
        const response = await fetch(`/api/ideas/${ideaId}/comments`);
        if (!response.ok) {
            throw new Error('Failed to load comments');
        }

        const comments = await response.json();
        renderComments(ideaId, comments);

    } catch (error) {
        console.error('Load comments error:', error);
        const commentsList = document.getElementById(`comments-list-${ideaId}`);
        if (commentsList) {
            commentsList.innerHTML = '<p style="color: var(--warning-red);">Kunde inte ladda kommentarer</p>';
        }
    }
}

/**
 * Render comments list
 */
function renderComments(ideaId, comments) {
    const commentsList = document.getElementById(`comments-list-${ideaId}`);

    if (!commentsList) return;

    if (comments.length === 0) {
        commentsList.innerHTML = '<p style="color: var(--neutral-gray); font-style: italic;">Inga kommentarer än. Var först med att kommentera!</p>';
        return;
    }

    const commentsHtml = comments.map(comment => {
        const date = new Date(comment.created_at);
        const formattedDate = date.toLocaleString('sv-SE', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });

        return `
            <div class="comment-item" style="background: var(--background-gray); padding: var(--space-md); border-radius: var(--border-radius-md); margin-bottom: var(--space-sm);">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: var(--space-xs);">
                    <strong style="color: var(--primary-blue);">
                        <i class="fas fa-user-circle"></i> ${comment.author.name}
                    </strong>
                    <span style="color: var(--neutral-gray); font-size: var(--font-size-sm);">
                        ${formattedDate}
                    </span>
                </div>
                <p style="margin: 0; white-space: pre-wrap;">${comment.content}</p>
            </div>
        `;
    }).join('');

    commentsList.innerHTML = commentsHtml;
}

/**
 * Submit a new comment
 */
async function submitComment(ideaId) {
    const commentInput = document.getElementById(`comment-input-${ideaId}`);

    if (!commentInput) return;

    const content = commentInput.value.trim();

    if (!content) {
        alert('Vänligen skriv en kommentar först');
        return;
    }

    try {
        const response = await fetch(`/api/ideas/${ideaId}/comments`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                content: content,
                author_id: CURRENT_USER_ID
            })
        });

        if (!response.ok) {
            throw new Error('Failed to submit comment');
        }

        // Clear input
        commentInput.value = '';

        // Reload comments
        await loadComments(ideaId);

        // Update comment count
        const commentCountEl = document.getElementById(`comment-count-${ideaId}`);
        if (commentCountEl) {
            const currentCount = parseInt(commentCountEl.textContent) || 0;
            commentCountEl.textContent = currentCount + 1;
        }

        // Show success message
        showSuccessMessage('Kommentar skickad!');

    } catch (error) {
        console.error('Submit comment error:', error);
        alert('Kunde inte skicka kommentar: ' + error.message);
    }
}

/**
 * Show success message
 */
function showSuccessMessage(message) {
    // Create temporary success message
    const successDiv = document.createElement('div');
    successDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--success-green);
        color: white;
        padding: var(--space-md);
        border-radius: var(--border-radius-md);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
    `;
    successDiv.innerHTML = `<i class="fas fa-check-circle"></i> ${message}`;

    document.body.appendChild(successDiv);

    // Remove after 3 seconds
    setTimeout(() => {
        successDiv.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => {
            document.body.removeChild(successDiv);
        }, 300);
    }, 3000);
}

// Check vote status for all visible ideas when page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('[VOTE] DOM loaded, will check vote status in 1 second');
    // Will be called after ideas are rendered
    setTimeout(() => {
        const voteButtons = document.querySelectorAll('[id^="vote-btn-"]');
        console.log(`[VOTE] Found ${voteButtons.length} vote buttons to check`);
        voteButtons.forEach(btn => {
            const ideaId = btn.id.replace('vote-btn-', '');
            checkVoteStatus(ideaId);
        });
    }, 1000);
});

/**
 * Reapply all vote button styles from cache
 * Call this after re-rendering idea lists
 */
function reapplyAllVoteStyles() {
    console.log(`[VOTE] Reapplying styles for ${votedIdeas.size} voted ideas`);
    votedIdeas.forEach(ideaId => {
        applyVoteButtonStyle(ideaId, true);
    });
}

// Make functions globally accessible
window.toggleVote = toggleVote;
window.checkVoteStatus = checkVoteStatus;
window.toggleComments = toggleComments;
window.submitComment = submitComment;
window.reapplyAllVoteStyles = reapplyAllVoteStyles;

console.log('[VOTE] Voting module loaded');

// LOTR Data Cloud POC - Frontend JavaScript (Enhanced with character details)

// DOM elements
const fetchBtn = document.getElementById('fetchBtn');
const wipeBtn = document.getElementById('wipeBtn');
const confirmBtn = document.getElementById('confirmBtn');
const confirmQuotesBtn = document.getElementById('confirmQuotesBtn');
const cancelBtn = document.getElementById('cancelBtn');
const spinner = document.getElementById('spinner');
const spinnerText = document.getElementById('spinnerText');
const previewSection = document.getElementById('previewSection');
const characterList = document.getElementById('characterList');
const movieList = document.getElementById('movieList');
const characterSearch = document.getElementById('characterSearch');
const summaryPanel = document.getElementById('summaryPanel');
const logPanel = document.getElementById('logPanel');
const summarySection = document.getElementById('summarySection');
const logSection = document.getElementById('logSection');
const characterDetail = document.getElementById('characterDetail');

// Stats elements
const statCharacters = document.getElementById('statCharacters');
const statQuotes = document.getElementById('statQuotes');
const statMovies = document.getElementById('statMovies');
const statSpeakers = document.getElementById('statSpeakers');

// Tab elements
const tabBtns = document.querySelectorAll('.tab-btn');
const charactersTab = document.getElementById('charactersTab');
const moviesTab = document.getElementById('moviesTab');

// View toggle elements
const fancyViewBtn = document.getElementById('fancyViewBtn');
const jsonViewBtn = document.getElementById('jsonViewBtn');
const fancyView = document.getElementById('fancyView');
const jsonView = document.getElementById('jsonView');
const jsonPreview = document.getElementById('jsonPreview');
const jsonTabBtns = document.querySelectorAll('.json-tab-btn');
const copyJsonBtn = document.getElementById('copyJsonBtn');
const jsonCount = document.getElementById('jsonCount');

// State
let isProcessing = false;
let fetchedData = null;
let selectedCharacterId = null;
let currentJsonView = 'characters';

// Constants
const MAX_CHARACTERS = 10000;
const MAX_LOG_ENTRIES = 50;

/**
 * Escape HTML to prevent XSS attacks
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Toggle between Fancy and JSON views
 */
function setViewMode(mode) {
    if (!fancyView || !jsonView) return;
    
    if (mode === 'fancy') {
        fancyView.style.display = 'block';
        jsonView.style.display = 'none';
        if (fancyViewBtn) fancyViewBtn.classList.add('active');
        if (jsonViewBtn) jsonViewBtn.classList.remove('active');
    } else {
        fancyView.style.display = 'none';
        jsonView.style.display = 'block';
        if (fancyViewBtn) fancyViewBtn.classList.remove('active');
        if (jsonViewBtn) jsonViewBtn.classList.add('active');
        updateJsonPreview(currentJsonView);
    }
}

/**
 * Update JSON preview based on selected tab
 */
function updateJsonPreview(type) {
    if (!fetchedData || !jsonPreview) return;
    
    currentJsonView = type;
    let data;
    let count = 0;
    
    // Update active tab
    if (jsonTabBtns) {
        jsonTabBtns.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.json === type);
        });
    }
    
    switch (type) {
        case 'characters':
            data = fetchedData.characters;
            count = data?.length || 0;
            if (jsonCount) jsonCount.textContent = `${count} characters`;
            break;
        case 'movies':
            data = fetchedData.movies;
            count = data?.length || 0;
            if (jsonCount) jsonCount.textContent = `${count} movies`;
            break;
        case 'stats':
            data = fetchedData.stats;
            if (jsonCount) jsonCount.textContent = 'Summary statistics';
            break;
        case 'all':
            data = {
                stats: fetchedData.stats,
                characters: fetchedData.characters,
                movies: fetchedData.movies
            };
            if (jsonCount) jsonCount.textContent = 'Complete dataset';
            break;
        default:
            data = fetchedData;
    }
    
    jsonPreview.textContent = JSON.stringify(data, null, 2);
}

/**
 * Copy JSON to clipboard
 */
async function copyJsonToClipboard() {
    try {
        await navigator.clipboard.writeText(jsonPreview.textContent);
        copyJsonBtn.textContent = '✅ Copied!';
        copyJsonBtn.classList.add('copied');
        setTimeout(() => {
            copyJsonBtn.textContent = '📋 Copy';
            copyJsonBtn.classList.remove('copied');
        }, 2000);
    } catch (err) {
        console.error('Failed to copy:', err);
        addLogEntry('Failed to copy to clipboard', true);
    }
}

/**
 * Show/hide panels
 */
function showPanel(panel) {
    panel.style.display = 'block';
    panel.classList.add('visible');
}

function hidePanel(panel) {
    panel.style.display = 'none';
    panel.classList.remove('visible');
}

/**
 * Add log entry
 */
function addLogEntry(message, isError = false) {
    showPanel(logSection);
    const entry = document.createElement('div');
    entry.className = 'log-entry' + (isError ? ' error' : '');
    entry.textContent = message; // textContent is safe, no XSS risk
    logPanel.insertBefore(entry, logPanel.firstChild);
    
    while (logPanel.children.length > MAX_LOG_ENTRIES) {
        logPanel.removeChild(logPanel.lastChild);
    }
}

function updateSummary(data) {
    showPanel(summarySection);
    summaryPanel.textContent = JSON.stringify(data, null, 2);
}

function setProcessing(processing, message = 'Processing...') {
    isProcessing = processing;
    fetchBtn.disabled = processing;
    wipeBtn.disabled = processing;
    confirmBtn.disabled = processing;
    if (confirmQuotesBtn) confirmQuotesBtn.disabled = processing;
    cancelBtn.disabled = processing;
    spinner.style.display = processing ? 'block' : 'none';
    spinnerText.textContent = message;
}

/**
 * Show character detail panel
 */
function showCharacterDetail(char) {
    selectedCharacterId = char._id;
    
    const race = char.race && char.race !== 'NaN' ? escapeHtml(char.race) : 'Unknown';
    const gender = char.gender && char.gender !== 'NaN' ? escapeHtml(char.gender) : 'Unknown';
    const realm = char.realm && char.realm !== 'NaN' ? escapeHtml(char.realm) : 'Unknown';
    const birth = char.birth && char.birth !== 'NaN' ? escapeHtml(char.birth) : 'Unknown';
    const death = char.death && char.death !== 'NaN' ? escapeHtml(char.death) : 'Unknown';
    const spouse = char.spouse && char.spouse !== 'NaN' ? escapeHtml(char.spouse) : 'None';
    const height = char.height && char.height !== 'NaN' ? escapeHtml(char.height) : 'Unknown';
    const hair = char.hair && char.hair !== 'NaN' ? escapeHtml(char.hair) : 'Unknown';
    const quoteCount = char.quoteCount || 0;
    const charName = escapeHtml(char.name || 'Unknown');
    
    // Build quotes HTML safely
    let quotesHtml = '';
    if (char.sampleQuotes && char.sampleQuotes.length > 0) {
        quotesHtml = char.sampleQuotes.map(q => {
            const dialog = escapeHtml(q.dialog || '');
            const movie = escapeHtml(q.movie || 'Unknown');
            return `
                <div class="quote-item">
                    <div class="quote-text">"${dialog}"</div>
                    <div class="quote-movie">— ${movie}</div>
                </div>
            `;
        }).join('');
    } else {
        quotesHtml = '<p class="no-quotes">This character has no recorded quotes in the films.</p>';
    }
    
    // Build detail panel HTML with escaped content
    characterDetail.innerHTML = `
        <div class="detail-header">
            <h3>${charName}</h3>
            <button class="close-detail" onclick="closeCharacterDetail()">✕</button>
        </div>
        
        <div class="detail-stats">
            <div class="detail-stat">
                <span class="stat-icon">🧝</span>
                <span class="stat-value">${race}</span>
                <span class="stat-name">Race</span>
            </div>
            <div class="detail-stat">
                <span class="stat-icon">👤</span>
                <span class="stat-value">${gender}</span>
                <span class="stat-name">Gender</span>
            </div>
            <div class="detail-stat">
                <span class="stat-icon">🏰</span>
                <span class="stat-value">${realm}</span>
                <span class="stat-name">Realm</span>
            </div>
            <div class="detail-stat">
                <span class="stat-icon">💬</span>
                <span class="stat-value">${quoteCount}</span>
                <span class="stat-name">Quotes</span>
            </div>
        </div>
        
        <div class="detail-info">
            <div class="info-row"><strong>Birth:</strong> ${birth}</div>
            <div class="info-row"><strong>Death:</strong> ${death}</div>
            <div class="info-row"><strong>Spouse:</strong> ${spouse}</div>
            <div class="info-row"><strong>Height:</strong> ${height}</div>
            <div class="info-row"><strong>Hair:</strong> ${hair}</div>
            ${char.wikiUrl ? `<div class="info-row"><a href="${escapeHtml(char.wikiUrl)}" target="_blank" rel="noopener noreferrer">📖 View on Wiki</a></div>` : ''}
        </div>
        
        <div class="detail-quotes">
            <h4>💬 Quotes (${quoteCount})</h4>
            <div class="quotes-list">
                ${quotesHtml}
            </div>
        </div>
    `;
    
    characterDetail.style.display = 'block';
    characterDetail.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Close character detail
 */
function closeCharacterDetail() {
    characterDetail.style.display = 'none';
    selectedCharacterId = null;
}

// Make it globally accessible
window.closeCharacterDetail = closeCharacterDetail;

/**
 * Render character list
 */
function renderCharacters(characters, filter = '') {
    const filtered = filter 
        ? characters.filter(c => {
            const search = filter.toLowerCase();
            return (c.name && c.name.toLowerCase().includes(search)) ||
                   (c.race && c.race.toLowerCase().includes(search)) ||
                   (c.realm && c.realm.toLowerCase().includes(search));
        })
        : characters;
    
    // Sort: characters with quotes first, then alphabetically
    filtered.sort((a, b) => {
        if ((b.quoteCount || 0) !== (a.quoteCount || 0)) {
            return (b.quoteCount || 0) - (a.quoteCount || 0);
        }
        return (a.name || '').localeCompare(b.name || '');
    });
    
    characterList.innerHTML = filtered.map((char, index) => {
        const race = char.race && char.race !== 'NaN' ? escapeHtml(char.race) : 'Unknown';
        const realm = char.realm && char.realm !== 'NaN' ? escapeHtml(char.realm) : '';
        const quoteCount = char.quoteCount || 0;
        const quoteClass = quoteCount > 0 ? '' : 'none';
        const quoteText = quoteCount > 0 ? `${quoteCount} quotes` : 'No quotes';
        const selected = char._id === selectedCharacterId ? 'selected' : '';
        const charName = escapeHtml(char.name || 'Unknown');
        
        let details = race;
        if (realm) details += ` • ${escapeHtml(realm)}`;
        
        return `
            <div class="character-item ${selected}" data-index="${index}" onclick="window.selectCharacter(${index})">
                <div class="char-info">
                    <div class="char-name">${charName}</div>
                    <div class="char-details">${details}</div>
                </div>
                <div class="char-quotes ${quoteClass}">${quoteText}</div>
            </div>
        `;
    }).join('');
    
    // Store filtered list for click handling
    window.filteredCharacters = filtered;
    
    characterSearch.placeholder = `🔍 Search ${filtered.length} characters...`;
}

// Global click handler
window.selectCharacter = function(index) {
    if (window.filteredCharacters && window.filteredCharacters[index]) {
        showCharacterDetail(window.filteredCharacters[index]);
    }
};

/**
 * Render movie list
 */
function renderMovies(movies) {
    movieList.innerHTML = movies.map(movie => {
        const runtime = movie.runtimeInMinutes ? `${movie.runtimeInMinutes} min` : 'N/A';
        const budget = movie.budgetInMillions ? `$${movie.budgetInMillions}M budget` : '';
        const awards = movie.academyAwardWins ? `${movie.academyAwardWins} Academy Awards` : '';
        const movieName = escapeHtml(movie.name || 'Unknown');
        
        return `
            <div class="movie-item">
                <div class="movie-name">${movieName}</div>
                <div class="movie-stats">
                    <span>🎬 ${runtime}</span>
                    ${budget ? `<span>💰 ${budget}</span>` : ''}
                    ${awards ? `<span>🏆 ${awards}</span>` : ''}
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Set up tabs
 */
function setupTabs() {
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            const tabName = btn.dataset.tab;
            if (tabName === 'characters') {
                charactersTab.classList.add('active');
                moviesTab.classList.remove('active');
            } else {
                moviesTab.classList.add('active');
                charactersTab.classList.remove('active');
            }
        });
    });
}

/**
 * Step 1: Fetch data
 */
async function handleFetch() {
    if (isProcessing) return;
    
    addLogEntry('📜 Speak, friend, and enter... Fetching from The One API');
    setProcessing(true, 'Fetching characters, quotes, and movies...');
    
    hidePanel(previewSection);
    hidePanel(summarySection);
    closeCharacterDetail();
    
    try {
        const response = await fetch('/fetch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.status === 'error') {
            addLogEntry(`🔥 ${data.error || 'Unknown error'}`, true);
            return;
        }
        
        // Validate response data
        if (!data.characters || !Array.isArray(data.characters)) {
            throw new Error('Invalid response format: missing characters array');
        }
        
        if (data.characters.length > MAX_CHARACTERS) {
            addLogEntry(`⚠️ Warning: Received ${data.characters.length} characters, limiting to ${MAX_CHARACTERS}`, true);
            data.characters = data.characters.slice(0, MAX_CHARACTERS);
        }
        
        fetchedData = data;
        
        statCharacters.textContent = data.stats?.characterCount || 0;
        statQuotes.textContent = data.stats?.quoteCount || 0;
        statMovies.textContent = data.stats?.movieCount || 0;
        statSpeakers.textContent = data.stats?.charactersWithQuotes || 0;
        
        renderCharacters(data.characters);
        renderMovies(data.movies || []);
        
        // Update JSON preview
        updateJsonPreview(currentJsonView);
        
        // Reset to fancy view
        setViewMode('fancy');
        
        characterSearch.value = '';
        characterSearch.oninput = () => {
            closeCharacterDetail();
            renderCharacters(data.characters, characterSearch.value);
        };
        
        showPanel(previewSection);
        
        if (data.logs && Array.isArray(data.logs)) {
            data.logs.forEach(log => addLogEntry(log));
        }
        
        addLogEntry('💡 Click any character to see their full details and quotes!');
        
    } catch (error) {
        console.error('Fetch error:', error);
        addLogEntry(`🔥 Network error: ${error.message || 'Unknown error'}`, true);
    } finally {
        setProcessing(false);
    }
}

/**
 * Step 2: Send to Data Cloud
 */
async function handleConfirm() {
    if (isProcessing || !fetchedData) return;
    
    // Validate data before sending
    if (!fetchedData.characters || !Array.isArray(fetchedData.characters)) {
        addLogEntry('🔥 Invalid data: characters array missing', true);
        return;
    }
    
    if (fetchedData.characters.length > MAX_CHARACTERS) {
        addLogEntry(`🔥 Too many characters: ${fetchedData.characters.length} exceeds limit of ${MAX_CHARACTERS}`, true);
        return;
    }
    
    addLogEntry('🌋 The fires of Mount Doom are lit! Sending to Data Cloud...');
    setProcessing(true, 'Forging records in the fires of Mount Doom...');
    
    try {
        const response = await fetch('/ingest', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ characters: fetchedData.characters })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.logs && Array.isArray(data.logs)) {
            data.logs.forEach(log => addLogEntry(log, data.status === 'error'));
        }
        
        const summary = {
            status: data.status,
            ingestedCount: data.ingestedCount || 0,
            totalRecords: data.totalRecords || 0,
            timestamp: data.timestamp || new Date().toISOString()
        };
        
        if (data.successfulBatches !== undefined) {
            summary.successfulBatches = data.successfulBatches;
            summary.totalBatches = data.totalBatches;
        }
        
        if (data.error) summary.error = data.error;
        
        updateSummary(summary);
        
        hidePanel(previewSection);
        closeCharacterDetail();
        fetchedData = null;
        
        if (data.status === 'success') {
            addLogEntry('✨ You bow to no one. Ingestion complete!');
        }
        
    } catch (error) {
        console.error('Ingest error:', error);
        addLogEntry(`🔥 Network error: ${error.message || 'Unknown error'}`, true);
        updateSummary({
            status: 'error',
            error: 'Failed to send data to Data Cloud',
            timestamp: new Date().toISOString()
        });
    } finally {
        setProcessing(false);
    }
}

/**
 * Send Quotes to Data Cloud (Engagement DMO)
 */
async function handleConfirmQuotes() {
    if (isProcessing || !fetchedData) return;
    
    // Validate data before sending
    if (!fetchedData.characters || !Array.isArray(fetchedData.characters)) {
        addLogEntry('🔥 Invalid data: characters array missing', true);
        return;
    }
    
    // Check if there are any quotes
    const totalQuotes = fetchedData.characters.reduce((sum, c) => sum + (c.sampleQuotes?.length || 0), 0);
    if (totalQuotes === 0) {
        addLogEntry('🔥 No quotes found in character data', true);
        return;
    }
    
    addLogEntry(`📜 Inscribing ${totalQuotes} quotes into the archives...`);
    setProcessing(true, 'Sending quotes to Data Cloud...');
    
    try {
        const response = await fetch('/ingest-quotes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ characters: fetchedData.characters })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.logs && Array.isArray(data.logs)) {
            data.logs.forEach(log => addLogEntry(log, data.status === 'error'));
        }
        
        const summary = {
            status: data.status,
            type: 'Quote Ingestion',
            ingestedCount: data.ingestedCount || 0,
            totalQuotes: data.totalQuotes || 0,
            timestamp: data.timestamp || new Date().toISOString()
        };
        
        if (data.successfulBatches !== undefined) {
            summary.successfulBatches = data.successfulBatches;
            summary.totalBatches = data.totalBatches;
        }
        
        if (data.error) summary.error = data.error;
        
        updateSummary(summary);
        
        if (data.status === 'success') {
            addLogEntry('✨ The ancient words have been preserved!');
        }
        
    } catch (error) {
        console.error('Quote ingest error:', error);
        addLogEntry(`🔥 Network error: ${error.message || 'Unknown error'}`, true);
        updateSummary({
            status: 'error',
            type: 'Quote Ingestion',
            error: 'Failed to send quotes to Data Cloud',
            timestamp: new Date().toISOString()
        });
    } finally {
        setProcessing(false);
    }
}

function handleCancel() {
    hidePanel(previewSection);
    closeCharacterDetail();
    fetchedData = null;
    addLogEntry('🤚 The ring remains. (Ingestion cancelled)');
}

async function handleWipe() {
    if (isProcessing) return;
    
    const confirmed = confirm(
        "Cast it into the fire? Destroy it!\n\n" +
        "This will delete all LOTR character data from Data Cloud.\n\n" +
        "Are you sure?"
    );
    
    if (!confirmed) {
        addLogEntry('🤚 The ring remains. (Deletion cancelled)');
        return;
    }
    
    addLogEntry('🔥 The fires are lit! Beginning the great purge...');
    setProcessing(true, 'Deleting records from Data Cloud...');
    
    hidePanel(previewSection);
    closeCharacterDetail();
    fetchedData = null;
    
    try {
        const response = await fetch('/wipe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.logs && Array.isArray(data.logs)) {
            data.logs.forEach(log => addLogEntry(log, data.status === 'error'));
        }
        
        updateSummary({
            status: data.status,
            deletedCount: data.deletedCount || 0,
            timestamp: data.timestamp || new Date().toISOString()
        });
        
        if (data.status === 'success') {
            addLogEntry('✨ It is done. The age of LOTR data is over.');
        }
        
    } catch (error) {
        console.error('Wipe error:', error);
        addLogEntry(`🔥 Network error: ${error.message || 'Unknown error'}`, true);
    } finally {
        setProcessing(false);
    }
}

// Event listeners
fetchBtn.addEventListener('click', handleFetch);
confirmBtn.addEventListener('click', handleConfirm);
if (confirmQuotesBtn) confirmQuotesBtn.addEventListener('click', handleConfirmQuotes);
cancelBtn.addEventListener('click', handleCancel);
wipeBtn.addEventListener('click', handleWipe);

// View toggle listeners
if (fancyViewBtn) fancyViewBtn.addEventListener('click', () => setViewMode('fancy'));
if (jsonViewBtn) jsonViewBtn.addEventListener('click', () => setViewMode('json'));

// JSON tab listeners
if (jsonTabBtns) {
    jsonTabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            updateJsonPreview(btn.dataset.json);
        });
    });
}

// Copy button
if (copyJsonBtn) copyJsonBtn.addEventListener('click', copyJsonToClipboard);

setupTabs();

// Global error handler
window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    addLogEntry('An unexpected error occurred. Please refresh the page.', true);
});

console.log('🧙‍♂️ LOTR Data Cloud POC - UI Ready');

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('search-form');
    const queryInput = document.getElementById('query-input');
    const searchBtn = document.getElementById('search-btn');
    const searchSpinner = document.getElementById('search-spinner');
    
    const statusSection = document.getElementById('status-section');
    const statusText = document.getElementById('status-text');
    const stages = [
        document.getElementById('stage-0'),
        document.getElementById('stage-1'),
        document.getElementById('stage-2'),
        document.getElementById('stage-3')
    ];
    
    const resultsContainer = document.getElementById('results-container');
    const sourcesList = document.getElementById('sources-list');
    const overviewContent = document.getElementById('overview-content');
    const keyFindingsList = document.getElementById('key-findings-list');
    const confidenceValue = document.getElementById('confidence-value');
    const anomaliesContainer = document.getElementById('anomalies-container');

    // Simulate backend polling with stages
    let pollingInterval;
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const query = queryInput.value.trim();
        if (!query) return;

        // Reset UI
        resultsContainer.classList.add('hidden');
        statusSection.classList.remove('hidden');
        searchBtn.disabled = true;
        searchBtn.querySelector('span').textContent = 'Scanning...';
        searchSpinner.style.display = 'block';
        
        stages.forEach(s => {
            s.classList.remove('active', 'done');
            s.classList.add('pending');
        });
        
        statusText.textContent = "Initializing scan…";
        statusText.style.color = "var(--text-primary)";

        // Fake stage progression to keep user engaged while waiting
        let currentStage = 0;
        stages[currentStage].classList.add('active');
        stages[currentStage].classList.remove('pending');
        
        pollingInterval = setInterval(() => {
            if (currentStage < stages.length - 1) {
                stages[currentStage].classList.remove('active');
                stages[currentStage].classList.add('done');
                currentStage++;
                stages[currentStage].classList.remove('pending');
                stages[currentStage].classList.add('active');
            } else {
                statusText.textContent = "Waiting on the final packet…";
            }
        }, 2500);

        try {
            const response = await fetch('http://127.0.0.1:8080/research', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            clearInterval(pollingInterval);
            
            // Mark all as done
            stages.forEach(s => {
                s.classList.remove('active', 'pending');
                s.classList.add('done');
            });
            statusText.textContent = "Scan complete";
            
            setTimeout(() => {
                statusSection.classList.add('hidden');
                displayResults(data);
            }, 1000);

        } catch (error) {
            clearInterval(pollingInterval);
            statusText.textContent = "Scan failed";
            statusText.style.color = "var(--accent-error)";
            console.error('Error:', error);
            
            anomaliesContainer.innerHTML = `
                <div class="alert alert-error">
                    <strong>Error:</strong> Failed to connect to the backend. Ensure it is running on port 8080.
                </div>
            `;
            resultsContainer.classList.remove('hidden');
        } finally {
            searchBtn.disabled = false;
            searchBtn.querySelector('span').textContent = 'Search';
            searchSpinner.style.display = 'none';
        }
    });

    function displayResults(data) {
        // Clear previous
        sourcesList.innerHTML = '';
        overviewContent.innerHTML = '';
        keyFindingsList.innerHTML = '';
        anomaliesContainer.innerHTML = '';
        
        // Render Sources
        if (data.sources && data.sources.length > 0) {
            data.sources.forEach((src, idx) => {
                const a = document.createElement('a');
                a.href = src.url || '#';
                a.target = "_blank";
                a.className = "source-row";
                a.innerHTML = `
                    <span class="src-index">${String(idx + 1).padStart(2, '0')}</span>
                    <span>${src.title || 'Source Document'}</span>
                `;
                sourcesList.appendChild(a);
            });
        } else {
            sourcesList.innerHTML = '<p class="text-muted">No sources indexed.</p>';
        }

        // Render Overview
        if (data.overview) {
            overviewContent.innerHTML = marked.parse(data.overview);
        } else {
            overviewContent.innerHTML = '<p class="text-muted">No overview generated.</p>';
        }

        // Render Key Findings
        if (data.key_findings && data.key_findings.length > 0) {
            data.key_findings.forEach(finding => {
                const li = document.createElement('li');
                li.textContent = finding;
                keyFindingsList.appendChild(li);
            });
        }

        // Render HUD
        confidenceValue.textContent = data.confidence || "Unknown";
        
        if (data.contradictions && data.contradictions.length > 0) {
            const list = data.contradictions.map(c => `<li>${c}</li>`).join('');
            anomaliesContainer.innerHTML = `
                <div class="alert alert-warning">
                    <strong>Anomalies detected:</strong>
                    <ul style="margin-left: 1rem; margin-top: 0.5rem;">${list}</ul>
                </div>
            `;
        } else {
            anomaliesContainer.innerHTML = `
                <div class="alert alert-success">
                    No anomalies detected.
                </div>
            `;
        }

        resultsContainer.classList.remove('hidden');
    }
});

// API Configuration — use the page origin when served from the backend to avoid CORS
const API_BASE_URL = (window && window.location && window.location.protocol !== 'file:' && window.location.origin && window.location.origin !== 'null') ? window.location.origin : 'http://localhost:8000';

// DOM Elements
const elements = {
    // Navigation
    navBtns: document.querySelectorAll('.nav-btn'),
    tabContents: document.querySelectorAll('.tab-content'),

    // Resume Analyzer
    jdUploadArea: document.getElementById('jdUploadArea'),
    resumeUploadArea: document.getElementById('resumeUploadArea'),
    jdFile: document.getElementById('jdFile'),
    resumeFile: document.getElementById('resumeFile'),
    jdFileInfo: document.getElementById('jdFileInfo'),
    resumeFileInfo: document.getElementById('resumeFileInfo'),
    mustHaveSkills: document.getElementById('mustHaveSkills'),
    skillStrictness: document.getElementById('skillStrictness'),
    strictnessValue: document.getElementById('strictnessValue'),
    minExperience: document.getElementById('minExperience'),
    analyzeBtn: document.getElementById('analyzeBtn'),

    // Resume Results
    resumeResultsSection: document.getElementById('resumeResultsSection'),
    resumeBackBtn: document.getElementById('resumeBackBtn'),
    scoreDisplay: document.getElementById('scoreDisplay'),
    resumeLoadingState: document.getElementById('resumeLoadingState'),
    resumeResultsContent: document.getElementById('resumeResultsContent'),

    // Analysis Tabs
    analysisTabHeaders: document.querySelectorAll('.analysis-tab-header'),
    analysisTabPanes: document.querySelectorAll('.analysis-tab-pane'),

    // Analysis Content Elements
    missingSkills: document.getElementById('missingSkills'),
    strongSkills: document.getElementById('strongSkills'),
    strengthsList: document.getElementById('strengthsList'),
    weaknessesList: document.getElementById('weaknessesList'),
    improvementsList: document.getElementById('improvementsList'),
    resumeOptimization: document.getElementById('resumeOptimization'),
    skillDevelopment: document.getElementById('skillDevelopment'),
    riskFactors: document.getElementById('riskFactors'),
    redFlags: document.getElementById('redFlags'),
    keywordAnalysis: document.getElementById('keywordAnalysis'),
    experienceEvaluation: document.getElementById('experienceEvaluation'),

    // Interview Coach
    jobRole: document.getElementById('jobRole'),
    company: document.getElementById('company'),
    experienceLevel: document.getElementById('experienceLevel'),
    interviewType: document.getElementById('interviewType'),
    startInterviewBtn: document.getElementById('startInterviewBtn'),
    endInterviewBtn: document.getElementById('endInterviewBtn'),
    interviewConversation: document.getElementById('interviewConversation'),
    conversationMessages: document.getElementById('conversationMessages'),
    userResponse: document.getElementById('userResponse'),
    sendResponseBtn: document.getElementById('sendResponseBtn'),
    listenBtn: document.getElementById('listenBtn'),
    voiceEnabled: document.getElementById('voiceEnabled'),
    interviewProgress: document.getElementById('interviewProgress'),

    // Interview Evaluation
    interviewEvaluationSection: document.getElementById('interviewEvaluationSection'),
    interviewScore: document.getElementById('interviewScore'),
    interviewFeedback: document.getElementById('interviewFeedback'),
    interviewStrengths: document.getElementById('interviewStrengths'),
    interviewImprovements: document.getElementById('interviewImprovements'),
    newInterviewBtn: document.getElementById('newInterviewBtn'),

    // History
    historyTable: document.getElementById('historyTable'),
    refreshHistory: document.getElementById('refreshHistory'),
    clearHistory: document.getElementById('clearHistory'),

    // Toast
    toastContainer: document.getElementById('toastContainer')
};

// State
let jdFile = null;
let resumeFile = null;
let currentInterviewSession = null;
let currentAnalysisData = null;

// Event Listeners
function initializeEventListeners() {
    // Navigation
    elements.navBtns.forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });

    // Resume Analyzer - File Upload
    elements.jdUploadArea.addEventListener('click', () => elements.jdFile.click());
    elements.resumeUploadArea.addEventListener('click', () => elements.resumeFile.click());

    elements.jdFile.addEventListener('change', (e) => handleFileSelect(e, 'jd'));
    elements.resumeFile.addEventListener('change', (e) => handleFileSelect(e, 'resume'));

    // Resume Analyzer - Configuration
    elements.skillStrictness.addEventListener('input', (e) => {
        elements.strictnessValue.textContent = e.target.value;
    });

    // Resume Analyzer - Analysis
    elements.analyzeBtn.addEventListener('click', analyzeResume);
    elements.resumeBackBtn.addEventListener('click', showResumeInputSection);

    // Analysis Tabs
    if (elements.analysisTabHeaders) {
        elements.analysisTabHeaders.forEach(header => {
            header.addEventListener('click', () => switchAnalysisTab(header.dataset.tab));
        });
    }

    // Interview Coach
    elements.startInterviewBtn.addEventListener('click', startInterview);
    elements.endInterviewBtn.addEventListener('click', endInterview);
    elements.sendResponseBtn.addEventListener('click', sendInterviewResponse);

    if (elements.listenBtn) {
        elements.listenBtn.addEventListener('click', async () => {
            if (!currentInterviewSession) {
                showToast('No active interview session', 'error');
                return;
            }

            const originalText = elements.listenBtn.innerHTML;
            elements.listenBtn.innerHTML = '<i class="fas fa-microphone"></i> Listening...';
            elements.listenBtn.disabled = true;
            elements.listenBtn.style.opacity = '0.7';

            try {
                const formData = new FormData();
                formData.append('session_id', currentInterviewSession);

                const response = await fetch(`${API_BASE_URL}/interview/listen`, {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) throw new Error('Listening failed');

                const result = await response.json();
                if (result.success && result.text) {
                    elements.userResponse.value = result.text;
                    showToast('Voice captured successfully', 'success');
                } else {
                    showToast(result.error || 'Could not recognize speech, please try again or type', 'warning');
                }
            } catch (e) {
                console.error(e);
                showToast('Mic error: ' + e.message, 'error');
            } finally {
                elements.listenBtn.innerHTML = originalText;
                elements.listenBtn.disabled = false;
                elements.listenBtn.style.opacity = '1';
            }
        });
    }

    if (elements.newInterviewBtn) {
        elements.newInterviewBtn.addEventListener('click', () => {
            elements.interviewEvaluationSection.classList.add('hidden');
            elements.startInterviewBtn.classList.remove('hidden');
        });
    }

    // History
    elements.refreshHistory.addEventListener('click', loadHistory);
    elements.clearHistory.addEventListener('click', clearHistory);

    // Add connection status indicator
    updateConnectionStatus();
}

// Navigation
function switchTab(tabName) {
    // Update navigation buttons
    elements.navBtns.forEach(btn => {
        if (btn.dataset.tab === tabName) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Update tab contents
    elements.tabContents.forEach(tab => {
        if (tab.id === `${tabName}Tab`) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });

    // Load data for specific tabs
    if (tabName === 'history') {
        loadHistory();
    }
}

// Resume Analysis Functions
function handleFileSelect(event, type) {
    const file = event.target.files[0];
    if (file) {
        updateFileInfo(file, type);
        if (type === 'jd') jdFile = file;
        if (type === 'resume') resumeFile = file;
    }
}

function updateFileInfo(file, type) {
    const fileInfoElement = type === 'jd' ? elements.jdFileInfo : elements.resumeFileInfo;
    const uploadArea = type === 'jd' ? elements.jdUploadArea : elements.resumeUploadArea;

    fileInfoElement.innerHTML = `
        <strong>${file.name}</strong>
        <br>Size: ${(file.size / 1024 / 1024).toFixed(2)} MB
        <br>Type: ${file.type}
    `;

    uploadArea.style.borderColor = 'var(--success)';
    uploadArea.style.background = '#f0fff4';
}

// Connection Testing
async function testBackendConnection() {
    try {
        const healthResponse = await fetch(`${API_BASE_URL}/health`);
        if (!healthResponse.ok) {
            throw new Error(`Health endpoint returned ${healthResponse.status}`);
        }
        const healthData = await healthResponse.json();
        return { success: true, data: healthData };
    } catch (error) {
        console.error('❌ Backend connection failed:', error);
        return { success: false, error: error.message };
    }
}

function updateConnectionStatus() {
    const statusIndicator = document.createElement('div');
    statusIndicator.id = 'connectionStatus';
    statusIndicator.style.cssText = `
        position: fixed;
        top: 10px;
        right: 10px;
        padding: 8px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        z-index: 1000;
        background: #ff6b6b;
        color: white;
    `;
    statusIndicator.innerHTML = '🔴 Checking...';
    document.body.appendChild(statusIndicator);

    // Test connection periodically
    setInterval(async () => {
        const result = await testBackendConnection();
        const statusElement = document.getElementById('connectionStatus');
        if (result.success) {
            statusElement.innerHTML = '🟢 Backend Online';
            statusElement.style.background = '#51cf66';
        } else {
            statusElement.innerHTML = '🔴 Backend Offline';
            statusElement.style.background = '#ff6b6b';
        }
    }, 10000);

    // Initial test
    testBackendConnection().then(result => {
        const statusElement = document.getElementById('connectionStatus');
        if (result.success) {
            statusElement.innerHTML = '🟢 Backend Online';
            statusElement.style.background = '#51cf66';
        }
    });
}

// Resume Analysis
async function analyzeResume() {
    if (!jdFile || !resumeFile) {
        showToast('Please upload both Job Description and Resume files', 'error');
        return;
    }

    // Test connection first
    const connectionTest = await testBackendConnection();
    if (!connectionTest.success) {
        showToast('Cannot connect to backend server. Please make sure it is running.', 'error');
        return;
    }

    showResumeResultsSection();
    elements.resumeLoadingState.classList.remove('hidden');
    elements.resumeResultsContent.classList.add('hidden');

    const formData = new FormData();
    formData.append('jd_file', jdFile);
    formData.append('resume_file', resumeFile);
    formData.append('must_have_skills', elements.mustHaveSkills.value);
    formData.append('skill_strictness', elements.skillStrictness.value);
    formData.append('min_experience', elements.minExperience.value);
    formData.append('analysis_depth', 'Standard');
    formData.append('industry_focus', 'Technology');

    try {
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Server returned ${response.status}`);
        }

        const result = await response.json();

        if (result.success) {
            currentAnalysisData = result;
            displayAnalysisResults(result);
            showToast('Analysis completed successfully!', 'success');
        } else {
            throw new Error(result.error || 'Analysis failed');
        }
    } catch (error) {
        console.error('❌ Analysis error:', error);
        showToast('Analysis failed: ' + error.message, 'error');
        showResumeInputSection();
    }
}

function displayAnalysisResults(result) {
    console.log('📊 Analysis result:', result);

    // Hide loading and show results
    elements.resumeLoadingState.classList.add('hidden');
    elements.resumeResultsContent.classList.remove('hidden');

    // Store analysis data for tab switching
    currentAnalysisData = result;

    // Display overall score
    const score = result.overall_score;
    let gradient, status, icon;

    if (score >= 70) {
        gradient = 'linear-gradient(135deg, #00b09b, #96c93d)';
        status = 'Strong Match';
        icon = '🎯';
    } else if (score >= 50) {
        gradient = 'linear-gradient(135deg, #f8b500, #fceabb)';
        status = 'Moderate Match';
        icon = '⚠️';
    } else {
        gradient = 'linear-gradient(135deg, #ff416c, #ff4b2b)';
        status = 'Needs Improvement';
        icon = '🔴';
    }

    elements.scoreDisplay.innerHTML = `
        <div style="background: ${gradient}; padding: 3rem; border-radius: 15px; text-align: center; box-shadow: 0 8px 25px rgba(0,0,0,0.15);">
            <h1 style="color: white; font-size: 4rem; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); font-weight: bold;">${score}%</h1>
            <p style="color: white; font-size: 1.5rem; margin: 0.5rem 0; font-weight: 600;">Overall ATS Score</p>
            <p style="color: white; font-size: 1.2rem; margin: 0; background: rgba(255,255,255,0.2); padding: 0.5rem 1.5rem; border-radius: 25px; display: inline-block; font-weight: 500;">
                ${icon} ${status}
            </p>
        </div>
    `;

    // Populate analysis data
    populateAnalysisData(result.analysis_data);

    // Load updated history
    loadHistory();
}

function populateAnalysisData(analysisData) {
    console.log('📝 Populating analysis data:', analysisData);

    if (!analysisData) {
        console.error('❌ No analysis data available');
        return;
    }

    // Skills Analysis
    const skillsAnalysis = analysisData.skills_analysis || {};
    populateList(elements.missingSkills, skillsAnalysis.missing_critical_skills || [], 'danger', '❌');
    populateList(elements.strongSkills, skillsAnalysis.strong_skills || [], 'success', '✅');

    // Detailed Feedback
    const feedback = analysisData.detailed_feedback || {};
    populateList(elements.strengthsList, feedback.strengths || [], 'success', '✅');
    populateList(elements.weaknessesList, feedback.weaknesses || [], 'danger', '❌');
    populateList(elements.improvementsList, feedback.immediate_improvements || [], 'warning', '⚡');

    // Recommendations
    const recommendations = analysisData.recommendations || {};
    populateList(elements.resumeOptimization, recommendations.resume_optimization || [], 'warning', '✏️');
    populateList(elements.skillDevelopment, recommendations.skill_development || [], 'warning', '📚');

    // Risk Analysis
    populateList(elements.riskFactors, analysisData.risk_factors || [], 'danger', '🔴');
    populateList(elements.redFlags, analysisData.potential_red_flags || [], 'danger', '🚩');

    // Keyword Analysis
    const keywordAnalysis = analysisData.keyword_analysis || {};
    if (elements.keywordAnalysis) {
        elements.keywordAnalysis.innerHTML = `
            <div class="keyword-stats">
                <div class="stat-item">
                    <strong>Keyword Density Score:</strong>
                    <span class="score">${keywordAnalysis.keyword_density_score || 'N/A'}</span>
                </div>
                <div class="stat-item">
                    <strong>ATS Optimization Score:</strong>
                    <span class="score">${keywordAnalysis.ats_optimization_score || 'N/A'}</span>
                </div>
            </div>
            ${keywordAnalysis.missing_keywords && keywordAnalysis.missing_keywords.length > 0 ? `
                <div class="missing-keywords">
                    <h4>Missing Keywords:</h4>
                    <div class="keyword-list">
                        ${keywordAnalysis.missing_keywords.map(keyword =>
            `<span class="keyword-tag missing">${keyword}</span>`
        ).join('')}
                    </div>
                </div>
            ` : ''}
        `;
    }

    // Experience Evaluation
    const experienceEvaluation = analysisData.experience_evaluation || {};
    if (elements.experienceEvaluation) {
        elements.experienceEvaluation.innerHTML = `
            <div class="experience-stats">
                <div class="stat-item">
                    <strong>Years Experience Match:</strong>
                    <span class="score">${experienceEvaluation.years_experience_match || 'N/A'}</span>
                </div>
                <div class="stat-item">
                    <strong>Relevant Experience Score:</strong>
                    <span class="score">${experienceEvaluation.relevant_experience_score || 'N/A'}</span>
                </div>
                <div class="stat-item">
                    <strong>Career Progression:</strong>
                    <span class="score">${experienceEvaluation.career_progression || 'N/A'}</span>
                </div>
            </div>
        `;
    }
}

function populateList(container, items, type = '', icon = '•') {
    if (!container) {
        console.error('❌ Container element not found');
        return;
    }

    if (!items || !Array.isArray(items) || items.length === 0) {
        container.innerHTML = `<div class="list-item" style="padding: 1rem; text-align: center; color: #666; font-style: italic;">
            No ${type} data available
        </div>`;
        return;
    }

    console.log(`📝 Populating ${container.id} with ${items.length} items`);

    container.innerHTML = items.map(item => {
        const displayText = typeof item === 'string' ? item : JSON.stringify(item);
        return `
            <div class="list-item ${type}">
                <span class="item-icon">${icon}</span>
                <span class="item-text">${displayText}</span>
            </div>
        `;
    }).join('');
}

// Analysis Tab Management
function switchAnalysisTab(tabName) {
    console.log('🔖 Switching to analysis tab:', tabName);

    // Update tab headers
    if (elements.analysisTabHeaders) {
        elements.analysisTabHeaders.forEach(header => {
            if (header.dataset.tab === tabName) {
                header.classList.add('active');
            } else {
                header.classList.remove('active');
            }
        });
    }

    // Update tab panes
    if (elements.analysisTabPanes) {
        elements.analysisTabPanes.forEach(pane => {
            if (pane.id === `${tabName}Tab`) {
                pane.classList.add('active');
            } else {
                pane.classList.remove('active');
            }
        });
    }
}

// Resume UI Management
function showResumeInputSection() {
    elements.resumeResultsSection.classList.add('hidden');
}

function showResumeResultsSection() {
    elements.resumeResultsSection.classList.remove('hidden');
}

// Interview Coach Functions
async function startInterview() {
    try {
        const formData = new FormData();
        formData.append('job_role', elements.jobRole.value);
        formData.append('company', elements.company.value);
        formData.append('experience_level', elements.experienceLevel.value);
        formData.append('interview_type', elements.interviewType.value);
        formData.append('voice_enabled', elements.voiceEnabled ? elements.voiceEnabled.checked : false);

        const response = await fetch(`${API_BASE_URL}/interview/start`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Failed to start interview: ${response.status}`);
        }

        const result = await response.json();

        if (result.success) {
            currentInterviewSession = result.session_id;

            // Update UI
            elements.interviewEvaluationSection.classList.add('hidden');
            elements.startInterviewBtn.classList.add('hidden');
            elements.endInterviewBtn.classList.remove('hidden');
            elements.interviewConversation.classList.remove('hidden');

            // Display first message
            displayInterviewMessage('interviewer', result.first_message);

            showToast('Interview started! The HR interviewer will begin the conversation.', 'success');
        } else {
            throw new Error('Failed to start interview session');
        }

    } catch (error) {
        console.error('❌ Error starting interview:', error);
        showToast('Failed to start interview: ' + error.message, 'error');
    }
}

async function sendInterviewResponse() {
    if (!currentInterviewSession) {
        showToast('No active interview session', 'error');
        return;
    }

    const userResponse = elements.userResponse.value.trim();
    if (!userResponse) {
        showToast('Please enter your response', 'warning');
        return;
    }

    try {
        // Display user message
        displayInterviewMessage('candidate', userResponse);
        elements.userResponse.value = '';

        const formData = new FormData();
        formData.append('session_id', currentInterviewSession);
        formData.append('user_response', userResponse);

        const response = await fetch(`${API_BASE_URL}/interview/respond`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Failed to send response: ${response.status}`);
        }

        const result = await response.json();

        if (result.success) {
            // Display AI response
            displayInterviewMessage('interviewer', result.ai_response);

            // Update progress
            updateInterviewProgress(result.conversation_history);
        } else {
            throw new Error('Failed to get AI response');
        }

    } catch (error) {
        console.error('❌ Error sending response:', error);
        showToast('Failed to send response: ' + error.message, 'error');
    }
}

function displayInterviewMessage(role, message) {
    const messageElement = document.createElement('div');
    messageElement.className = `message ${role}`;
    messageElement.innerHTML = `
        <strong>${role === 'interviewer' ? '🤵 HR Interviewer' : '👤 You'}:</strong>
        <div style="margin-top: 0.5rem;">${message}</div>
    `;

    elements.conversationMessages.appendChild(messageElement);
    elements.conversationMessages.scrollTop = elements.conversationMessages.scrollHeight;
}

function updateInterviewProgress(conversationHistory) {
    const interviewerMessages = conversationHistory.filter(msg => msg.role === 'interviewer').length;
    const progress = Math.min((interviewerMessages / 8) * 100, 100);

    elements.interviewProgress.textContent = `Progress: ${Math.round(progress)}%`;
}

async function endInterview() {
    if (!currentInterviewSession) return;

    try {
        elements.endInterviewBtn.disabled = true;
        elements.endInterviewBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Evaluating...';

        const formData = new FormData();
        formData.append('session_id', currentInterviewSession);

        const response = await fetch(`${API_BASE_URL}/interview/end`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        // Reset UI
        elements.startInterviewBtn.classList.remove('hidden');
        elements.endInterviewBtn.classList.add('hidden');
        elements.endInterviewBtn.disabled = false;
        elements.endInterviewBtn.innerHTML = '<i class="fas fa-stop"></i> End Interview';
        elements.interviewConversation.classList.add('hidden');
        elements.conversationMessages.innerHTML = '';
        elements.userResponse.value = '';

        currentInterviewSession = null;

        if (result.success && result.evaluation) {
            // Show evaluation section
            elements.interviewEvaluationSection.classList.remove('hidden');
            elements.interviewScore.textContent = `${result.evaluation.score}/100`;

            elements.interviewFeedback.textContent = result.evaluation.overall_feedback || 'No feedback provided.';

            populateList(elements.interviewStrengths, result.evaluation.strengths || [], 'success', '✅');
            populateList(elements.interviewImprovements, result.evaluation.areas_for_improvement || [], 'warning', '⚡');
        }

        showToast('Interview ended successfully', 'success');

    } catch (error) {
        console.error('❌ Error ending interview:', error);
        elements.endInterviewBtn.disabled = false;
        elements.endInterviewBtn.innerHTML = '<i class="fas fa-stop"></i> End Interview';
        showToast('Failed to end interview: ' + error.message, 'error');
    }
}

// History Management
async function loadHistory() {
    try {
        const response = await fetch(`${API_BASE_URL}/history`);

        if (!response.ok) {
            throw new Error(`History endpoint returned ${response.status}`);
        }

        const result = await response.json();

        if (result.success) {
            displayHistory(result.history);
        } else {
            throw new Error(result.error || 'Failed to load history');
        }
    } catch (error) {
        console.error('❌ Error loading history:', error);
        elements.historyTable.innerHTML = '<p style="padding: 2rem; text-align: center; color: #666;">Unable to load history.</p>';
    }
}

function displayHistory(history) {
    if (!history || history.length === 0) {
        elements.historyTable.innerHTML = '<p style="padding: 2rem; text-align: center; color: #666;">No analysis history yet. Run your first analysis above!</p>';
        return;
    }

    // Display table
    elements.historyTable.innerHTML = `
        <div style="overflow-x: auto; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <table style="width: 100%; border-collapse: collapse; background: white;">
                <thead>
                    <tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                        <th style="padding: 1rem; text-align: left; font-weight: 600;">Date</th>
                        <th style="padding: 1rem; text-align: left; font-weight: 600;">JD File</th>
                        <th style="padding: 1rem; text-align: left; font-weight: 600;">Resume File</th>
                        <th style="padding: 1rem; text-align: left; font-weight: 600;">Score</th>
                        <th style="padding: 1rem; text-align: left; font-weight: 600;">Status</th>
                    </tr>
                </thead>
                <tbody>
                    ${history.map(item => `
                        <tr style="border-bottom: 1px solid var(--border); transition: background 0.2s;">
                            <td style="padding: 1rem;">${item.date}</td>
                            <td style="padding: 1rem; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${item.jd_file}">${item.jd_file}</td>
                            <td style="padding: 1rem; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${item.resume_file}">${item.resume_file}</td>
                            <td style="padding: 1rem; font-weight: bold; color: ${item.score >= 70 ? '#28a745' :
            item.score >= 50 ? '#ffc107' : '#dc3545'
        };">${item.score}%</td>
                            <td style="padding: 1rem;">${item.status}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

async function clearHistory() {
    if (!confirm('Are you sure you want to clear all analysis history? This action cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/history`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error(`Clear history returned ${response.status}`);
        }

        const result = await response.json();

        if (result.success) {
            showToast('History cleared successfully!', 'success');
            loadHistory();
        } else {
            throw new Error(result.error || 'Failed to clear history');
        }
    } catch (error) {
        console.error('❌ Error clearing history:', error);
        showToast('Failed to clear history', 'error');
    }
}

// Toast Notifications
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        color: white;
        z-index: 10000;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        animation: slideIn 0.3s ease;
    `;

    // Set background color based on type
    if (type === 'success') toast.style.background = '#28a745';
    else if (type === 'error') toast.style.background = '#dc3545';
    else if (type === 'warning') toast.style.background = '#ffc107';
    else toast.style.background = '#007bff';

    elements.toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Add CSS animations and styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .hidden {
        display: none !important;
    }

    .list-item {
        padding: 12px 16px;
        margin: 8px 0;
        border-radius: 8px;
        background: #f8f9fa;
        border-left: 4px solid #6c757d;
        transition: all 0.3s ease;
        display: flex;
        align-items: flex-start;
        gap: 8px;
    }

    .list-item.success {
        background: #d4edda;
        border-left-color: #28a745;
        color: #155724;
    }

    .list-item.danger {
        background: #f8d7da;
        border-left-color: #dc3545;
        color: #721c24;
    }

    .list-item.warning {
        background: #fff3cd;
        border-left-color: #ffc107;
        color: #856404;
    }

    .list-item:hover {
        transform: translateX(5px);
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }

    .item-icon {
        font-size: 14px;
        flex-shrink: 0;
        margin-top: 2px;
    }

    .item-text {
        flex: 1;
    }

    .analysis-tabs {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: var(--shadow);
        margin-bottom: 1.5rem;
    }

    .analysis-tab-headers {
        display: flex;
        border-bottom: 1px solid var(--border);
        margin-bottom: 1.5rem;
        flex-wrap: wrap;
    }

    .analysis-tab-header {
        padding: 1rem 1.5rem;
        background: none;
        border: none;
        border-bottom: 3px solid transparent;
        cursor: pointer;
        transition: all 0.3s ease;
        font-weight: 600;
        white-space: nowrap;
    }

    .analysis-tab-header.active {
        border-bottom-color: var(--primary);
        color: var(--primary);
    }

    .analysis-tab-pane {
        display: none;
    }

    .analysis-tab-pane.active {
        display: block;
    }

    .keyword-stats, .experience-stats {
        display: grid;
        gap: 1rem;
        margin-bottom: 1.5rem;
    }

    .stat-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.75rem;
        background: #f8f9fa;
        border-radius: 8px;
        border-left: 4px solid var(--primary);
    }

    .stat-item .score {
        font-weight: bold;
        color: var(--primary);
    }

    .keyword-list {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 0.5rem;
    }

    .keyword-tag {
        padding: 0.25rem 0.75rem;
        background: #e9ecef;
        border-radius: 20px;
        font-size: 0.875rem;
        border: 1px solid #dee2e6;
    }

    .keyword-tag.missing {
        background: #f8d7da;
        color: #721c24;
        border-color: #f5c6cb;
    }

    .analysis-grid {
        display: grid;
        gap: 2rem;
        margin-top: 1rem;
    }

    .analysis-column {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .analysis-column h4 {
        margin-bottom: 0.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--border);
        color: var(--dark);
    }
`;
document.head.appendChild(style);

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initializing CareerPrep Pro...');

    initializeEventListeners();
    loadHistory();

    // Test initial connection
    testBackendConnection().then(result => {
        if (result.success) {
            console.log('🎉 Application initialized successfully!');
        } else {
            console.warn('⚠️ Application initialized but backend connection failed');
        }
    });
});
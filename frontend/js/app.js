/**
 * 🔮 GIT SÉANCE — Master Application Controller
 */

let currentSeanceData = null;
let currentRepoUrl = '';
let currentFilter = 'all';
let currentSort = 'mortality';
let currentSearch = '';

// Active modal séance session state
let activeReportData = null;
let activeChannelingData = null;
let activeChatHistory = [];

document.addEventListener('DOMContentLoaded', () => {
  initControls();
  initForm();
  initPresets();
  initModal();

  // Play keyboard sound on typing
  document.querySelectorAll('input, select').forEach((elem) => {
    elem.addEventListener('keydown', () => SoundFX.playKeyClick());
  });
});

/* ─── Control Bar (CRT & Audio Toggles) ─── */
function initControls() {
  const crtToggle = document.getElementById('crt-toggle-btn');
  const soundToggle = document.getElementById('sound-toggle-btn');

  if (crtToggle) {
    crtToggle.addEventListener('click', () => {
      document.body.classList.toggle('crt-disabled');
      const isDisabled = document.body.classList.contains('crt-disabled');
      crtToggle.classList.toggle('active', !isDisabled);
      crtToggle.innerHTML = isDisabled ? '📺 CRT: OFF' : '📺 CRT: ON';
      SoundFX.playKeyClick();
    });
  }

  if (soundToggle) {
    soundToggle.addEventListener('click', () => {
      const enabled = SoundFX.toggleSound();
      soundToggle.classList.toggle('active', enabled);
      soundToggle.innerHTML = enabled ? '🔊 AUDIO: ON' : '🔇 AUDIO: OFF';
      if (enabled) SoundFX.playKeyClick();
    });
  }
}

/* ─── Summoning Form & Presets ─── */
function initForm() {
  const form = document.getElementById('summon-form');
  const input = document.getElementById('repo-url-input');
  const submitBtn = document.getElementById('summon-btn');

  if (!form || !input) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const url = input.value.trim();
    if (!url) return;
    executeSeance(url);
  });
}

function initPresets() {
  const presets = document.querySelectorAll('.preset-chip');
  const input = document.getElementById('repo-url-input');

  presets.forEach((chip) => {
    chip.addEventListener('click', () => {
      const url = chip.getAttribute('data-url');
      if (url && input) {
        input.value = url;
        SoundFX.playKeyClick();
        executeSeance(url);
      }
    });
  });
}

/* ─── Execute Repository Scan ─── */
async function executeSeance(repoUrl) {
  currentRepoUrl = repoUrl;
  const submitBtn = document.getElementById('summon-btn');
  const resultsContainer = document.getElementById('seance-results');

  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span>⏳ Channeling spirits...</span>`;
  }

  Terminal.clearLogs();
  Terminal.triggerFlicker();
  SoundFX.playSummonSweep();

  function onComplete(data) {
    currentSeanceData = data;
    renderSeanceResults(data);
    if (resultsContainer) {
      resultsContainer.style.display = 'block';
      resultsContainer.scrollIntoView({ behavior: 'smooth' });
    }
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerHTML = `<span>🔮 INITIATE SÉANCE</span>`;
    }
  }

  function onError(msg) {
    Terminal.log('error', `Séance disrupted: ${msg}`);
    alert(`The séance was disrupted: ${msg}`);
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerHTML = `<span>🔮 INITIATE SÉANCE</span>`;
    }
  }

  // Use real-time Server-Sent Events (SSE) streaming if available
  if (window.EventSource) {
    const streamUrl = `/api/seance/stream?repo_url=${encodeURIComponent(repoUrl)}`;
    const eventSource = new EventSource(streamUrl);

    eventSource.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.agent === 'error') {
          eventSource.close();
          onError(payload.message);
        } else if (payload.agent === 'complete') {
          eventSource.close();
          Terminal.log('medium', payload.message);
          onComplete(payload.result);
        } else {
          Terminal.log(payload.agent, payload.message);
        }
      } catch (err) {
        console.error('SSE parse error:', err);
      }
    };

    eventSource.onerror = (err) => {
      eventSource.close();
      console.warn('SSE disconnected, falling back to direct POST /api/seance/scan', err);
      fallbackPostSeance(repoUrl, onComplete, onError);
    };
  } else {
    fallbackPostSeance(repoUrl, onComplete, onError);
  }
}

async function fallbackPostSeance(repoUrl, onComplete, onError) {
  try {
    Terminal.log('reaper', `Contacting repository archives for ${repoUrl}...`);
    const response = await fetch('/api/seance/scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repo_url: repoUrl }),
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'The spirits refused the summons');
    }

    const data = await response.json();
    Terminal.log('medium', `Séance complete. Channeled ${data.total_files_scanned} files.`);
    onComplete(data);
  } catch (err) {
    onError(err.message);
  }
}

/* ─── Render Séance Ledger Results ─── */
function renderSeanceResults(data) {
  // Prophecy Summary
  const prophecyText = document.getElementById('prophecy-text');
  if (prophecyText) {
    prophecyText.textContent = `"${data.summary}"`;
  }

  // Tally counts
  document.getElementById('tally-total').textContent = data.total_files_scanned;
  document.getElementById('tally-dead').textContent = data.dead_count;
  document.getElementById('tally-haunted').textContent = data.haunted_count;
  document.getElementById('tally-orphaned').textContent = data.orphaned_count;
  document.getElementById('tally-cursed').textContent = data.cursed_count;
  document.getElementById('tally-alive').textContent = data.alive_count;

  // Setup toolbar listeners
  setupToolbarListeners();

  // Render file roster
  renderFileRoster();
}

function setupToolbarListeners() {
  // Filter pills
  document.querySelectorAll('.filter-pill').forEach((pill) => {
    pill.addEventListener('click', () => {
      document.querySelectorAll('.filter-pill').forEach((p) => p.classList.remove('active'));
      pill.classList.add('active');
      currentFilter = pill.getAttribute('data-filter');
      SoundFX.playKeyClick();
      renderFileRoster();
    });
  });

  // Search input
  const searchInput = document.getElementById('roster-search');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      currentSearch = e.target.value.toLowerCase().trim();
      renderFileRoster();
    });
  }

  // Sort dropdown
  const sortSelect = document.getElementById('roster-sort');
  if (sortSelect) {
    sortSelect.addEventListener('change', (e) => {
      currentSort = e.target.value;
      SoundFX.playKeyClick();
      renderFileRoster();
    });
  }

  // Badge button
  const badgeBtn = document.getElementById('embed-badge-btn');
  if (badgeBtn) {
    badgeBtn.onclick = () => {
      SoundFX.playKeyClick();
      copyBadgeSnippet();
    };
  }

  // Export buttons
  const mdBtn = document.getElementById('export-markdown-btn');
  if (mdBtn) {
    mdBtn.onclick = () => {
      SoundFX.playKeyClick();
      exportMarkdownReport();
    };
  }

  const csvBtn = document.getElementById('export-csv-btn');
  if (csvBtn) {
    csvBtn.onclick = () => {
      SoundFX.playKeyClick();
      exportTabPFNCSVReport();
    };
  }

  const jsonBtn = document.getElementById('export-json-btn');
  if (jsonBtn) {
    jsonBtn.onclick = () => {
      SoundFX.playKeyClick();
      exportJsonReport();
    };
  }
}

function exportTabPFNCSVReport() {
  if (!currentSeanceData) return;
  const d = currentSeanceData;
  const headers = [
    'file_path',
    'status',
    'tabpfn_mortality_risk',
    'ghost_score',
    'days_since_last_commit',
    'total_commits',
    'unique_authors',
    'bug_fix_commit_ratio',
    'lines_added',
    'lines_deleted',
    'has_tests',
    'churn_velocity',
    'last_author',
    'last_commit_date',
  ];

  const rows = [headers.join(',')];

  d.haunting_reports.forEach((r) => {
    const m = r.metrics;
    const risk = r.mortality_risk !== null ? r.mortality_risk.toFixed(4) : r.ghost_score.toFixed(4);
    const row = [
      `"${r.file_path.replace(/"/g, '""')}"`,
      r.status,
      risk,
      r.ghost_score.toFixed(4),
      m.days_since_last_commit,
      m.total_commits,
      m.unique_authors,
      m.bug_fix_commit_ratio.toFixed(4),
      m.lines_added,
      m.lines_deleted,
      m.has_tests ? 1 : 0,
      m.churn_velocity.toFixed(4),
      `"${(m.last_author || 'unknown').replace(/"/g, '""')}"`,
      `"${m.last_commit_date || ''}"`,
    ];
    rows.push(row.join(','));
  });

  const csvContent = rows.join('\r\n');
  downloadBlob(csvContent, `tabpfn-${d.repo_name}-forensic-dataset.csv`, 'text/csv');
}

function copyBadgeSnippet() {
  if (!currentRepoUrl) return;
  const match = currentRepoUrl.match(/github\.com\/([^\/]+)\/([^\/]+)/);
  const owner = match ? match[1] : 'owner';
  const repo = match ? match[2].replace(/\.git$/, '') : 'repo';
  const origin = window.location.origin;
  const badgeUrl = `${origin}/api/badge/${owner}/${repo}.svg`;
  const snippet = `[![GitSéance Mortality](${badgeUrl})](${currentRepoUrl})`;
  navigator.clipboard.writeText(snippet);

  const badgeBtn = document.getElementById('embed-badge-btn');
  if (badgeBtn) {
    badgeBtn.textContent = '✅ Copied!';
    setTimeout(() => {
      badgeBtn.textContent = '🛡️ Badge';
    }, 2500);
  }
}

function exportMarkdownReport() {
  if (!currentSeanceData) return;
  const d = currentSeanceData;
  let md = `# 🔮 GitSéance Haunting Dossier: ${d.repo_name}\n\n`;
  md += `> Repository: ${d.repo_url}\n`;
  md += `> Prophecy: "${d.summary}"\n\n`;
  md += `## 📊 Graveyard Tally\n\n`;
  md += `- **Total Files Scanned:** ${d.total_files_scanned}\n`;
  md += `- **💀 Clinically Dead:** ${d.dead_count}\n`;
  md += `- **👻 Haunted:** ${d.haunted_count}\n`;
  md += `- **🪦 Orphaned:** ${d.orphaned_count}\n`;
  md += `- **☠️ Cursed:** ${d.cursed_count}\n`;
  md += `- **✨ Active / Fading:** ${d.alive_count}\n\n`;
  md += `## 📜 File Necropsy Ledger\n\n`;
  md += `| File Path | Status | TabPFN Mortality | Days Inactive | Commits | Top Warnings |\n`;
  md += `|---|---|---|---|---|---|\n`;

  d.haunting_reports.forEach((r) => {
    const risk = r.mortality_risk !== null ? `${Math.round(r.mortality_risk * 100)}%` : `${Math.round(r.ghost_score * 100)}%`;
    const warn = r.warnings.slice(0, 2).join('; ') || 'None';
    md += `| \`${r.file_path}\` | **${r.status.toUpperCase()}** | ${risk} | ${r.metrics.days_since_last_commit}d | ${r.metrics.total_commits} | ${warn} |\n`;
  });

  md += `\n---\n*Generated by GitSéance — AI Code Necromancer & TabPFN Mortality Predictor*\n`;

  downloadBlob(md, `gitseance-${d.repo_name}-autopsy.md`, 'text/markdown');
}

function exportJsonReport() {
  if (!currentSeanceData) return;
  const jsonStr = JSON.stringify(currentSeanceData, null, 2);
  downloadBlob(jsonStr, `gitseance-${currentSeanceData.repo_name}-ledger.json`, 'application/json');
}

function downloadBlob(content, filename, mimeType) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function generateAutopsyCertificate(report, channeling) {
  if (!report) return 'Autopsy record unavailable.';
  const m = report.metrics;
  const risk = report.mortality_risk !== null ? `${Math.round(report.mortality_risk * 100)}%` : `${Math.round(report.ghost_score * 100)}%`;
  const cleanAuthor = m.last_author || 'Unknown Contributor';
  const statusStr = report.status.toUpperCase();
  const dateStr = (m.last_commit_date || 'UNKNOWN').split('T')[0];
  const lastMsg = (m.last_commit_message || 'Initial changes').replace(/[\r\n]+/g, ' ').slice(0, 36);
  const partingWords = (channeling ? channeling.ghost_message : 'My spirit remains bound to these instructions.').slice(0, 110);
  const effortStr = channeling ? channeling.revival_patch.estimated_effort.toUpperCase() : 'MODERATE';

  return `+========================================================================+
|                     💀 OFFICIAL CODE AUTOPSY 💀                        |
|                 DEPARTMENT OF SOFTWARE NECROMANCY                      |
+========================================================================+
| DECEASED ARTIFACT   : ${report.file_path.padEnd(48, ' ')} |
| CHIEF ARCHITECT     : ${cleanAuthor.padEnd(48, ' ')} |
| DATE OF EXPIRATION  : ${(dateStr + ' (' + m.days_since_last_commit + ' days inactive)').padEnd(48, ' ')} |
| FINAL RECORDED WORDS: ${('"' + lastMsg + '"').padEnd(48, ' ')} |
| TOTAL COMMITS       : ${(m.total_commits + ' commits across file lifetime').padEnd(48, ' ')} |
| RECORDED BUS FACTOR : ${(m.unique_authors + ' author(s) recorded in blame').padEnd(48, ' ')} |
| HAUNTING STATUS     : ${statusStr.padEnd(48, ' ')} |
| TABPFN MORTALITY    : ${(risk + ' Bayesian mortality risk').padEnd(48, ' ')} |
| GHOST SEVERITY      : ${(report.ghost_score.toFixed(2) + ' / 1.00 index').padEnd(48, ' ')} |
+------------------------------------------------------------------------+
| GHOST TESTIMONY:                                                       |
| "${partingWords}"
+------------------------------------------------------------------------+
| REVIVAL EFFORT      : ${effortStr.padEnd(48, ' ')} |
| CERTIFICATE STAMP   : GITSEANCE FORENSIC ENGINE v1.0.0                 |
| AI RUNTIMES         : TABPFN-3.5 + GOOGLE GEMMA + ELEVENLABS           |
+========================================================================+`;
}

function renderFileRoster() {
  if (!currentSeanceData) return;
  const rosterContainer = document.getElementById('ledger-roster');
  if (!rosterContainer) return;

  let reports = [...currentSeanceData.haunting_reports];

  // Filter
  if (currentFilter !== 'all') {
    if (currentFilter === 'high_risk') {
      reports = reports.filter((r) => (r.mortality_risk !== null ? r.mortality_risk >= 0.7 : r.ghost_score >= 0.7));
    } else {
      reports = reports.filter((r) => r.status === currentFilter);
    }
  }

  // Search
  if (currentSearch) {
    reports = reports.filter((r) => r.file_path.toLowerCase().includes(currentSearch));
  }

  // Sort
  reports.sort((a, b) => {
    if (currentSort === 'mortality') {
      const riskA = a.mortality_risk !== null ? a.mortality_risk : a.ghost_score;
      const riskB = b.mortality_risk !== null ? b.mortality_risk : b.ghost_score;
      return riskB - riskA;
    } else if (currentSort === 'ghost_score') {
      return b.ghost_score - a.ghost_score;
    } else if (currentSort === 'age') {
      return b.metrics.days_since_last_commit - a.metrics.days_since_last_commit;
    } else if (currentSort === 'commits') {
      return b.metrics.total_commits - a.metrics.total_commits;
    }
    return 0;
  });

  rosterContainer.innerHTML = '';

  if (reports.length === 0) {
    rosterContainer.innerHTML = `
      <div style="text-align: center; padding: 40px; color: var(--terminal-muted); font-family: var(--font-mono);">
        🕸️ No haunted files match your search criteria.
      </div>
    `;
    return;
  }

  reports.forEach((report) => {
    const row = document.createElement('div');
    row.className = 'file-row';

    const riskVal = report.mortality_risk !== null ? report.mortality_risk : report.ghost_score;
    const riskPercent = Math.round(riskVal * 100);

    let riskClass = 'risk-low';
    if (riskVal >= 0.75) riskClass = 'risk-critical';
    else if (riskVal >= 0.5) riskClass = 'risk-high';
    else if (riskVal >= 0.3) riskClass = 'risk-moderate';

    const statusIcons = {
      dead: '💀',
      haunted: '👻',
      orphaned: '🪦',
      cursed: '☠️',
      fading: '🌫️',
      alive: '✨',
    };

    const warningsHtml = report.warnings
      .slice(0, 2)
      .map((w) => `<div class="warning-tag">${w}</div>`)
      .join('');

    row.innerHTML = `
      <div class="file-meta-col">
        <div class="file-path" title="${report.file_path}">
          <span>📄</span> ${report.file_path}
        </div>
        <div class="file-details">
          <span>Touched ${report.metrics.days_since_last_commit} days ago</span>
          <span>•</span>
          <span>Author: ${report.metrics.last_author || 'unknown'}</span>
          <span>•</span>
          <span>${report.metrics.total_commits} commits</span>
        </div>
      </div>

      <div>
        <span class="status-badge status-${report.status}">
          ${statusIcons[report.status] || '👻'} ${report.status}
        </span>
      </div>

      <div class="mortality-col">
        <div class="mortality-label-row">
          <span>TabPFN Mortality:</span>
          <span class="mortality-value text-${riskClass === 'risk-critical' ? 'dead' : 'ghost'}">${riskPercent}%</span>
        </div>
        <div class="meter-track">
          <div class="meter-fill ${riskClass}" style="width: ${riskPercent}%"></div>
        </div>
      </div>

      <div class="warnings-col">
        ${warningsHtml || '<div class="warning-tag text-muted">Stable ectoplasm</div>'}
      </div>

      <div>
        <button class="commune-btn" data-filepath="${report.file_path}">
          <span>🔮 COMMUNE</span>
        </button>
      </div>
    `;

    const communeBtn = row.querySelector('.commune-btn');
    communeBtn.addEventListener('click', () => {
      openSeanceChamber(report.file_path);
    });

    rosterContainer.appendChild(row);
  });
}

/* ─── The Séance Chamber (Modal Ghost Channeling) ─── */
function initModal() {
  const modal = document.getElementById('seance-modal');
  const closeBtn = document.getElementById('chamber-close-btn');

  if (closeBtn && modal) {
    closeBtn.addEventListener('click', () => {
      modal.classList.remove('active');
      GhostVoicePlayer.stop();
      SoundFX.playKeyClick();
    });
  }
}

async function openSeanceChamber(filePath) {
  const modal = document.getElementById('seance-modal');
  if (!modal) return;

  Terminal.triggerFlicker();
  SoundFX.playChannelingChime();
  modal.classList.add('active');

  // Find report for this file
  activeReportData = currentSeanceData?.haunting_reports?.find((r) => r.file_path === filePath) || null;
  activeChannelingData = null;
  activeChatHistory = [];

  const titleElem = document.getElementById('chamber-file-title');
  const monologueElem = document.getElementById('chamber-monologue');
  const whyElem = document.getElementById('chamber-why');
  const wishElem = document.getElementById('chamber-wish');
  const stepsElem = document.getElementById('chamber-steps');
  const effortElem = document.getElementById('chamber-effort');
  const serpListElem = document.getElementById('serp-replacements-list');
  const voiceBtn = document.getElementById('play-voice-btn');
  const voiceSelect = document.getElementById('voice-select');
  const canvas = document.getElementById('waveform-canvas');

  // Autopsy drawer elements
  const autopsyBtn = document.getElementById('print-autopsy-btn');
  const autopsyDrawer = document.getElementById('autopsy-drawer');
  const autopsyPre = document.getElementById('autopsy-pre');
  const closeAutopsyBtn = document.getElementById('close-autopsy-btn');
  const copyAutopsyBtn = document.getElementById('copy-autopsy-btn');
  const downloadAutopsyBtn = document.getElementById('download-autopsy-btn');

  if (autopsyDrawer) autopsyDrawer.style.display = 'none';
  const downloadVoiceBtn = document.getElementById('download-voice-btn');
  if (downloadVoiceBtn) downloadVoiceBtn.style.display = 'none';

  // Chat elements
  const chatStream = document.getElementById('ghost-chat-stream');
  const chatForm = document.getElementById('ghost-chat-form');
  const chatInput = document.getElementById('ghost-chat-input');
  const chatTag = document.getElementById('chat-model-badge');

  titleElem.textContent = filePath;
  monologueElem.innerHTML = '<em>Consulting the spirit realm via Gemma...</em>';
  whyElem.textContent = 'Channeling...';
  wishElem.textContent = 'Channeling...';
  stepsElem.innerHTML = '<li>Analyzing ancient syntax...</li>';
  serpListElem.innerHTML = '<div>Searching real-time 2026 intelligence via SerpApi...</div>';

  if (chatStream) {
    const author = activeReportData?.metrics?.last_author || 'the author';
    chatStream.innerHTML = `
      <div class="chat-bubble bubble-ghost">
        <span class="bubble-speaker">GHOST:</span> I am the spirit of ${author}. Speak your questions, living developer. What troubles you about ${filePath}?
      </div>
    `;
  }

  try {
    const res = await fetch('/api/seance/channel', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        repo_url: currentRepoUrl,
        file_path: filePath,
      }),
    });

    if (!res.ok) {
      const err = await responseError(res);
      throw new Error(err);
    }

    const data = await res.json();
    const ch = data.channeling;
    activeChannelingData = ch;

    // Typewriter effect for ghost message
    Terminal.typewriter(monologueElem, ch.ghost_message, 20);

    whyElem.textContent = ch.why_written;
    wishElem.textContent = ch.last_wish;
    effortElem.textContent = `Effort: ${ch.revival_patch.estimated_effort.toUpperCase()}`;

    // Migration steps
    stepsElem.innerHTML = '';
    ch.revival_patch.migration_steps.forEach((step) => {
      const li = document.createElement('li');
      li.textContent = step;
      stepsElem.appendChild(li);
    });

    // SerpApi Replacements
    serpListElem.innerHTML = '';
    if (data.replacements && data.replacements.length > 0) {
      data.replacements.forEach((rep) => {
        const item = document.createElement('div');
        item.className = 'replacement-item';
        item.innerHTML = `
          <div class="replacement-details">
            <span class="replacement-name">${rep.new_package}</span>
            <span class="replacement-reason">${rep.reason}</span>
          </div>
          <a href="${rep.url}" target="_blank" rel="noopener" class="replacement-link">
            Verify ↗
          </a>
        `;
        serpListElem.appendChild(item);
      });
    } else {
      serpListElem.innerHTML = `<div class="text-muted" style="font-size: 13px;">No deprecated third-party packages detected in this file.</div>`;
    }

    // Connect voice player
    if (voiceBtn) {
      voiceBtn.onclick = () => {
        const selectedVoice = voiceSelect ? voiceSelect.value : 'aria';
        GhostVoicePlayer.speak(ch.ghost_message, selectedVoice, voiceBtn, canvas);
      };
    }

    // Copy revival patch button
    const copyBtn = document.getElementById('copy-patch-btn');
    if (copyBtn) {
      copyBtn.onclick = () => {
        const patchContent = `REVIVAL BLUEPRINT FOR: ${filePath}\nSummary: ${ch.revival_patch.summary}\nEffort: ${ch.revival_patch.estimated_effort}\n\nSTEPS:\n` +
          ch.revival_patch.migration_steps.map((s, i) => `${i + 1}. ${s}`).join('\n');
        navigator.clipboard.writeText(patchContent);
        copyBtn.textContent = '✅ Copied to clipboard!';
        setTimeout(() => {
          copyBtn.textContent = '📋 Copy Revival Blueprint';
        }, 2000);
      };
    }

    // Autopsy Certificate wiring
    if (autopsyBtn && autopsyDrawer && autopsyPre) {
      autopsyBtn.onclick = () => {
        const cert = generateAutopsyCertificate(activeReportData, activeChannelingData);
        autopsyPre.textContent = cert;
        autopsyDrawer.style.display = 'block';
        SoundFX.playKeyClick();
        autopsyDrawer.scrollIntoView({ behavior: 'smooth' });
      };
    }

    if (closeAutopsyBtn && autopsyDrawer) {
      closeAutopsyBtn.onclick = () => {
        autopsyDrawer.style.display = 'none';
        SoundFX.playKeyClick();
      };
    }

    if (copyAutopsyBtn && autopsyPre) {
      copyAutopsyBtn.onclick = () => {
        navigator.clipboard.writeText(autopsyPre.textContent);
        copyAutopsyBtn.textContent = '✅ Copied!';
        setTimeout(() => { copyAutopsyBtn.textContent = '📋 Copy Certificate'; }, 2000);
      };
    }

    if (downloadAutopsyBtn && autopsyPre) {
      downloadAutopsyBtn.onclick = () => {
        const cleanName = filePath.replace(/[^a-zA-Z0-9_-]/g, '_');
        downloadBlob(autopsyPre.textContent, `${cleanName}-autopsy-certificate.txt`, 'text/plain');
      };
    }

    // Conversational Chat form handler
    if (chatForm && chatInput && chatStream) {
      chatForm.onsubmit = async (e) => {
        e.preventDefault();
        const userMsg = chatInput.value.trim();
        if (!userMsg) return;

        // Append user bubble
        appendChatBubble(chatStream, 'user', userMsg);
        chatInput.value = '';
        SoundFX.playKeyClick();

        activeChatHistory.push({ role: 'user', content: userMsg });

        // Append pending ghost bubble
        const pendingBubble = appendChatBubble(chatStream, 'ghost', '...');
        chatStream.scrollTop = chatStream.scrollHeight;

        try {
          const resp = await fetch('/api/seance/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              repo_url: currentRepoUrl,
              file_path: filePath,
              author_name: activeReportData?.metrics?.last_author || 'an ancient author',
              message: userMsg,
              history: activeChatHistory,
            }),
          });

          const chatData = await resp.json();
          const reply = chatData.reply || 'The spirit grows faint...';
          activeChatHistory.push({ role: 'ghost', content: reply });

          if (chatTag && chatData.model_used) {
            chatTag.textContent = chatData.model_used;
          }

          pendingBubble.innerHTML = `<span class="bubble-speaker">GHOST:</span> `;
          Terminal.typewriter(pendingBubble, reply, 16);
          SoundFX.playChannelingChime();
        } catch (err) {
          pendingBubble.innerHTML = `<span class="bubble-speaker">GHOST:</span> <span class="text-dead">The spirit connection was severed: ${err.message}</span>`;
        }
      };
    }

  } catch (err) {
    monologueElem.innerHTML = `<span class="text-dead">Failed to commune with spirit: ${err.message}</span>`;
  }
}

async function responseError(res) {
  try {
    const err = await res.json();
    return err.detail || 'Channeling interrupted';
  } catch {
    return 'Channeling interrupted';
  }
}

function appendChatBubble(streamElem, role, text) {
  const bubble = document.createElement('div');
  bubble.className = `chat-bubble bubble-${role}`;
  if (role === 'user') {
    bubble.innerHTML = `<span class="bubble-speaker">YOU:</span> ${escapeHtml(text)}`;
  } else {
    bubble.innerHTML = `<span class="bubble-speaker">GHOST:</span> ${escapeHtml(text)}`;
  }
  streamElem.appendChild(bubble);
  streamElem.scrollTop = streamElem.scrollHeight;
  return bubble;
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

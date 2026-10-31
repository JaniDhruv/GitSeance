/**
 * 🔮 GIT SÉANCE — Master Application Controller
 */

let currentSeanceData = null;
let currentRepoUrl = '';
let currentFilter = 'all';
let currentSort = 'mortality';
let currentSearch = '';

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

  // Export buttons
  const mdBtn = document.getElementById('export-markdown-btn');
  if (mdBtn) {
    mdBtn.addEventListener('click', () => {
      SoundFX.playKeyClick();
      exportMarkdownReport();
    });
  }

  const jsonBtn = document.getElementById('export-json-btn');
  if (jsonBtn) {
    jsonBtn.addEventListener('click', () => {
      SoundFX.playKeyClick();
      exportJsonReport();
    });
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

  titleElem.textContent = filePath;
  monologueElem.innerHTML = '<em>Consulting the spirit realm via Gemma 3...</em>';
  whyElem.textContent = 'Channeling...';
  wishElem.textContent = 'Channeling...';
  stepsElem.innerHTML = '<li>Analyzing ancient syntax...</li>';
  serpListElem.innerHTML = '<div>Searching real-time 2026 intelligence via SerpApi...</div>';

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
      const err = await res.json();
      throw new Error(err.detail || 'Channeling interrupted');
    }

    const data = await res.json();
    const ch = data.channeling;

    // Typewriter effect for ghost message
    Terminal.typewriter(monologueElem, ch.ghost_message, 22);

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
  } catch (err) {
    monologueElem.innerHTML = `<span class="text-dead">Failed to commune with spirit: ${err.message}</span>`;
  }
}

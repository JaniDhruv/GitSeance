/**
 * 🔮 GIT SÉANCE — Terminal Physics, Telemetry Logger & Typewriter Engine
 */

const Terminal = (function () {
  const consoleElem = document.getElementById('telemetry-console');

  return {
    // Append structured log to live CRT console
    log(agent, message, type = 'info') {
      if (!consoleElem) return;
      consoleElem.classList.add('active');

      const entry = document.createElement('div');
      entry.className = `log-entry agent-${agent.toLowerCase()}`;

      const now = new Date();
      const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(
        now.getMinutes()
      ).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;

      entry.innerHTML = `
        <span class="log-time">[${timeStr}]</span>
        <span class="log-agent">[${agent.toUpperCase()}]</span>
        <span class="log-msg">${message}</span>
      `;

      consoleElem.appendChild(entry);
      consoleElem.scrollTop = consoleElem.scrollHeight;
    },

    clearLogs() {
      if (consoleElem) {
        consoleElem.innerHTML = '';
        consoleElem.classList.remove('active');
      }
    },

    // CRT Screen Flicker
    triggerFlicker() {
      document.body.classList.add('screen-flicker-active');
      setTimeout(() => {
        document.body.classList.remove('screen-flicker-active');
      }, 450);
    },

    // Typewriter effect for Spirit Channeling Monologue
    typewriter(element, text, speed = 18, onComplete) {
      if (!element) return;
      element.innerHTML = '';
      let index = 0;

      const cursor = document.createElement('span');
      cursor.className = 'terminal-cursor';
      element.appendChild(cursor);

      function typeNext() {
        if (index < text.length) {
          const char = text.charAt(index);
          cursor.insertAdjacentText('beforebegin', char);
          index++;

          // Natural cadence variation
          let delay = speed;
          if (char === '.' || char === '!' || char === '?') delay = speed * 8;
          else if (char === ',') delay = speed * 4;

          setTimeout(typeNext, delay);
        } else {
          cursor.remove();
          if (onComplete) onComplete();
        }
      }

      typeNext();
    },
  };
})();

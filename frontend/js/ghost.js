/**
 * 🔮 GIT SÉANCE — Ethereal Ghost Canvas & Interactive Ectoplasm Particles
 */

(function initGhostCanvas() {
  const canvas = document.getElementById('ghost-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  let width = (canvas.width = window.innerWidth);
  let height = (canvas.height = window.innerHeight);

  window.addEventListener('resize', () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  });

  // Spectral Wisps
  const NUM_WISPS = 18;
  const wisps = [];

  for (let i = 0; i < NUM_WISPS; i++) {
    wisps.push({
      x: Math.random() * width,
      y: Math.random() * height,
      radius: Math.random() * 45 + 15,
      vx: (Math.random() - 0.5) * 0.4,
      vy: -Math.random() * 0.4 - 0.1, // Float gently upwards
      alpha: Math.random() * 0.25 + 0.05,
      pulseSpeed: Math.random() * 0.02 + 0.005,
      pulseOffset: Math.random() * Math.PI * 2,
    });
  }

  function render(time) {
    ctx.clearRect(0, 0, width, height);

    for (let i = 0; i < wisps.length; i++) {
      const w = wisps[i];
      w.x += w.vx;
      w.y += w.vy;

      // Wrap around edges
      if (w.y < -w.radius * 2) {
        w.y = height + w.radius;
        w.x = Math.random() * width;
      }
      if (w.x < -w.radius) w.x = width + w.radius;
      if (w.x > width + w.radius) w.x = -w.radius;

      const currentAlpha = w.alpha + Math.sin(time * 0.001 * w.pulseSpeed + w.pulseOffset) * 0.08;
      const grad = ctx.createRadialGradient(w.x, w.y, 0, w.x, w.y, w.radius);
      grad.addColorStop(0, `rgba(0, 255, 102, ${Math.max(0, currentAlpha)})`);
      grad.addColorStop(0.5, `rgba(0, 200, 80, ${Math.max(0, currentAlpha * 0.4)})`);
      grad.addColorStop(1, 'rgba(0, 0, 0, 0)');

      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(w.x, w.y, w.radius, 0, Math.PI * 2);
      ctx.fill();
    }

    requestAnimationFrame(render);
  }

  requestAnimationFrame(render);

  // Ectoplasm Cursor Trailer
  let lastMove = 0;
  window.addEventListener('mousemove', (e) => {
    const now = performance.now();
    if (now - lastMove < 35) return; // Throttle
    lastMove = now;

    const particle = document.createElement('div');
    particle.className = 'ectoplasm-particle';
    particle.style.left = `${e.clientX}px`;
    particle.style.top = `${e.clientY}px`;
    document.body.appendChild(particle);

    requestAnimationFrame(() => {
      const offsetX = (Math.random() - 0.5) * 20;
      const offsetY = (Math.random() - 0.5) * 20 - 15;
      particle.style.transform = `translate(${offsetX}px, ${offsetY}px) scale(0)`;
      particle.style.opacity = '0';
    });

    setTimeout(() => {
      particle.remove();
    }, 550);
  });
})();

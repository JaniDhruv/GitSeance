/**
 * 🔮 GIT SÉANCE — Web Audio Synth & ElevenLabs Voice Deck
 */

const SoundFX = (function () {
  let audioCtx = null;
  let soundEnabled = true;

  function getAudioContext() {
    if (!audioCtx) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      audioCtx = new AudioContext();
    }
    if (audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
    return audioCtx;
  }

  return {
    toggleSound(enable) {
      if (typeof enable === 'boolean') {
        soundEnabled = enable;
      } else {
        soundEnabled = !soundEnabled;
      }
      return soundEnabled;
    },

    isEnabled() {
      return soundEnabled;
    },

    // Mechanical CRT Keystroke
    playKeyClick() {
      if (!soundEnabled) return;
      try {
        const ctx = getAudioContext();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.type = 'triangle';
        osc.frequency.setValueAtTime(450 + Math.random() * 250, ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(80, ctx.currentTime + 0.04);

        gain.gain.setValueAtTime(0.04, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.04);

        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.start();
        osc.stop(ctx.currentTime + 0.05);
      } catch (e) {
        // Audio context may be blocked before gesture
      }
    },

    // Eerie Summoning Drone
    playSummonSweep() {
      if (!soundEnabled) return;
      try {
        const ctx = getAudioContext();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.type = 'sine';
        osc.frequency.setValueAtTime(110, ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(440, ctx.currentTime + 0.8);
        osc.frequency.exponentialRampToValueAtTime(220, ctx.currentTime + 1.6);

        gain.gain.setValueAtTime(0.08, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1.6);

        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.start();
        osc.stop(ctx.currentTime + 1.7);
      } catch (e) {}
    },

    // Ghost Whispering Frequency
    playChannelingChime() {
      if (!soundEnabled) return;
      try {
        const ctx = getAudioContext();
        const notes = [330, 392, 493.88, 587.33];
        notes.forEach((freq, idx) => {
          const osc = ctx.createOscillator();
          const gain = ctx.createGain();
          osc.type = 'sine';
          osc.frequency.setValueAtTime(freq, ctx.currentTime + idx * 0.12);
          gain.gain.setValueAtTime(0.03, ctx.currentTime + idx * 0.12);
          gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + idx * 0.12 + 0.6);
          osc.connect(gain);
          gain.connect(ctx.destination);
          osc.start(ctx.currentTime + idx * 0.12);
          osc.stop(ctx.currentTime + idx * 0.12 + 0.65);
        });
      } catch (e) {}
    },
  };
})();

// ElevenLabs Voice & Audio Visualizer Deck
const GhostVoicePlayer = (function () {
  let currentAudio = null;
  let visualizerId = null;

  function visualize(audioElement, canvas) {
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    const audioCtx = new AudioContext();
    const source = audioCtx.createMediaElementSource(audioElement);
    const analyser = audioCtx.createAnalyser();
    analyser.fftSize = 64;
    source.connect(analyser);
    analyser.connect(audioCtx.destination);

    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    function draw() {
      visualizerId = requestAnimationFrame(draw);
      analyser.getByteFrequencyData(dataArray);

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const barWidth = (canvas.width / bufferLength) * 1.8;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const barHeight = (dataArray[i] / 255) * canvas.height;
        ctx.fillStyle = `rgb(0, 255, 102)`;
        ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
        x += barWidth + 2;
      }
    }

    draw();
  }

  return {
    async speak(text, voice = 'aria', btnElement, canvasElement) {
      if (currentAudio) {
        currentAudio.pause();
        currentAudio = null;
        if (visualizerId) cancelAnimationFrame(visualizerId);
      }

      if (btnElement) {
        btnElement.disabled = true;
        btnElement.innerHTML = `<span>⏳ Channeling voice...</span>`;
      }

      try {
        const res = await fetch('/api/tts/speak', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text, voice }),
        });

        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || 'Voice synthesis failed');
        }

        const data = await res.json();
        const audio = new Audio(data.audio_url);
        currentAudio = audio;

        // Enable MP3 Download Button
        const downloadBtn = document.getElementById('download-voice-btn');
        if (downloadBtn && data.audio_url) {
          downloadBtn.style.display = 'inline-flex';
          downloadBtn.onclick = () => {
            const a = document.createElement('a');
            a.href = data.audio_url;
            a.download = `ghost-transmission-${voice}.mp3`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
          };
        }

        audio.onplay = () => {
          if (btnElement) {
            btnElement.disabled = false;
            btnElement.innerHTML = `<span>⏹ Stop Voice</span>`;
          }
          if (canvasElement) visualize(audio, canvasElement);
        };

        audio.onended = () => {
          if (btnElement) {
            btnElement.disabled = false;
            btnElement.innerHTML = `<span>🔊 Channel Ghost Voice</span>`;
          }
          if (visualizerId) cancelAnimationFrame(visualizerId);
        };

        audio.onerror = () => {
          throw new Error('Audio playback failed');
        };

        await audio.play();
      } catch (err) {
        console.warn('ElevenLabs TTS unavailable, falling back to Web Speech API:', err);
        if ('speechSynthesis' in window) {
          window.speechSynthesis.cancel();
          const utterance = new SpeechSynthesisUtterance(text);
          utterance.pitch = (voice === 'roger' || voice === 'charlie') ? 0.6 : 0.85;
          utterance.rate = 0.88;

          utterance.onstart = () => {
            if (btnElement) {
              btnElement.disabled = false;
              btnElement.innerHTML = `<span>⏹ Stop Voice (Ethereal)</span>`;
            }
          };
          utterance.onend = () => {
            if (btnElement) {
              btnElement.disabled = false;
              btnElement.innerHTML = `<span>🔊 Channel Ghost Voice</span>`;
            }
          };
          utterance.onerror = () => {
            if (btnElement) {
              btnElement.disabled = false;
              btnElement.innerHTML = `<span>🔊 Channel Ghost Voice</span>`;
            }
          };
          window.speechSynthesis.speak(utterance);
        } else {
          if (btnElement) {
            btnElement.disabled = false;
            btnElement.innerHTML = `<span>⚠️ Voice Unavailable</span>`;
          }
        }
      }
    },

    stop() {
      if (currentAudio) {
        currentAudio.pause();
        currentAudio = null;
      }
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
      if (visualizerId) cancelAnimationFrame(visualizerId);
    },
  };
})();

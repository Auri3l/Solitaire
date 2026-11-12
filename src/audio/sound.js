/**
 * Solitaire Web Audio Sound Synthesizer
 * 100% Procedural synthesis using Web Audio API.
 * Requires no external audio files, works offline and instantaneously.
 */

export class SoundEffects {
  constructor(enabled = true, volume = 0.5) {
    this.enabled = enabled;
    this.volume = volume;
    this.ctx = null;
    this.masterGain = null;
    this._dealNoiseBuffer = null;
  }

  _initContext() {
    if (this.ctx) return;
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
        this.masterGain = this.ctx.createGain();
        this.masterGain.gain.setValueAtTime(this.enabled ? this.volume : 0, this.ctx.currentTime);
        this.masterGain.connect(this.ctx.destination);

        const bufferSize = Math.max(1, Math.floor(this.ctx.sampleRate * 0.05));
        const buffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
        const data = buffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) {
          data[i] = (Math.random() * 2 - 1) * Math.exp(-i / (bufferSize * 0.3));
        }
        this._dealNoiseBuffer = buffer;
      }
    } catch {
      // Audio not supported or restricted
    }
  }

  setVolume(vol) {
    this.volume = Math.max(0, Math.min(1, vol));
    if (this.masterGain && this.ctx) {
      this.masterGain.gain.setValueAtTime(this.enabled ? this.volume : 0, this.ctx.currentTime);
    }
  }

  setEnabled(enabled) {
    this.enabled = Boolean(enabled);
    if (this.masterGain && this.ctx) {
      this.masterGain.gain.setValueAtTime(this.enabled ? this.volume : 0, this.ctx.currentTime);
    }
  }

  _ensureReady() {
    if (!this.enabled) return false;
    this._initContext();
    if (!this.ctx) return false;
    if (this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
    return true;
  }

  /**
   * Sound of dealing a card / drawing from stock.
   */
  playDeal() {
    if (!this._ensureReady()) return;
    const t = this.ctx.currentTime;

    const noise = this.ctx.createBufferSource();
    noise.buffer = this._dealNoiseBuffer;

    const filter = this.ctx.createBiquadFilter();
    filter.type = 'bandpass';
    filter.frequency.setValueAtTime(1400, t);
    filter.Q.setValueAtTime(3.0, t);

    const gain = this.ctx.createGain();
    gain.gain.setValueAtTime(0.4, t);
    gain.gain.exponentialRampToValueAtTime(0.001, t + 0.05);

    noise.connect(filter);
    filter.connect(gain);
    gain.connect(this.masterGain);

    noise.start(t);
  }

  /**
   * Sound of card flipping face up.
   */
  playFlip() {
    if (!this._ensureReady()) return;
    const t = this.ctx.currentTime;

    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(350, t);
    osc.frequency.exponentialRampToValueAtTime(800, t + 0.07);

    gain.gain.setValueAtTime(0.3, t);
    gain.gain.exponentialRampToValueAtTime(0.001, t + 0.07);

    osc.connect(gain);
    gain.connect(this.masterGain);

    osc.start(t);
    osc.stop(t + 0.07);
  }

  /**
   * Sound of card placed onto tableau or foundation.
   */
  playPlace() {
    if (!this._ensureReady()) return;
    const t = this.ctx.currentTime;

    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();

    osc.type = 'triangle';
    osc.frequency.setValueAtTime(180, t);
    osc.frequency.exponentialRampToValueAtTime(70, t + 0.09);

    gain.gain.setValueAtTime(0.5, t);
    gain.gain.exponentialRampToValueAtTime(0.001, t + 0.09);

    osc.connect(gain);
    gain.connect(this.masterGain);

    osc.start(t);
    osc.stop(t + 0.09);
  }

  /**
   * Sound of illegal move rejected.
   */
  playInvalid() {
    if (!this._ensureReady()) return;
    const t = this.ctx.currentTime;

    [0, 0.08].forEach(offset => {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(120, t + offset);
      osc.frequency.exponentialRampToValueAtTime(60, t + offset + 0.06);

      gain.gain.setValueAtTime(0.2, t + offset);
      gain.gain.exponentialRampToValueAtTime(0.001, t + offset + 0.06);

      osc.connect(gain);
      gain.connect(this.masterGain);

      osc.start(t + offset);
      osc.stop(t + offset + 0.06);
    });
  }

  /**
   * Sound of stock recycling (deck shuffle).
   */
  playShuffle() {
    if (!this._ensureReady()) return;
    const t = this.ctx.currentTime;

    // Series of 6 rapid card clicks
    for (let i = 0; i < 6; i++) {
      const offset = i * 0.035;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'triangle';
      osc.frequency.setValueAtTime(400 + (i * 50), t + offset);
      gain.gain.setValueAtTime(0.25, t + offset);
      gain.gain.exponentialRampToValueAtTime(0.001, t + offset + 0.03);

      osc.connect(gain);
      gain.connect(this.masterGain);

      osc.start(t + offset);
      osc.stop(t + offset + 0.03);
    }
  }

  /**
   * Quick note for Auto-Complete card placement.
   */
  playAutoCompleteNote(index = 0) {
    if (!this._ensureReady()) return;
    const t = this.ctx.currentTime;

    const scale = [261.63, 293.66, 329.63, 392.00, 440.00, 523.25, 587.33, 659.25, 783.99, 880.00];
    const freq = scale[index % scale.length];

    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(freq, t);

    gain.gain.setValueAtTime(0.25, t);
    gain.gain.exponentialRampToValueAtTime(0.001, t + 0.15);

    osc.connect(gain);
    gain.connect(this.masterGain);

    osc.start(t);
    osc.stop(t + 0.15);
  }

  /**
   * Triumphant victory fanfare.
   */
  playVictory() {
    if (!this._ensureReady()) return;
    const t = this.ctx.currentTime;

    // C major triumphant arpeggio: C4, E4, G4, C5, E5, G5, C6 (chord sustain)
    const notes = [261.63, 329.63, 392.00, 523.25, 659.25, 783.99, 1046.50];
    notes.forEach((freq, idx) => {
      const delay = idx * 0.1;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = idx === notes.length - 1 ? 'triangle' : 'sine';
      osc.frequency.setValueAtTime(freq, t + delay);

      const duration = idx === notes.length - 1 ? 1.8 : 0.4;
      gain.gain.setValueAtTime(0.35, t + delay);
      gain.gain.exponentialRampToValueAtTime(0.001, t + delay + duration);

      osc.connect(gain);
      gain.connect(this.masterGain);

      osc.start(t + delay);
      osc.stop(t + delay + duration);
    });
  }

  /**
   * Reverse whoosh for Undo.
   */
  playUndo() {
    if (!this._ensureReady()) return;
    const t = this.ctx.currentTime;

    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(600, t);
    osc.frequency.exponentialRampToValueAtTime(250, t + 0.08);

    gain.gain.setValueAtTime(0.25, t);
    gain.gain.exponentialRampToValueAtTime(0.001, t + 0.08);

    osc.connect(gain);
    gain.connect(this.masterGain);

    osc.start(t);
    osc.stop(t + 0.08);
  }

  /**
   * Sound of ceramic Vegas chip clink.
   */
  playChip() {
    if (!this._ensureReady()) return;
    const t = this.ctx.currentTime;

    [2400, 3150].forEach((freq, idx) => {
      const offset = idx * 0.012;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, t + offset);
      osc.frequency.exponentialRampToValueAtTime(freq * 0.85, t + offset + 0.04);

      gain.gain.setValueAtTime(0.35, t + offset);
      gain.gain.exponentialRampToValueAtTime(0.001, t + offset + 0.04);

      osc.connect(gain);
      gain.connect(this.masterGain);

      osc.start(t + offset);
      osc.stop(t + offset + 0.04);
    });
  }

  /**
   * Bright, metallic cash register bell chime for Break-Even / Profit.
   */
  playCashChime() {
    if (!this._ensureReady()) return;
    const t = this.ctx.currentTime;

    // Two bright bell tones: 1318.51 (E6) and 1661.22 (G#6)
    [1318.51, 1661.22].forEach((freq, idx) => {
      const offset = idx * 0.07;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'triangle';
      osc.frequency.setValueAtTime(freq, t + offset);

      gain.gain.setValueAtTime(0.4, t + offset);
      gain.gain.exponentialRampToValueAtTime(0.001, t + offset + 0.35);

      osc.connect(gain);
      gain.connect(this.masterGain);

      osc.start(t + offset);
      osc.stop(t + offset + 0.35);
    });
  }

  /**
   * Dramatic brass/synth chime for Doubling Down.
   */
  playDoubleDown() {
    if (!this._ensureReady()) return;
    const t = this.ctx.currentTime;

    const chords = [
      [392.00, 493.88], // G4, B4
      [523.25, 659.25]  // C5, E5
    ];

    chords.forEach((chord, chordIdx) => {
      const chordTime = t + (chordIdx * 0.12);
      chord.forEach(freq => {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(freq, chordTime);

        const filter = this.ctx.createBiquadFilter();
        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(1800, chordTime);
        filter.frequency.exponentialRampToValueAtTime(600, chordTime + 0.25);

        gain.gain.setValueAtTime(0.25, chordTime);
        gain.gain.exponentialRampToValueAtTime(0.001, chordTime + 0.25);

        osc.connect(filter);
        filter.connect(gain);
        gain.connect(this.masterGain);

        osc.start(chordTime);
        osc.stop(chordTime + 0.25);
      });
    });
  }

  /**
   * Joyous Vegas payout jackpot arpeggio.
   */
  playJackpot() {
    if (!this._ensureReady()) return;
    const t = this.ctx.currentTime;

    const arpeggio = [523.25, 659.25, 783.99, 987.77, 1046.50, 1174.66, 1318.51, 1567.98, 2093.00];
    arpeggio.forEach((freq, idx) => {
      const delay = idx * 0.06;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, t + delay);

      const duration = idx === arpeggio.length - 1 ? 0.8 : 0.2;
      gain.gain.setValueAtTime(0.3, t + delay);
      gain.gain.exponentialRampToValueAtTime(0.001, t + delay + duration);

      osc.connect(gain);
      gain.connect(this.masterGain);

      osc.start(t + delay);
      osc.stop(t + delay + duration);
    });
  }
}

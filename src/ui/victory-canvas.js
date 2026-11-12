/**
 * Solitaire Classic Victory Celebration
 * Recreates the iconic cascading bouncing cards celebration with canvas physics
 * and colorful confetti particle bursts using a composite offscreen trail buffer.
 */

export class VictoryCelebration {
  /**
   * @param {HTMLCanvasElement} canvas
   */
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.trailCanvas = document.createElement('canvas');
    this.trailCtx = this.trailCanvas.getContext('2d');

    this.animId = null;
    this.activeCards = [];
    this.confetti = [];
    this.isRunning = false;
    this.cardImages = new Map();

    this._handleResize = this._handleResize.bind(this);
    window.addEventListener('resize', this._handleResize);
    this._handleResize();
  }

  _handleResize() {
    if (!this.canvas) return;
    const w = window.innerWidth;
    const h = window.innerHeight;
    this.canvas.width = w;
    this.canvas.height = h;
    if (this.trailCanvas) {
      this.trailCanvas.width = w;
      this.trailCanvas.height = h;
    }
  }

  /**
   * Pre-renders card DOM elements or SVGs to Image bitmaps for maximum 60fps canvas performance.
   * @param {Array<Array<import('../engine/card.js').Card>>} foundations
   * @param {Function} getSvgFn
   */
  async prepareCards(foundations, getSvgFn) {
    this.cardImages.clear();
    const loadPromises = [];

    for (const pile of foundations) {
      for (const card of pile) {
        if (!this.cardImages.has(card.id)) {
          const rawSvg = getSvgFn(card);
          // Scale rasterization resolution to 300x435 for crisp rendering on larger desktop/retina screens
          const svgMarkup = rawSvg.replace('width="100"', 'width="300"').replace('height="145"', 'height="435"');
          const blob = new Blob([svgMarkup], { type: 'image/svg+xml;charset=utf-8' });
          const url = URL.createObjectURL(blob);
          const img = new Image();

          const p = new Promise(resolve => {
            img.onload = () => {
              this.cardImages.set(card.id, img);
              URL.revokeObjectURL(url);
              resolve();
            };
            img.onerror = () => {
              URL.revokeObjectURL(url);
              resolve();
            };
          });

          img.src = url;
          loadPromises.push(p);
        }
      }
    }

    await Promise.all(loadPromises);
  }

  /**
   * Starts the victory animation given the foundation pile screen coordinates.
   * @param {Array<{ x: number, y: number, width: number, height: number, cards: Array }>} foundationRects
   */
  start(foundationRects) {
    this.stop();
    this.isRunning = true;
    this._handleResize();
    this.canvas.style.display = 'block';

    // Clear main display and trail canvas
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    this.trailCtx.clearRect(0, 0, this.trailCanvas.width, this.trailCanvas.height);

    // Initialize bouncing card queue from top of foundations (Kings first down to Aces)
    const cardQueue = [];
    foundationRects.forEach(rect => {
      if (rect.cards && rect.cards.length > 0) {
        // Deep copy in reverse order (top card pops first)
        const reversed = [...rect.cards].reverse();
        reversed.forEach((card, idx) => {
          cardQueue.push({
            card,
            x: rect.x,
            y: rect.y,
            width: rect.width,
            height: rect.height,
            vx: (Math.random() * 8 - 4) * 1.5,
            vy: -(Math.random() * 5 + 3),
            gravity: 0.55,
            bounce: -0.82,
            delay: idx * 280 + Math.random() * 150
          });
        });
      }
    });

    // Shuffle queue slightly so cards burst excitingly from different foundations
    cardQueue.sort((a, b) => a.delay - b.delay);

    this.activeCards = [];
    let currentCardIndex = 0;
    const startTime = performance.now();

    // Spawn Confetti
    this._spawnConfetti();

    const loop = (currentTime) => {
      if (!this.isRunning) return;

      const elapsed = currentTime - startTime;

      // Check if next card should launch
      while (currentCardIndex < cardQueue.length && elapsed >= cardQueue[currentCardIndex].delay) {
        const c = cardQueue[currentCardIndex];
        // Ensure horizontal velocity is non-zero
        if (Math.abs(c.vx) < 1.5) c.vx = c.vx < 0 ? -3 : 3;
        this.activeCards.push(c);
        currentCardIndex++;
      }

      // 1. Stamp active bouncing cards onto offscreen trail buffer (leaves authentic Windows cascade trails)
      for (let i = this.activeCards.length - 1; i >= 0; i--) {
        const c = this.activeCards[i];
        const img = this.cardImages.get(c.card.id);

        if (img) {
          this.trailCtx.drawImage(img, c.x, c.y, c.width, c.height);
        } else {
          this.trailCtx.fillStyle = '#ffffff';
          this.trailCtx.fillRect(c.x, c.y, c.width, c.height);
          this.trailCtx.strokeStyle = '#000000';
          this.trailCtx.strokeRect(c.x, c.y, c.width, c.height);
        }

        // Apply physics
        c.vy += c.gravity;
        c.x += c.vx;
        c.y += c.vy;

        // Bounce off bottom floor
        if (c.y + c.height >= this.canvas.height) {
          c.y = this.canvas.height - c.height;
          c.vy *= c.bounce;
        }

        // Check if card has exited screen left/right
        if (c.x < -c.width * 2 || c.x > this.canvas.width + c.width * 2) {
          this.activeCards.splice(i, 1);
        }
      }

      // 2. Clear main display canvas for dynamic rendering
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

      // 3. Composite historical card trails
      this.ctx.drawImage(this.trailCanvas, 0, 0);

      // 4. Draw card heads at their current position
      for (const c of this.activeCards) {
        const img = this.cardImages.get(c.card.id);
        if (img) {
          this.ctx.drawImage(img, c.x, c.y, c.width, c.height);
        }
      }

      // 5. Update and render crisp confetti without streak accumulation
      this._updateConfetti();

      this.animId = requestAnimationFrame(loop);
    };

    this.animId = requestAnimationFrame(loop);
  }

  _spawnConfetti() {
    this.confetti = [];
    const colors = ['#f44336', '#e91e63', '#9c27b0', '#2196f3', '#4caf50', '#ffeb3b', '#ff9800', '#ffd700'];
    for (let i = 0; i < 120; i++) {
      this.confetti.push({
        x: Math.random() * this.canvas.width,
        y: -20 - Math.random() * 200,
        vx: Math.random() * 4 - 2,
        vy: Math.random() * 4 + 2,
        size: Math.random() * 8 + 4,
        color: colors[Math.floor(Math.random() * colors.length)],
        rotation: Math.random() * 360,
        rotSpeed: Math.random() * 8 - 4
      });
    }
  }

  _updateConfetti() {
    for (const p of this.confetti) {
      this.ctx.save();
      this.ctx.translate(p.x, p.y);
      this.ctx.rotate((p.rotation * Math.PI) / 180);
      this.ctx.fillStyle = p.color;
      this.ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size);
      this.ctx.restore();

      p.x += p.vx;
      p.y += p.vy;
      p.rotation += p.rotSpeed;

      if (p.y > this.canvas.height + 20) {
        p.y = -20;
        p.x = Math.random() * this.canvas.width;
      }
    }
  }

  stop() {
    this.isRunning = false;
    if (this.animId) {
      cancelAnimationFrame(this.animId);
      this.animId = null;
    }
    if (this.canvas) {
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
      this.canvas.style.display = 'none';
    }
    if (this.trailCtx && this.trailCanvas) {
      this.trailCtx.clearRect(0, 0, this.trailCanvas.width, this.trailCanvas.height);
    }
    this.activeCards = [];
    this.confetti = [];
  }

  destroy() {
    this.stop();
    window.removeEventListener('resize', this._handleResize);
  }
}

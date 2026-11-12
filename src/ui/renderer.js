/**
 * Solitaire Board Renderer
 * Renders game state to DOM with optimized SVG cards, responsive stacking,
 * hint indicators, and card animations.
 */

import { getCardFaceSVG, getCardBackSVG, getFoundationPlaceholderSVG, getStockPlaceholderSVG } from './cards-svg.js';
import { SUITS } from '../engine/card.js';

export class BoardRenderer {
  /**
   * @param {Object} elements - references to DOM containers
   * @param {HTMLElement} elements.stockContainer
   * @param {HTMLElement} elements.wasteContainer
   * @param {HTMLElement} elements.foundationsContainer
   * @param {HTMLElement} elements.tableauContainer
   */
  constructor(elements, cardBackTheme = 'classic') {
    this.stockEl = elements.stockContainer;
    this.wasteEl = elements.wasteContainer;
    this.foundationsEl = elements.foundationsContainer;
    this.tableauEl = elements.tableauContainer;
    this.cardBackTheme = cardBackTheme;

    this.suitOrder = [SUITS.HEARTS, SUITS.DIAMONDS, SUITS.CLUBS, SUITS.SPADES];

    this._setupSkeleton();
  }

  setCardBackTheme(theme) {
    this.cardBackTheme = theme;
  }

  _getOffsets() {
    let downOffset = 20;
    let upOffset = 38;
    let cardHeight = 183;
    let cardWidth = 126;

    if (typeof window !== 'undefined' && typeof window.getComputedStyle === 'function') {
      try {
        const targetNode = this.tableauEl || (typeof document !== 'undefined' && (document.body || document.documentElement));
        if (targetNode) {
          const style = window.getComputedStyle(targetNode);
          const up = parseFloat(style.getPropertyValue('--card-up-offset'));
          const down = parseFloat(style.getPropertyValue('--card-down-offset'));
          const h = parseFloat(style.getPropertyValue('--card-height'));
          const w = parseFloat(style.getPropertyValue('--card-width'));
          if (up && !isNaN(up) && up > 0) upOffset = up;
          if (down && !isNaN(down) && down > 0) downOffset = down;
          if (h && !isNaN(h) && h > 0) cardHeight = h;
          if (w && !isNaN(w) && w > 0) cardWidth = w;
        }
      } catch {
        // fallback
      }
    } else {
      downOffset = 18;
      upOffset = 30;
      cardHeight = 152;
      cardWidth = 105;
    }

    return { downOffset, upOffset, cardHeight, cardWidth };
  }

  _setupSkeleton() {
    // Setup 4 foundation slots
    this.foundationsEl.innerHTML = '';
    for (let f = 0; f < 4; f++) {
      const fPile = document.createElement('div');
      fPile.className = 'foundation-pile slot';
      fPile.dataset.foundationIndex = f;
      fPile.innerHTML = getFoundationPlaceholderSVG(this.suitOrder[f]);
      this.foundationsEl.appendChild(fPile);
    }

    // Setup 7 tableau columns
    this.tableauEl.innerHTML = '';
    for (let c = 0; c < 7; c++) {
      const col = document.createElement('div');
      col.className = 'tableau-column';
      col.dataset.col = c;
      this.tableauEl.appendChild(col);
    }
  }

  /**
   * Complete render pass for game state.
   * @param {import('../engine/solitaire.js').SolitaireGame} game
   */
  render(game) {
    this.renderStock(game);
    this.renderWaste(game);
    this.renderFoundations(game);
    this.renderTableau(game);
  }

  renderStock(game) {
    this.stockEl.innerHTML = '';
    if (game.stock.length > 0) {
      const cardEl = document.createElement('div');
      cardEl.className = 'card face-down stock-card';
      cardEl.dataset.pile = 'stock';
      cardEl.innerHTML = getCardBackSVG(this.cardBackTheme);

      // Card count badge
      const badge = document.createElement('div');
      badge.className = 'stock-badge';
      badge.textContent = game.stock.length;
      cardEl.appendChild(badge);

      this.stockEl.appendChild(cardEl);
    } else {
      // Empty stock: show recycle slot
      const emptySlot = document.createElement('div');
      emptySlot.className = 'stock-empty-slot slot';
      emptySlot.dataset.pile = 'stock';
      emptySlot.title = game.waste.length > 0 ? 'Click to recycle waste' : 'Stock empty';
      emptySlot.innerHTML = getStockPlaceholderSVG();

      if (game.waste.length > 0) {
        emptySlot.classList.add('can-recycle');
      }
      this.stockEl.appendChild(emptySlot);
    }
  }

  renderWaste(game) {
    this.wasteEl.innerHTML = '';
    if (game.waste.length === 0) {
      const placeholder = document.createElement('div');
      placeholder.className = 'waste-placeholder slot';
      this.wasteEl.appendChild(placeholder);
      return;
    }

    // In Draw 3 mode, show up to top 3 cards fanned horizontally
    const visibleCount = game.drawMode === 3 ? Math.min(3, game.waste.length) : 1;
    const startIndex = game.waste.length - visibleCount;
    const effectiveWidth = (this.wasteEl && this.wasteEl.clientWidth) || this._getOffsets().cardWidth || 126;
    // Landscape phones stack the waste under the stock, so the Draw 3 fan runs downwards there
    const fanDown = typeof window !== 'undefined' && typeof window.getComputedStyle === 'function' &&
      window.getComputedStyle(this.wasteEl).getPropertyValue('--waste-fan').trim() === 'vertical';
    const fanOffset = fanDown
      ? Math.max(10, Math.round(this._getOffsets().cardHeight * 0.2))
      : Math.min(38, Math.max(12, Math.round(effectiveWidth * 0.24)));

    for (let i = startIndex; i < game.waste.length; i++) {
      const card = game.waste[i];
      const isTop = i === game.waste.length - 1;
      const offsetIndex = i - startIndex;

      const cardEl = document.createElement('div');
      cardEl.className = `card face-up waste-card ${card.isRed ? 'red' : 'black'}`;
      cardEl.dataset.pile = 'waste';
      cardEl.dataset.id = card.id;

      if (isTop) {
        cardEl.classList.add('top-waste');
      }

      // Horizontal fan offset in Draw 3 using left so transforms do not cause card jump
      if (game.drawMode === 3 && visibleCount > 1 && fanDown) {
        cardEl.style.left = '0px';
        cardEl.style.top = `${offsetIndex * fanOffset}px`;
        cardEl.dataset.originalLeft = 0;
        cardEl.style.zIndex = `${offsetIndex + 1}`;
        cardEl.dataset.originalZIndex = `${offsetIndex + 1}`;
      } else if (game.drawMode === 3 && visibleCount > 1) {
        cardEl.style.left = `${offsetIndex * fanOffset}px`;
        cardEl.dataset.originalLeft = offsetIndex * fanOffset;
        cardEl.style.zIndex = `${offsetIndex + 1}`;
        cardEl.dataset.originalZIndex = `${offsetIndex + 1}`;
      } else {
        cardEl.style.left = '0px';
        cardEl.dataset.originalLeft = 0;
        cardEl.style.zIndex = '1';
        cardEl.dataset.originalZIndex = '1';
      }

      cardEl.innerHTML = getCardFaceSVG(card);
      this.wasteEl.appendChild(cardEl);
    }
  }

  renderFoundations(game) {
    const fSlots = this.foundationsEl.querySelectorAll('.foundation-pile');
    fSlots.forEach((slot, fIdx) => {
      slot.innerHTML = '';
      const pile = game.foundations[fIdx];

      if (pile.length === 0) {
        slot.innerHTML = getFoundationPlaceholderSVG(this.suitOrder[fIdx]);
      } else {
        const topCard = pile[pile.length - 1];
        const cardEl = document.createElement('div');
        cardEl.className = `card face-up ${topCard.isRed ? 'red' : 'black'}`;
        cardEl.dataset.pile = 'foundation';
        cardEl.dataset.foundationIndex = fIdx;
        cardEl.dataset.id = topCard.id;
        cardEl.style.zIndex = '1';
        cardEl.dataset.originalZIndex = '1';
        cardEl.innerHTML = getCardFaceSVG(topCard);

        slot.appendChild(cardEl);
      }
    });
  }

  renderTableau(game) {
    const cols = this.tableauEl.querySelectorAll('.tableau-column');
    const baseOffsets = this._getOffsets();
    // Measure column positions before mutating any column DOM to avoid layout thrashing
    const colTops = Array.from(cols).map(colEl => (
      typeof colEl.getBoundingClientRect === 'function' ? colEl.getBoundingClientRect().top : 0
    ));

    cols.forEach((colEl, colIdx) => {
      colEl.innerHTML = '';
      const colCards = game.tableau[colIdx];

      // Calculate dynamic vertical offset based on column height and card size
      let { downOffset, upOffset, cardHeight } = baseOffsets;

      if (colCards.length === 0) {
        colEl.style.minHeight = `${cardHeight}px`;
        const emptySlot = document.createElement('div');
        emptySlot.className = 'empty-column-slot slot';
        colEl.appendChild(emptySlot);
        return;
      }

      const totalCards = colCards.length;
      if (totalCards > 12) {
        downOffset = Math.round(downOffset * 0.72);
        upOffset = Math.round(upOffset * 0.73);
      } else if (totalCards > 8) {
        downOffset = Math.round(downOffset * 0.85);
        upOffset = Math.round(upOffset * 0.87);
      }

      ({ downOffset, upOffset } = this._fitColumnToScreen(colTops[colIdx], colCards, downOffset, upOffset, cardHeight));

      let currentTop = 0;
      let lastCardTop = 0;

      colCards.forEach((card, cardIdx) => {
        const isFaceUp = card.faceUp;
        const cardEl = document.createElement('div');
        cardEl.className = `card ${isFaceUp ? 'face-up' : 'face-down'} ${card.isRed ? 'red' : 'black'}`;
        cardEl.dataset.pile = 'tableau';
        cardEl.dataset.col = colIdx;
        cardEl.dataset.index = cardIdx;
        cardEl.dataset.id = card.id;

        cardEl.style.top = `${currentTop}px`;
        cardEl.style.zIndex = `${cardIdx + 1}`;
        cardEl.dataset.originalTop = currentTop;
        cardEl.dataset.originalZIndex = `${cardIdx + 1}`;

        cardEl.innerHTML = isFaceUp ? getCardFaceSVG(card) : getCardBackSVG(this.cardBackTheme);
        colEl.appendChild(cardEl);

        lastCardTop = currentTop;
        // Next card offset
        currentTop += isFaceUp ? upOffset : downOffset;
      });

      // Adjust column height to precisely fit all cards
      colEl.style.minHeight = `${lastCardTop + cardHeight}px`;
    });
  }

  /**
   * When cards are sized to the screen (phones), squeezes a long column's offsets so the whole
   * column stays above the bottom edge instead of running under the ad banner.
   */
  _fitColumnToScreen(colRectTop, colCards, downOffset, upOffset, cardHeight) {
    if (typeof window === 'undefined' || typeof document === 'undefined' || !document.body ||
        !document.body.style.getPropertyValue('--card-width')) {
      return { downOffset, upOffset };
    }
    // The body is the scroller (html/body are 100% high), so add its scroll as well as the window's
    const scrolled = (window.scrollY || 0) + (document.body.scrollTop || 0);
    const colTop = colRectTop + scrolled;
    const container = document.getElementById('app-container');
    const safeBottom = container ? parseFloat(window.getComputedStyle(container).paddingBottom) || 0 : 0;
    const available = window.innerHeight - safeBottom - colTop - 6 - cardHeight;
    let downs = 0;
    let ups = 0;
    for (let i = 0; i < colCards.length - 1; i++) {
      if (colCards[i].faceUp) ups++; else downs++;
    }
    const natural = downs * downOffset + ups * upOffset;
    if (natural <= available || natural === 0) return { downOffset, upOffset };

    // Keep face-up rank corners readable and face-down edges visible
    const minUp = Math.round(cardHeight * 0.13);
    const minDown = 3;
    const scale = Math.max(0, available) / natural;
    const down = Math.max(minDown, Math.floor(downOffset * scale));
    // Face-up cards get whatever room the squeezed face-down cards leave
    const up = ups > 0
      ? Math.min(upOffset, Math.max(minUp, Math.floor((available - downs * down) / ups)))
      : upOffset;
    return { downOffset: down, upOffset: up };
  }

  /**
   * Highlights a hint on the board.
   * @param {Object} hint
   */
  highlightHint(hint) {
    this.clearHintHighlight();

    // Find source card element
    let sourceEl = null;
    if (hint.source.pile === 'stock') {
      sourceEl = this.stockEl.querySelector('.card, .stock-empty-slot');
    } else if (hint.source.pile === 'waste') {
      sourceEl = this.wasteEl.querySelector('.top-waste') || this.wasteEl.querySelector('.card');
    } else if (hint.source.pile === 'tableau') {
      sourceEl = this.tableauEl.querySelector(`.card[data-col="${hint.source.col}"][data-index="${hint.source.cardIndex}"]`);
    }

    // Find target slot element
    let targetEl = null;
    if (hint.target.pile === 'foundation') {
      targetEl = this.foundationsEl.querySelector(`.foundation-pile[data-foundation-index="${hint.target.foundationIndex}"]`);
    } else if (hint.target.pile === 'tableau') {
      const colEl = this.tableauEl.querySelector(`.tableau-column[data-col="${hint.target.col}"]`);
      if (colEl) {
        const cards = colEl.querySelectorAll('.card');
        targetEl = cards.length > 0 ? cards[cards.length - 1] : colEl.querySelector('.empty-column-slot');
      }
    } else if (hint.target.pile === 'waste') {
      targetEl = this.wasteEl.querySelector('.card, .waste-placeholder');
    } else if (hint.target.pile === 'stock') {
      targetEl = this.stockEl.querySelector('.stock-empty-slot, .card');
    }

    if (sourceEl) {
      sourceEl.classList.add('hint-source-glow');
    }
    if (targetEl) {
      targetEl.classList.add('hint-target-glow');
    }
  }

  clearHintHighlight() {
    const glowing = document.querySelectorAll('.hint-source-glow, .hint-target-glow');
    glowing.forEach(el => {
      el.classList.remove('hint-source-glow', 'hint-target-glow');
    });
  }

  /**
   * Smoothly animates a card flying from its current position to target element.
   * @param {HTMLElement} cardEl
   * @param {HTMLElement} targetEl
   * @returns {Promise<void>}
   */
  animateCardFly(cardEl, targetEl) {
    return new Promise(resolve => {
      if (!cardEl || !targetEl) return resolve();

      const startRect = cardEl.getBoundingClientRect();
      const endRect = targetEl.getBoundingClientRect();

      const clone = cardEl.cloneNode(true);
      clone.classList.add('card-flying');
      clone.style.position = 'fixed';
      clone.style.left = `${startRect.left}px`;
      clone.style.top = `${startRect.top}px`;
      clone.style.width = `${startRect.width}px`;
      clone.style.height = `${startRect.height}px`;
      clone.style.zIndex = '9999';
      clone.style.pointerEvents = 'none';
      clone.style.transition = 'all 0.28s cubic-bezier(0.25, 1, 0.5, 1)';
      document.body.appendChild(clone);

      cardEl.style.visibility = 'hidden';

      // Force layout then animate
      requestAnimationFrame(() => {
        clone.style.left = `${endRect.left}px`;
        clone.style.top = `${endRect.top}px`;
      });

      setTimeout(() => {
        clone.remove();
        cardEl.style.visibility = '';
        resolve();
      }, 300);
    });
  }
}

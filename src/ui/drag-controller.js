/**
 * Solitaire Drag and Drop Controller
 * High-performance pointer-events drag-and-drop with multi-card stack dragging,
 * touch support, target hit-testing, visual feedback, and smooth spring-back.
 */

export class DragController {
  /**
   * @param {Object} options
   * @param {HTMLElement} options.boardElement
   * @param {Function} options.isValidMoveFn - (source, target) => boolean
   * @param {Function} options.onDrop - (source, target) => void
   * @param {Function} options.onClick - (cardId, source) => void
   * @param {Object} [options.haptics] - Optional HapticFeedback instance
   */
  constructor({ boardElement, isValidMoveFn, onDrop, onClick, haptics = null }) {
    this.board = boardElement;
    this.isValidMove = isValidMoveFn;
    this.onDrop = onDrop;
    this.onClick = onClick;
    this.haptics = haptics;

    this.isDragging = false;
    this.dragStarted = false;
    this.dragData = null;
    this.draggedElements = [];
    this.originalStyles = [];
    this.startX = 0;
    this.startY = 0;
    this.currentX = 0;
    this.currentY = 0;
    this.highlightedTarget = null;
    this._animateBackTimer = null;
    this._activePointerId = null;

    this.DRAG_THRESHOLD = 6; // pixels

    this._onPointerDown = this._onPointerDown.bind(this);
    this._onPointerMove = this._onPointerMove.bind(this);
    this._onPointerUp = this._onPointerUp.bind(this);
    this._onPointerCancel = this._onPointerCancel.bind(this);
    this._onContextMenu = this._onContextMenu.bind(this);

    this.board.addEventListener('pointerdown', this._onPointerDown);
    this.board.addEventListener('contextmenu', this._onContextMenu);
    // Taps already auto-move on pointerup; listening for dblclick as well would
    // fire a second auto-move on whatever card ended up under the pointer.
  }

  _onContextMenu(e) {
    e.preventDefault();
    // A touch long-press fires contextmenu while the pointer is still down;
    // its pointerup will already register the tap, so don't move twice.
    if (this.dragStarted || this._activePointerId !== null) return;
    const cardEl = e.target.closest('.card.face-up');
    if (!cardEl) return;

    const sourcePile = cardEl.dataset.pile;
    const cardId = cardEl.dataset.id;
    let source = null;

    if (sourcePile === 'tableau') {
      const col = parseInt(cardEl.dataset.col, 10);
      const cardIndex = parseInt(cardEl.dataset.index, 10);
      source = { pile: 'tableau', col, cardIndex };
    } else if (sourcePile === 'waste') {
      if (!cardEl.classList.contains('top-waste')) return;
      source = { pile: 'waste' };
    } else if (sourcePile === 'foundation') {
      const foundationIndex = parseInt(cardEl.dataset.foundationIndex, 10);
      source = { pile: 'foundation', foundationIndex };
    }

    if (source && cardId) {
      this.onClick(cardId, source);
    }
  }

  _onPointerDown(e) {
    // Ignore extra fingers while another pointer is still pressed
    if (this._activePointerId !== null) return;

    // If a previous animation was running, finish it immediately
    if (this._animateBackTimer) {
      clearTimeout(this._animateBackTimer);
      this._animateBackTimer = null;
      this._resetDragState();
    }

    // Only primary mouse button or touch
    if (e.button !== 0 && e.pointerType === 'mouse') return;

    // Find closest card element
    const cardEl = e.target.closest('.card');
    if (!cardEl) return;

    // Must be face up to drag
    if (!cardEl.classList.contains('face-up')) return;

    const sourcePile = cardEl.dataset.pile;
    const cardId = cardEl.dataset.id;
    let source = null;
    let elements = [];

    if (sourcePile === 'tableau') {
      const col = parseInt(cardEl.dataset.col, 10);
      const cardIndex = parseInt(cardEl.dataset.index, 10);
      source = { pile: 'tableau', col, cardIndex };

      // Grab this card and all cards above it in the same column
      const columnEl = cardEl.closest('.tableau-column');
      if (columnEl) {
        const allCardsInCol = Array.from(columnEl.querySelectorAll('.card'));
        const domIndex = allCardsInCol.indexOf(cardEl);
        elements = domIndex !== -1 ? allCardsInCol.slice(domIndex) : [cardEl];
      }
    } else if (sourcePile === 'waste') {
      // In Draw 3, only top card of waste can be moved
      if (!cardEl.classList.contains('top-waste')) return;
      source = { pile: 'waste' };
      elements = [cardEl];
    } else if (sourcePile === 'foundation') {
      const foundationIndex = parseInt(cardEl.dataset.foundationIndex, 10);
      source = { pile: 'foundation', foundationIndex };
      elements = [cardEl];
    }

    if (!source || elements.length === 0) return;

    this.dragData = {
      cardId,
      source,
      pointerId: e.pointerId,
      cardRect: cardEl.getBoundingClientRect()
    };

    this.draggedElements = elements;
    this.originalStyles = elements.map(el => ({
      zIndex: el.style.zIndex || el.dataset.originalZIndex || '',
      pointerEvents: el.style.pointerEvents || '',
      transform: el.style.transform || '',
      transition: el.style.transition || ''
    }));
    this.startX = e.clientX;
    this.startY = e.clientY;
    this.currentX = e.clientX;
    this.currentY = e.clientY;
    this.isDragging = false;
    this.dragStarted = true;
    this._activePointerId = e.pointerId ?? 'primary';

    window.addEventListener('pointermove', this._onPointerMove);
    window.addEventListener('pointerup', this._onPointerUp);
    window.addEventListener('pointercancel', this._onPointerCancel);
  }

  _isActivePointer(e) {
    return e.pointerId === undefined || this._activePointerId === 'primary' || e.pointerId === this._activePointerId;
  }

  _onPointerMove(e) {
    if (!this.dragStarted || !this.dragData || !this._isActivePointer(e)) return;

    const dx = e.clientX - this.startX;
    const dy = e.clientY - this.startY;
    const distance = Math.hypot(dx, dy);

    if (!this.isDragging) {
      if (distance >= this.DRAG_THRESHOLD) {
        this.isDragging = true;
        this._startDrag();
      } else {
        return;
      }
    }

    this.currentX = e.clientX;
    this.currentY = e.clientY;

    // Move dragged card stack
    this.draggedElements.forEach(el => {
      el.style.transform = `translate3d(${dx}px, ${dy}px, 0) scale(1.04)`;
    });

    // Hit-test targets
    this._checkDropTargets(e.clientX, e.clientY);
  }

  _startDrag() {
    this.haptics?.tick();
    this.draggedElements.forEach((el, index) => {
      el.classList.add('is-dragging');
      el.style.zIndex = `${1000 + index}`;
      el.style.pointerEvents = 'none';
      el.style.transition = 'none';
    });
  }

  _checkDropTargets(x, y) {
    const targets = this._getAllDropTargets();
    let bestTarget = null;
    let maxOverlap = 0;

    const leadCardRect = this.draggedElements[0].getBoundingClientRect();

    targets.forEach(target => {
      const targetRect = target.element.getBoundingClientRect();
      const overlap = this._calculateOverlap(leadCardRect, targetRect);

      if (overlap > 0) {
        // Validate if this move is legal
        if (this.isValidMove(this.dragData.source, target.data)) {
          if (overlap > maxOverlap) {
            maxOverlap = overlap;
            bestTarget = target;
          }
        }
      }
    });

    if (this.highlightedTarget !== (bestTarget ? bestTarget.element : null)) {
      if (this.highlightedTarget) {
        this.highlightedTarget.classList.remove('drop-hover');
      }
      this.highlightedTarget = bestTarget ? bestTarget.element : null;
      if (this.highlightedTarget) {
        this.highlightedTarget.classList.add('drop-hover');
        this.haptics?.snapTarget();
      }
    }
  }

  _calculateOverlap(r1, r2) {
    const xOverlap = Math.max(0, Math.min(r1.right, r2.right) - Math.max(r1.left, r2.left));
    const yOverlap = Math.max(0, Math.min(r1.bottom, r2.bottom) - Math.max(r1.top, r2.top));
    return xOverlap * yOverlap;
  }

  _getAllDropTargets() {
    const targets = [];

    // Foundation piles
    const foundationSlots = this.board.querySelectorAll('.foundation-pile');
    foundationSlots.forEach(el => {
      const foundationIndex = parseInt(el.dataset.foundationIndex, 10);
      targets.push({
        element: el,
        data: { pile: 'foundation', foundationIndex }
      });
    });

    // Tableau columns
    const tableauCols = this.board.querySelectorAll('.tableau-column');
    tableauCols.forEach(el => {
      const col = parseInt(el.dataset.col, 10);
      targets.push({
        element: el,
        data: { pile: 'tableau', col }
      });
    });

    return targets;
  }

  _onPointerUp(e) {
    if (!this._isActivePointer(e)) return;
    this._cleanupPointerListeners();

    if (!this.dragStarted || !this.dragData) return;

    if (!this.isDragging) {
      // It was a tap / click!
      const { cardId, source } = this.dragData;
      this._resetDragState();
      this.onClick(cardId, source);
      return;
    }

    // Ensure drop target is evaluated at final release position
    this._checkDropTargets(e.clientX, e.clientY);

    // It was a drag: check where it landed
    const targetElement = this.highlightedTarget;
    let targetData = null;

    if (targetElement) {
      if (targetElement.classList.contains('foundation-pile')) {
        targetData = {
          pile: 'foundation',
          foundationIndex: parseInt(targetElement.dataset.foundationIndex, 10)
        };
      } else if (targetElement.classList.contains('tableau-column')) {
        targetData = {
          pile: 'tableau',
          col: parseInt(targetElement.dataset.col, 10)
        };
      }
    }

    if (this.highlightedTarget) {
      this.highlightedTarget.classList.remove('drop-hover');
      this.highlightedTarget = null;
    }

    if (targetData && this.isValidMove(this.dragData.source, targetData)) {
      // Valid Drop!
      const source = this.dragData.source;
      this._resetDragState();
      this.onDrop(source, targetData);
    } else {
      // Invalid Drop: animate back
      this._animateBack();
    }
  }

  _animateBack() {
    this.haptics?.invalid();
    if (this._animateBackTimer) {
      clearTimeout(this._animateBackTimer);
    }
    const elements = [...this.draggedElements];
    elements.forEach((el, index) => {
      const orig = this.originalStyles ? this.originalStyles[index] : null;
      el.style.pointerEvents = (orig && orig.pointerEvents) ? orig.pointerEvents : '';
      el.style.transition = 'transform 0.22s cubic-bezier(0.2, 0.9, 0.3, 1)';
      el.style.transform = 'translate3d(0, 0, 0) scale(1)';
    });

    this._animateBackTimer = setTimeout(() => {
      this._animateBackTimer = null;
      this._resetDragState();
    }, 230);
  }

  _onPointerCancel(e) {
    if (e && !this._isActivePointer(e)) return;
    this._cleanupPointerListeners();
    if (this.isDragging) {
      this._animateBack();
    } else {
      this._resetDragState();
    }
  }

  _cleanupPointerListeners() {
    window.removeEventListener('pointermove', this._onPointerMove);
    window.removeEventListener('pointerup', this._onPointerUp);
    window.removeEventListener('pointercancel', this._onPointerCancel);
    this._activePointerId = null;
  }

  _resetDragState() {
    this.draggedElements.forEach((el, index) => {
      el.classList.remove('is-dragging');
      const orig = this.originalStyles ? this.originalStyles[index] : null;
      const origZ = (orig && orig.zIndex) || el.dataset.originalZIndex || '';
      if (origZ) {
        el.style.zIndex = origZ;
      } else {
        el.style.zIndex = '';
      }
      el.style.pointerEvents = (orig && orig.pointerEvents) ? orig.pointerEvents : '';
      el.style.transform = (orig && orig.transform) ? orig.transform : '';
      el.style.transition = (orig && orig.transition) ? orig.transition : '';
    });

    if (this.highlightedTarget) {
      this.highlightedTarget.classList.remove('drop-hover');
      this.highlightedTarget = null;
    }

    this.isDragging = false;
    this.dragStarted = false;
    this.dragData = null;
    this.draggedElements = [];
    this.originalStyles = [];
  }

  destroy() {
    this._cleanupPointerListeners();
    if (this._animateBackTimer) {
      clearTimeout(this._animateBackTimer);
      this._animateBackTimer = null;
    }
    if (this.dragStarted) {
      this._resetDragState();
    }
    this.board.removeEventListener('pointerdown', this._onPointerDown);
    this.board.removeEventListener('contextmenu', this._onContextMenu);
  }
}

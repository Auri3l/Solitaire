/**
 * Solitaire Haptic Feedback Engine
 * Provides crisp, tactile haptic sensations when playing on phone / mobile devices.
 * Supports:
 * 1. Native Android bridge (`window.AndroidHaptics`) via WebView JavascriptInterface
 * 2. Standard W3C Web Vibration API (`navigator.vibrate`)
 * Safe across all browsers, desktops, and headless environments.
 */

export const HAPTIC_PATTERNS = {
  // Ultra-light selection / drag pickup (10ms)
  TICK: 10,
  // Snapping card over valid drop target (8ms)
  SNAP: 8,
  // Card placed on tableau (18ms)
  PLACE: 18,
  // Card sent to foundation pile (25ms)
  FOUNDATION: 25,
  // Hidden card flip (14ms)
  FLIP: 14,
  // Drawing from stock (15ms)
  DEAL: 15,
  // Recycling / reshuffling waste back to stock
  RECYCLE: [15, 35, 20],
  // Undo move (16ms)
  UNDO: 16,
  // Vegas Double Down
  DOUBLE_DOWN: [20, 35, 30],
  // Illegal move / buzz warning
  INVALID: [30, 40, 30],
  // Micro tick during rapid auto-complete cascade
  AUTO_COMPLETE: 8,
  // Victory celebration fanfare
  VICTORY: [40, 60, 40, 60, 80, 60, 100]
};

export class HapticFeedback {
  /**
   * @param {boolean} [enabled=true]
   */
  constructor(enabled = true) {
    this.enabled = Boolean(enabled);
    this._lastSnapTime = -Infinity;
  }

  /**
   * Toggle haptic feedback on or off
   * @param {boolean} enabled
   */
  setEnabled(enabled) {
    this.enabled = Boolean(enabled);
  }

  /**
   * Check if haptic hardware or vibration API is available
   * @returns {boolean}
   */
  get isSupported() {
    if (typeof window !== 'undefined' && window.AndroidHaptics) {
      if (typeof window.AndroidHaptics.isAvailable === 'function') {
        try {
          return Boolean(window.AndroidHaptics.isAvailable());
        } catch {
          return true;
        }
      }
      return true;
    }
    if (typeof navigator !== 'undefined' && typeof navigator.vibrate === 'function') {
      return true;
    }
    return false;
  }

  /**
   * Check if running on mobile device or phone
   * @returns {boolean}
   */
  get isMobile() {
    if (typeof window === 'undefined') return false;
    if (window.AndroidHaptics) return true;
    const ua = (typeof navigator !== 'undefined' && navigator.userAgent) ? navigator.userAgent : '';
    const hasTouch = (typeof navigator !== 'undefined' && (navigator.maxTouchPoints > 0 || 'ontouchstart' in window));
    return hasTouch && /android|iphone|ipad|ipod|mobile/i.test(ua);
  }

  /**
   * Execute vibration or native haptic call
   * @param {number|number[]} pattern - Duration in ms or pattern array
   * @param {string} [presetType] - Semantic type hint for native bridges ('tick', 'snap', 'place', 'foundation', 'click', 'error')
   * @returns {boolean}
   */
  trigger(pattern, presetType = null) {
    if (!this.enabled) return false;

    // 1. Try Android Native Bridge if running inside Android WebView shell
    if (typeof window !== 'undefined' && window.AndroidHaptics) {
      try {
        if (Array.isArray(pattern)) {
          if (typeof window.AndroidHaptics.vibratePattern === 'function') {
            return Boolean(window.AndroidHaptics.vibratePattern(JSON.stringify(pattern)));
          } else if (typeof window.AndroidHaptics.vibrate === 'function') {
            return Boolean(window.AndroidHaptics.vibrate(pattern[0] || 15));
          }
        }
        if (presetType && typeof window.AndroidHaptics.performHaptic === 'function') {
          return Boolean(window.AndroidHaptics.performHaptic(presetType));
        }
        if (typeof window.AndroidHaptics.vibrate === 'function') {
          return Boolean(window.AndroidHaptics.vibrate(pattern));
        }
      } catch {
        // Fall back to navigator.vibrate
      }
    }

    // 2. Try standard W3C Web Vibration API
    if (typeof navigator !== 'undefined' && typeof navigator.vibrate === 'function') {
      try {
        return Boolean(navigator.vibrate(pattern));
      } catch {
        // May fail if permissions policy or user gesture requirement is not met
      }
    }

    return false;
  }

  /**
   * Tactile tick on card lift, drag start, or button press
   */
  tick() {
    return this.trigger(HAPTIC_PATTERNS.TICK, 'tick');
  }

  /**
   * Subtle tick when card enters a valid drop target zone
   * Throttled with a 90ms debounce to avoid vibration chatter
   */
  snapTarget() {
    const now = (typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now();
    if (now - this._lastSnapTime < 90) {
      return false;
    }
    this._lastSnapTime = now;
    return this.trigger(HAPTIC_PATTERNS.SNAP, 'snap');
  }

  /**
   * Card dropped or auto-moved to tableau
   */
  place() {
    return this.trigger(HAPTIC_PATTERNS.PLACE, 'place');
  }

  /**
   * Card promoted to foundation
   */
  foundation() {
    return this.trigger(HAPTIC_PATTERNS.FOUNDATION, 'foundation');
  }

  /**
   * Card flipped face-up
   */
  flip() {
    return this.trigger(HAPTIC_PATTERNS.FLIP, 'click');
  }

  /**
   * Card drawn from stock
   */
  deal() {
    return this.trigger(HAPTIC_PATTERNS.DEAL, 'click');
  }

  /**
   * Stock recycled
   */
  recycle() {
    return this.trigger(HAPTIC_PATTERNS.RECYCLE, 'recycle');
  }

  /**
   * Invalid move or blocked action
   */
  invalid() {
    return this.trigger(HAPTIC_PATTERNS.INVALID, 'error');
  }

  /**
   * Move undone
   */
  undo() {
    return this.trigger(HAPTIC_PATTERNS.UNDO, 'click');
  }

  /**
   * Vegas Double Down activated
   */
  doubleDown() {
    return this.trigger(HAPTIC_PATTERNS.DOUBLE_DOWN, 'double_down');
  }

  /**
   * Auto-complete card cascade step
   */
  autoCompleteStep() {
    return this.trigger(HAPTIC_PATTERNS.AUTO_COMPLETE, 'tick');
  }

  /**
   * Victory celebration fanfare
   */
  victory() {
    return this.trigger(HAPTIC_PATTERNS.VICTORY, 'victory');
  }
}

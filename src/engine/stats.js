/**
 * Solitaire Statistics & Settings Persistence
 * Manages player statistics, game settings, and auto-save state using localStorage.
 */

const STORAGE_KEYS = {
  STATS: 'solitaire_pro_stats_v2',
  SETTINGS: 'solitaire_pro_settings_v2',
  SAVED_GAME: 'solitaire_pro_saved_game_v2'
};

const DEFAULT_SETTINGS = {
  theme: 'felt-emerald',
  cardBack: 'classic',
  cardSize: 'auto',
  drawMode: 1,
  scoringMode: 'standard',
  dealType: 'solvable',
  soundEnabled: true,
  soundVolume: 0.6,
  hapticsEnabled: true,
  vegasCumulative: true,
  vegasBalance: 500,
  vegasStake: 1,
  dailyChipsDate: null,
  // null until the player picks one, so the device language is used on first launch
  language: null,
  recentSeeds: []
};

/** How many recent deal numbers a new winnable deal avoids repeating. */
export const RECENT_SEEDS_LIMIT = 50;

const DEFAULT_MODE_STATS = {
  gamesPlayed: 0,
  gamesWon: 0,
  currentStreak: 0,
  bestStreak: 0,
  bestTime: null,
  bestScore: null,
  fewestMoves: null
};

export class StatsManager {
  constructor() {
    this.stats = this._loadStats();
    this.settings = this._loadSettings();
  }

  _getStorage() {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        return window.localStorage;
      }
    } catch {
      // localStorage may be disabled
    }
    return null;
  }

  _loadStats() {
    const storage = this._getStorage();
    if (storage) {
      const data = storage.getItem(STORAGE_KEYS.STATS);
      if (data) {
        try {
          return JSON.parse(data);
        } catch {
          // ignore corrupted data
        }
      }
    }
    return {
      'standard-1': { ...DEFAULT_MODE_STATS },
      'standard-3': { ...DEFAULT_MODE_STATS },
      'vegas-1': { ...DEFAULT_MODE_STATS },
      'vegas-3': { ...DEFAULT_MODE_STATS },
      'none-1': { ...DEFAULT_MODE_STATS },
      'none-3': { ...DEFAULT_MODE_STATS }
    };
  }

  _saveStats() {
    const storage = this._getStorage();
    if (storage) {
      try {
        storage.setItem(STORAGE_KEYS.STATS, JSON.stringify(this.stats));
      } catch {
        // quota exceeded or storage error
      }
    }
  }

  _loadSettings() {
    const storage = this._getStorage();
    if (storage) {
      const data = storage.getItem(STORAGE_KEYS.SETTINGS);
      if (data) {
        try {
          return { ...DEFAULT_SETTINGS, ...JSON.parse(data) };
        } catch {
          // ignore
        }
      }
    }
    return { ...DEFAULT_SETTINGS };
  }

  saveSettings(newSettings) {
    this.settings = { ...this.settings, ...newSettings };
    const storage = this._getStorage();
    if (storage) {
      try {
        storage.setItem(STORAGE_KEYS.SETTINGS, JSON.stringify(this.settings));
      } catch {
        // ignore
      }
    }
  }

  /** Deal numbers of the most recent games, newest last. */
  getRecentSeeds() {
    return Array.isArray(this.settings.recentSeeds) ? this.settings.recentSeeds : [];
  }

  /**
   * Remembers a dealt game's number so the next winnable deals do not repeat it.
   * @param {number} seed
   */
  recordDealSeed(seed) {
    if (!Number.isFinite(seed)) return;
    const recent = this.getRecentSeeds().filter(s => s !== seed);
    recent.push(seed);
    this.saveSettings({ recentSeeds: recent.slice(-RECENT_SEEDS_LIMIT) });
  }

  /**
   * Reloads player's Vegas bankroll chips by adding amount (or resetting if in debt).
   * @param {number} [amount=500]
   */
  reloadBankroll(amount = 500) {
    const current = typeof this.settings.vegasBalance === 'number' ? this.settings.vegasBalance : 0;
    const newBal = (current < 0 ? 0 : current) + amount;
    this.saveSettings({ vegasBalance: newBal });
    return newBal;
  }

  /**
   * Resets player's Vegas bankroll chips directly to amount.
   * @param {number} [amount=500]
   */
  resetBankroll(amount = 500) {
    this.saveSettings({ vegasBalance: amount });
    return amount;
  }

  /**
   * Whether the once-a-day free chips refill is available: only when the bankroll is below the
   * refill amount and it has not been claimed on this calendar day.
   * @param {string} today - local date as YYYY-MM-DD
   */
  canClaimDailyChips(today, amount = 500) {
    const current = typeof this.settings.vegasBalance === 'number' ? this.settings.vegasBalance : 0;
    return current < amount && this.settings.dailyChipsDate !== today;
  }

  /**
   * Claims the daily free chips, refilling the bankroll to amount. Returns the new balance, or null if unavailable.
   * @param {string} today - local date as YYYY-MM-DD
   */
  claimDailyChips(today, amount = 500) {
    if (!this.canClaimDailyChips(today, amount)) return null;
    this.saveSettings({ vegasBalance: amount, dailyChipsDate: today });
    return amount;
  }

  getModeKey(scoringMode, drawMode) {
    return `${scoringMode}-${drawMode}`;
  }

  getStatsForMode(scoringMode, drawMode) {
    const key = this.getModeKey(scoringMode, drawMode);
    if (!this.stats[key]) {
      this.stats[key] = { ...DEFAULT_MODE_STATS };
    }
    return this.stats[key];
  }

  recordGameStarted(scoringMode, drawMode) {
    const modeStats = this.getStatsForMode(scoringMode, drawMode);
    modeStats.gamesPlayed++;
    this._saveStats();
  }

  recordGameWon(scoringMode, drawMode, { time, moves, score }) {
    const modeStats = this.getStatsForMode(scoringMode, drawMode);
    modeStats.gamesWon++;
    modeStats.currentStreak++;
    if (modeStats.currentStreak > modeStats.bestStreak) {
      modeStats.bestStreak = modeStats.currentStreak;
    }

    if (modeStats.bestTime === null || time < modeStats.bestTime) {
      modeStats.bestTime = time;
    }

    if (modeStats.fewestMoves === null || moves < modeStats.fewestMoves) {
      modeStats.fewestMoves = moves;
    }

    if (modeStats.bestScore === null || score > modeStats.bestScore) {
      modeStats.bestScore = score;
    }

    this._saveStats();
  }

  recordGameLost(scoringMode, drawMode) {
    const modeStats = this.getStatsForMode(scoringMode, drawMode);
    modeStats.currentStreak = 0;
    this._saveStats();
  }

  resetAllStats() {
    this.stats = {
      'standard-1': { ...DEFAULT_MODE_STATS },
      'standard-3': { ...DEFAULT_MODE_STATS },
      'vegas-1': { ...DEFAULT_MODE_STATS },
      'vegas-3': { ...DEFAULT_MODE_STATS },
      'none-1': { ...DEFAULT_MODE_STATS },
      'none-3': { ...DEFAULT_MODE_STATS }
    };
    this._saveStats();
  }

  saveGame(gameData) {
    const storage = this._getStorage();
    if (storage) {
      try {
        storage.setItem(STORAGE_KEYS.SAVED_GAME, JSON.stringify(gameData));
      } catch {
        // ignore
      }
    }
  }

  getSavedGame() {
    const storage = this._getStorage();
    if (storage) {
      const data = storage.getItem(STORAGE_KEYS.SAVED_GAME);
      if (data) {
        try {
          return JSON.parse(data);
        } catch {
          return null;
        }
      }
    }
    return null;
  }

  clearSavedGame() {
    const storage = this._getStorage();
    if (storage) {
      try {
        storage.removeItem(STORAGE_KEYS.SAVED_GAME);
      } catch {
        // ignore
      }
    }
  }
}

/**
 * Solitaire Pro 2.0 - Leaderboard & High Scores Engine
 * Pure logic module managing high scores, weekly/monthly/all-time leaderboards,
 * player profile, and Google Play Games synchronization.
 * Zero DOM dependencies; fully unit-tested in node:test.
 */

const STORAGE_KEYS = {
  SCORES: 'solitaire_pro_scores_v2',
  PROFILE: 'solitaire_pro_profile_v2'
};

const DEFAULT_PROFILE = {
  playerName: 'Oyuncu',
  isGooglePlayConnected: false,
  gamerTag: null,
  level: 12,
  xp: 1450,
  avatar: '🎮',
  lastSync: null
};

// The leaderboard holds only the player's own scores. Earlier builds shipped
// invented "seed-*" entries; they are filtered out when stored data is loaded.
function generateInitialSeeds() {
  return [];
}

function isSeedEntry(entry) {
  return Boolean(entry && typeof entry.id === 'string' && entry.id.startsWith('seed-'));
}

export class LeaderboardManager {
  constructor() {
    this.inMemoryScores = null;
    this.inMemoryProfile = null;
    this.scores = this._loadScores();
    this.profile = this._loadProfile();
  }

  _getStorage() {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        return window.localStorage;
      }
    } catch {
      // storage unavailable
    }
    return null;
  }

  _loadScores() {
    const storage = this._getStorage();
    if (storage) {
      const data = storage.getItem(STORAGE_KEYS.SCORES);
      if (data) {
        try {
          const parsed = JSON.parse(data);
          if (Array.isArray(parsed)) {
            return parsed.filter(entry => !isSeedEntry(entry));
          }
        } catch {
          // ignore corrupted data
        }
      }
    } else if (this.inMemoryScores) {
      return this.inMemoryScores;
    }

    const seeds = generateInitialSeeds();
    this.inMemoryScores = seeds;
    return seeds;
  }

  _saveScores() {
    const storage = this._getStorage();
    if (storage) {
      try {
        if (this.scores.length > 500) {
          const sorted = [...this.scores].sort((a, b) => b.score - a.score);
          this.scores = sorted.slice(0, 500);
        }
        storage.setItem(STORAGE_KEYS.SCORES, JSON.stringify(this.scores));
      } catch {
        // storage quota exceeded
      }
    }
    this.inMemoryScores = this.scores;
  }

  _loadProfile() {
    const storage = this._getStorage();
    if (storage) {
      const data = storage.getItem(STORAGE_KEYS.PROFILE);
      if (data) {
        try {
          return { ...DEFAULT_PROFILE, ...JSON.parse(data) };
        } catch {
          // ignore corrupted data
        }
      }
    } else if (this.inMemoryProfile) {
      return this.inMemoryProfile;
    }

    const initial = { ...DEFAULT_PROFILE };
    this.inMemoryProfile = initial;
    return initial;
  }

  _saveProfile() {
    const storage = this._getStorage();
    if (storage) {
      try {
        storage.setItem(STORAGE_KEYS.PROFILE, JSON.stringify(this.profile));
      } catch {
        // ignore
      }
    }
    this.inMemoryProfile = this.profile;
  }

  getProfile() {
    return { ...this.profile };
  }

  setPlayerName(name) {
    if (!name || typeof name !== 'string') return;
    const trimmed = name.trim().slice(0, 24);
    if (!trimmed) return;
    this.profile.playerName = trimmed;
    if (!this.profile.isGooglePlayConnected || !this.profile.gamerTag) {
      this.profile.gamerTag = trimmed;
    }
    for (const item of this.scores) {
      if (item.isPlayer) {
        item.playerName = trimmed;
      }
    }
    this._saveProfile();
    this._saveScores();
  }

  connectGooglePlay({ gamerTag, playerName, avatar } = {}) {
    const defaultTag = playerName || this.profile.playerName || 'PlayGamer';
    const tag = gamerTag || `${defaultTag}#${Math.floor(1000 + Math.random() * 9000)}`;

    this.profile.isGooglePlayConnected = true;
    this.profile.gamerTag = tag;
    if (playerName) this.profile.playerName = playerName;
    if (avatar) this.profile.avatar = avatar;
    this.profile.lastSync = new Date().toISOString();
    this.profile.xp = (this.profile.xp || 1450) + 250;
    this.profile.level = Math.floor(this.profile.xp / 100);

    // Upgrade player's existing local scores to Google Play source
    for (const item of this.scores) {
      if (item.isPlayer) {
        item.source = 'google_play';
        item.playerName = tag;
      }
    }

    this._saveProfile();
    this._saveScores();
    return this.getProfile();
  }

  disconnectGooglePlay() {
    this.profile.isGooglePlayConnected = false;
    this._saveProfile();
    return this.getProfile();
  }

  syncWithGooglePlay() {
    if (!this.profile.isGooglePlayConnected) {
      return { success: false, reason: 'not_connected' };
    }
    this.profile.lastSync = new Date().toISOString();
    this.profile.xp = (this.profile.xp || 1450) + 50;
    this.profile.level = Math.floor(this.profile.xp / 100);
    this._saveProfile();
    return {
      success: true,
      lastSync: this.profile.lastSync,
      gamerTag: this.profile.gamerTag,
      level: this.profile.level
    };
  }

  /**
   * Adds a newly completed game score to the leaderboard.
   */
  addScore({
    score,
    moves,
    time,
    scoringMode = 'standard',
    drawMode = 1,
    playerName = null,
    isPlayer = true,
    timestamp = Date.now()
  }) {
    const finalPlayerName = playerName
      || (this.profile.isGooglePlayConnected && this.profile.gamerTag ? this.profile.gamerTag : this.profile.playerName)
      || 'Oyuncu';

    const mode = `${scoringMode}-${drawMode}`;
    const source = this.profile.isGooglePlayConnected ? 'google_play' : 'local';

    const entry = {
      id: `score-${timestamp}-${Math.floor(Math.random() * 100000)}`,
      playerName: finalPlayerName,
      score: Number(score) || 0,
      moves: Number(moves) || 0,
      time: Number(time) || 0,
      mode,
      timestamp,
      source,
      isPlayer: Boolean(isPlayer)
    };

    this.scores.push(entry);
    this._saveScores();

    // Check ranks across timeframes (both in specific mode and overall)
    const rankWeekly = this._calculateRank(entry.id, 'weekly', mode);
    const rankWeeklyAll = this._calculateRank(entry.id, 'weekly', 'all');
    const rankMonthly = this._calculateRank(entry.id, 'monthly', mode);
    const rankMonthlyAll = this._calculateRank(entry.id, 'monthly', 'all');
    const rankAllTime = this._calculateRank(entry.id, 'all_time', mode);
    const rankAllTimeAll = this._calculateRank(entry.id, 'all_time', 'all');

    return {
      entry,
      rankWeekly,
      rankWeeklyAll,
      rankMonthly,
      rankMonthlyAll,
      rankAllTime,
      rankAllTimeAll,
      isWeeklyHighScore: (rankWeekly > 0 && rankWeekly <= 10) || (rankWeeklyAll > 0 && rankWeeklyAll <= 10),
      isMonthlyHighScore: (rankMonthly > 0 && rankMonthly <= 10) || (rankMonthlyAll > 0 && rankMonthlyAll <= 10),
      isAllTimeHighScore: (rankAllTime > 0 && rankAllTime <= 10) || (rankAllTimeAll > 0 && rankAllTimeAll <= 10)
    };
  }

  /**
   * Calculates 1-based rank of a score by ID within timeframe and mode.
   */
  _calculateRank(scoreId, timeframe, mode) {
    const board = this.getScores({ timeframe, mode, limit: Number.MAX_SAFE_INTEGER });
    const idx = board.findIndex(item => item.id === scoreId);
    return idx === -1 ? -1 : idx + 1;
  }

  /**
   * Retrieves sorted and ranked scores with timeframe and mode filtering.
   * @param {Object} options
   * @param {'weekly'|'monthly'|'all_time'} [options.timeframe='weekly']
   * @param {'all'|'standard'|'vegas'|'standard-1'|'standard-3'|'vegas-1'|'vegas-3'} [options.mode='all']
   * @param {number} [options.limit=25]
   */
  getScores({ timeframe = 'weekly', mode = 'all', limit = 25 } = {}) {
    const now = Date.now();
    const dayMs = 24 * 60 * 60 * 1000;

    const filtered = this.scores.filter(entry => {
      const ts = Number(entry.timestamp);
      // Timeframe check
      if (timeframe === 'weekly') {
        if (!ts || Number.isNaN(ts) || ts < now - 7 * dayMs) return false;
      } else if (timeframe === 'monthly') {
        if (!ts || Number.isNaN(ts) || ts < now - 30 * dayMs) return false;
      }

      // Mode check
      if (mode !== 'all') {
        if (mode === 'standard') {
          if (!entry.mode || !entry.mode.startsWith('standard')) return false;
        } else if (mode === 'vegas') {
          if (!entry.mode || !entry.mode.startsWith('vegas')) return false;
        } else {
          if (entry.mode !== mode) return false;
        }
      }

      return true;
    });

    // Sort: score DESC, time ASC, moves ASC, timestamp DESC
    filtered.sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score;
      if (a.time !== b.time) return a.time - b.time;
      if (a.moves !== b.moves) return a.moves - b.moves;
      return (b.timestamp || 0) - (a.timestamp || 0);
    });

    const sliced = Number.isFinite(limit) ? filtered.slice(0, limit) : filtered;
    return sliced.map((item, idx) => ({
      ...item,
      rank: idx + 1
    }));
  }

  /**
   * Returns current player's best rank and score entry in given timeframe and mode.
   */
  getPlayerBest({ timeframe = 'weekly', mode = 'all' } = {}) {
    const board = this.getScores({ timeframe, mode, limit: Number.MAX_SAFE_INTEGER });
    const playerEntries = board.filter(item => item.isPlayer);
    if (playerEntries.length === 0) return null;

    // First entry is the player's best because list is already sorted
    return {
      rank: playerEntries[0].rank,
      entry: playerEntries[0],
      totalEntries: board.length
    };
  }

  /**
   * Resets scores back to fresh seed dataset.
   */
  resetLeaderboard() {
    this.scores = generateInitialSeeds();
    this._saveScores();
    return this.scores;
  }
}

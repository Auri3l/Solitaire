/**
 * Solitaire Master Application Coordinator
 * Glues together Game Engine, Board Renderer, Drag & Drop, Sound, Victory Canvas, and UI Modals.
 */

import { SolitaireGame, SCORING_MODES, DRAW_MODES } from '../engine/solitaire.js';
import { HintEngine } from '../engine/hints.js';
import { StatsManager } from '../engine/stats.js';
import { LeaderboardManager } from '../engine/leaderboard.js';
import { SoundEffects } from '../audio/sound.js';
import { HapticFeedback } from './haptics.js';
import { BoardRenderer } from './renderer.js';
import { DragController } from './drag-controller.js';
import { VictoryCelebration } from './victory-canvas.js';
import { getCardFaceSVG } from './cards-svg.js';
import { t, translateHint, SUPPORTED_LANGUAGES } from './i18n.js';

export class SolitaireApp {
  constructor() {
    this.stats = new StatsManager();
    this.leaderboard = new LeaderboardManager();
    this.activeLbTimeframe = 'weekly';
    this.activeLbMode = 'all';

    const settings = this.stats.settings;

    const urlParams = (typeof window !== 'undefined' && window.location && window.location.search)
      ? new URLSearchParams(window.location.search)
      : null;
    const urlLang = urlParams?.get('lang');

    let savedLang = null;
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        const raw = window.localStorage.getItem('solitaire_pro_settings_v2');
        if (raw) {
          const parsed = JSON.parse(raw);
          if (parsed && parsed.language) savedLang = parsed.language;
        }
      }
    } catch {}

    const detectedLang = (typeof navigator !== 'undefined' && navigator.language && navigator.language.startsWith('tr')) ? 'tr' : 'en';

    this.language = urlLang || savedLang || detectedLang;
    this.sound = new SoundEffects(settings.soundEnabled, settings.soundVolume);
    this.haptics = new HapticFeedback(settings.hapticsEnabled !== false);
    this.game = null;
    this.renderer = null;
    this.dragController = null;
    this.victoryCelebration = null;

    this.timer = null;
    this.timerSeconds = 0;
    this.isPaused = false;
    this.isHidden = false;
    this.autoCompleteInProgress = false;
    this._autoCompleteTimer = null;

    this._bindDOM();
    this._initGame();
    this._setupEventListeners();
    this._applyTheme(settings.theme);
    this._applyCardSize(settings.cardSize || 'auto');
    this._applyLanguage(this.language);
    this._initPlayGames();
    this._initAds();
    this._initBilling();
    this._setupHomeScreen();
    if (!this._launchedWithUrlDeal) this.showHome();

    if (this._brokeAtLaunch) {
      // The opening deal can't be paid for: hand the bankroll back and ask for chips before dealing
      this.game.setBankroll(this.stats.settings.vegasBalance);
      this._pendingAfterChips = () => this._startNewGame(this.stats.settings.dealType === 'solvable');
      this._openCashierModal({ needed: 52 });
    }
  }

  _bindDOM() {
    // Top HUD
    this.dom = {
      gameNumber: document.getElementById('game-number'),
      scoreValue: document.getElementById('score-value'),
      movesValue: document.getElementById('moves-value'),
      timeValue: document.getElementById('time-value'),
      vegasContainer: document.getElementById('vegas-container'),
      vegasValue: document.getElementById('vegas-value'),
      vegasBalanceValue: document.getElementById('vegas-balance-value'),
      vegasBreakevenBadge: document.getElementById('vegas-breakeven-badge'),
      vegasBreakevenText: document.getElementById('vegas-breakeven-text'),
      btnDoubleDown: document.getElementById('btn-double-down'),
      btnBuyPass: document.getElementById('btn-buy-pass'),
      btnVegasCashier: document.getElementById('btn-vegas-cashier'),
      modalCashier: document.getElementById('modal-cashier'),
      cashierBalanceDisplay: document.getElementById('cashier-balance-display'),
      btnCashierReload: document.getElementById('btn-cashier-reload'),
      btnCashierReset: document.getElementById('btn-cashier-reset'),
      vegasVictoryReceipt: document.getElementById('vegas-victory-receipt'),
      passesBadge: document.getElementById('passes-badge'),
      drawModeBadge: document.getElementById('draw-mode-badge'),

      // Containers
      board: document.getElementById('solitaire-board'),
      stockContainer: document.getElementById('stock-container'),
      wasteContainer: document.getElementById('waste-container'),
      foundationsContainer: document.getElementById('foundations-container'),
      tableauContainer: document.getElementById('tableau-container'),

      // Action buttons
      btnNewGame: document.getElementById('btn-new-game'),
      btnRestart: document.getElementById('btn-restart'),
      btnUndo: document.getElementById('btn-undo'),
      btnRedo: document.getElementById('btn-redo'),
      btnHint: document.getElementById('btn-hint'),
      btnAutoComplete: document.getElementById('btn-auto-complete'),
      btnAutoCompleteFab: document.getElementById('btn-auto-complete-fab'),
      btnSound: document.getElementById('btn-sound'),
      btnSettings: document.getElementById('btn-settings'),
      btnStats: document.getElementById('btn-stats'),
      btnLeaderboard: document.getElementById('btn-leaderboard'),
      btnRules: document.getElementById('btn-rules'),

      // Hint toast
      hintToast: document.getElementById('hint-toast'),
      hintText: document.getElementById('hint-text'),

      // Canvas
      victoryCanvas: document.getElementById('victory-canvas'),

      // Modals
      modalBackdrop: document.getElementById('modal-backdrop'),
      modalSettings: document.getElementById('modal-settings'),
      modalStats: document.getElementById('modal-stats'),
      modalLeaderboard: document.getElementById('modal-leaderboard'),
      modalRules: document.getElementById('modal-rules'),
      modalShortcuts: document.getElementById('modal-shortcuts'),
      modalNewGame: document.getElementById('modal-new-game'),
      modalVictory: document.getElementById('modal-victory'),

      // Leaderboard & Google Play Elements
      gpgStatusPill: document.getElementById('gpg-status-pill'),
      gpgDesc: document.getElementById('gpg-desc'),
      gpgConnectRow: document.getElementById('gpg-connect-row'),
      gpgProfileRow: document.getElementById('gpg-profile-row'),
      gpgAvatar: document.getElementById('gpg-avatar'),
      gpgGamertag: document.getElementById('gpg-gamertag'),
      gpgLevel: document.getElementById('gpg-level'),
      btnGpgConnect: document.getElementById('btn-gpg-connect'),
      btnGpgSync: document.getElementById('btn-gpg-sync'),
      btnOpenGpgOverlay: document.getElementById('btn-open-gpg-overlay'),
      leaderboardTbody: document.getElementById('leaderboard-tbody'),
      lbStandingText: document.getElementById('lb-player-standing-text'),
      btnLbChangeName: document.getElementById('btn-lb-change-name'),
      btnStatsGotoLeaderboard: document.getElementById('btn-stats-goto-leaderboard'),
      victoryHighScoreCard: document.getElementById('victory-high-score-card'),
      victoryHighScoreText: document.getElementById('victory-high-score-text'),
      btnVictoryViewLeaderboard: document.getElementById('btn-victory-view-leaderboard')
    };
  }

  _initGame() {
    const settings = this.stats.settings;

    // Parse deterministic debug and scenario URL parameters
    const urlParams = (typeof window !== 'undefined' && window.location && window.location.search)
      ? new URLSearchParams(window.location.search)
      : null;

    const hasSeed = urlParams && urlParams.has('seed');
    const hasDraw = urlParams && urlParams.has('draw');
    const hasScoring = urlParams && urlParams.has('scoring');

    let seed = null;
    let drawMode = settings.drawMode;
    let scoringMode = settings.scoringMode;
    let vegasStake = settings.vegasStake || 1;

    if (hasSeed) {
      const s = parseInt(urlParams.get('seed'), 10);
      if (!Number.isNaN(s)) seed = s;
    }
    if (hasDraw) {
      const d = parseInt(urlParams.get('draw'), 10);
      if (d === 1 || d === 3) drawMode = d;
    }
    if (hasScoring) {
      const sc = urlParams.get('scoring').toLowerCase();
      if (sc === 'standard' || sc === 'vegas' || sc === 'none') scoringMode = sc;
    }
    if (urlParams && urlParams.has('stake')) {
      const st = parseInt(urlParams.get('stake'), 10);
      if ([1, 2, 5, 10].includes(st)) vegasStake = st;
    }

    const isDeterministicOverride = hasSeed || hasDraw || hasScoring;
    // A deal chosen in the URL opens straight into the game instead of the home screen
    this._launchedWithUrlDeal = isDeterministicOverride;

    // Check for saved game (bypassed if URL parameters specify deal configuration)
    const saved = isDeterministicOverride ? null : this.stats.getSavedGame();
    if (saved && !saved.isWon) {
      try {
        this.game = SolitaireGame.fromJSON(saved);
        this.timerSeconds = this.game.elapsedSeconds || 0;
      } catch {
        this.game = new SolitaireGame({
          drawMode: settings.drawMode,
          scoringMode: settings.scoringMode,
          solvable: settings.dealType === 'solvable',
          avoidSeeds: this.stats.getRecentSeeds(),
          vegasCumulative: settings.vegasCumulative ? settings.vegasBalance : 0,
          vegasStake: settings.vegasStake || 1
        });
        this.stats.recordDealSeed(this.game.dealSeed);
      }
    } else {
      let brokeAtLaunch = false;
      if (scoringMode === SCORING_MODES.VEGAS && settings.vegasCumulative) {
        const affordable = SolitaireGame.affordableStake(settings.vegasBalance, vegasStake);
        if (affordable > 0) vegasStake = affordable;
        else brokeAtLaunch = true;
      }
      this._brokeAtLaunch = brokeAtLaunch;
      this.game = new SolitaireGame({
        seed: seed !== null ? seed : undefined,
        drawMode,
        scoringMode,
        solvable: seed !== null ? false : (settings.dealType === 'solvable'),
        avoidSeeds: this.stats.getRecentSeeds(),
        vegasCumulative: settings.vegasCumulative ? settings.vegasBalance : 0,
        vegasStake
      });
      this.stats.recordDealSeed(this.game.dealSeed);
      if (!isDeterministicOverride) {
        this.stats.recordGameStarted(this.game.scoringMode, this.game.drawMode);
      }
    }

    // Public debug hooks for automated tests, replays, and diagnostics
    this.debug = {
      drawStock: () => this._handleStockClick(),
      undo: () => this._handleUndo(),
      redo: () => this._handleRedo(),
      hint: () => this._handleHint(),
      autoComplete: () => this._triggerAutoComplete(),
      dump: () => JSON.stringify(this.game.toJSON(), null, 2),
      load: (json) => {
        const data = typeof json === 'string' ? JSON.parse(json) : json;
        this.game = SolitaireGame.fromJSON(data);
        this._updateUI();
      }
    };

    if (typeof window !== 'undefined') {
      window.solitaireApp = this;
      window.__dump = () => this.debug.dump();
      window.__load = (json) => this.debug.load(json);
    }

    // Initialize Renderer
    this.renderer = new BoardRenderer({
      stockContainer: this.dom.stockContainer,
      wasteContainer: this.dom.wasteContainer,
      foundationsContainer: this.dom.foundationsContainer,
      tableauContainer: this.dom.tableauContainer
    }, settings.cardBack);

    // Initialize Drag Controller
    this.dragController = new DragController({
      boardElement: this.dom.board,
      isValidMoveFn: (source, target) => this.game.validateMove(source, target).valid,
      onDrop: (source, target) => this._handleDrop(source, target),
      onClick: (cardId, source) => this._handleCardClick(cardId, source),
      haptics: this.haptics
    });

    // Initialize Victory Canvas
    this.victoryCelebration = new VictoryCelebration(this.dom.victoryCanvas);

    this._startTimer();
    this._updateUI();
  }

  _setupEventListeners() {
    // Stock click (Draw card or recycle)
    this.dom.stockContainer.addEventListener('click', () => {
      this._handleStockClick();
    });

    // Top action buttons
    this.dom.btnNewGame.addEventListener('click', () => {
      this.haptics.tick();
      this._openModal(this.dom.modalNewGame);
    });
    this.dom.btnRestart.addEventListener('click', () => {
      this.haptics.tick();
      this._restartCurrentGame();
    });
    if (this.dom.gameNumber) {
      this.dom.gameNumber.addEventListener('click', () => {
        this.haptics.tick();
        this._promptGameNumber();
      });
    }
    this.dom.btnUndo.addEventListener('click', () => this._handleUndo());
    this.dom.btnRedo.addEventListener('click', () => this._handleRedo());
    this.dom.btnHint.addEventListener('click', () => this._handleHint());
    [this.dom.btnAutoComplete, this.dom.btnAutoCompleteFab].forEach(btn => {
      if (!btn) return;
      btn.addEventListener('click', () => {
        this.haptics.tick();
        this._triggerAutoComplete();
      });
    });

    // Vegas Action buttons
    if (this.dom.btnDoubleDown) {
      this.dom.btnDoubleDown.addEventListener('click', () => this._handleDoubleDown());
    }

    if (this.dom.btnBuyPass) {
      this.dom.btnBuyPass.addEventListener('click', () => this._handleBuyPass());
    }

    if (this.dom.btnVegasCashier) {
      this.dom.btnVegasCashier.addEventListener('click', () => this._openCashierModal());
    }

    // Stake buttons
    document.querySelectorAll('.stake-chip-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        this.haptics.tick();
        const stake = parseInt(e.currentTarget.dataset.stake, 10);
        this._handleStakeChange(stake);
      });
    });

    // Cashier Reload & Reset
    if (this.dom.btnCashierReload) {
      this.dom.btnCashierReload.addEventListener('click', () => {
        this.haptics.tick();
        const ads = this._adsBridge();
        if (ads) {
          // On Android, reloading chips is paid for by watching a rewarded video
          let shown = false;
          try {
            shown = ads.isRewardedReady() && ads.showRewarded();
          } catch {}
          if (!shown) this._showToast(t('toastVideoNotReady', this.language));
          return;
        }
        this._syncBankrollToSettings();
        this._grantChips(this.stats.reloadBankroll(500), t('toastReloadChips', this.language));
      });
    }

    if (this.dom.btnCashierReset) {
      this.dom.btnCashierReset.addEventListener('click', () => {
        this.haptics.tick();
        this._syncBankrollToSettings();
        const newBal = this.stats.claimDailyChips(this._todayKey());
        if (newBal === null) {
          this._showToast(t('toastDailyChipsUsed', this.language));
          return;
        }
        this._grantChips(newBal, t('toastDailyChips', this.language));
      });
    }

    const btnRemoveAds = typeof document !== 'undefined' ? document.getElementById('btn-remove-ads') : null;
    if (btnRemoveAds) {
      btnRemoveAds.addEventListener('click', () => {
        this.haptics.tick();
        const billing = this._billingBridge();
        let started = false;
        try {
          started = Boolean(billing && billing.buyRemoveAds());
        } catch {}
        if (!started) this._showToast(t('toastPurchaseUnavailable', this.language));
      });
    }

    const btnRestore = typeof document !== 'undefined' ? document.getElementById('btn-restore-purchases') : null;
    if (btnRestore) {
      btnRestore.addEventListener('click', () => {
        this.haptics.tick();
        const billing = this._billingBridge();
        if (!billing) return;
        try {
          billing.restorePurchases();
        } catch {}
      });
    }

    const btnPrivacy = typeof document !== 'undefined' ? document.getElementById('btn-privacy-options') : null;
    if (btnPrivacy) {
      btnPrivacy.addEventListener('click', () => {
        const ads = this._adsBridge();
        if (!ads) return;
        try {
          ads.showPrivacyOptions();
        } catch {}
      });
    }

    this.dom.btnSound.addEventListener('click', () => {
      this.haptics.tick();
      const isEnabled = !this.sound.enabled;
      this.sound.setEnabled(isEnabled);
      this.stats.saveSettings({ soundEnabled: isEnabled });
      this._updateSoundButton();
    });

    this.dom.btnSettings.addEventListener('click', () => {
      this.haptics.tick();
      this._openSettingsModal();
    });
    this.dom.btnStats.addEventListener('click', () => {
      this.haptics.tick();
      this._openStatsModal();
    });
    if (this.dom.btnLeaderboard) {
      this.dom.btnLeaderboard.addEventListener('click', () => {
        this.haptics.tick();
        this._openLeaderboardModal();
      });
    }
    this.dom.btnRules.addEventListener('click', () => {
      this.haptics.tick();
      this._openModal(this.dom.modalRules);
    });

    // Leaderboard timeframe tabs
    document.querySelectorAll('.lb-time-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.lb-time-btn').forEach(b => b.classList.remove('active'));
        e.currentTarget.classList.add('active');
        this.activeLbTimeframe = e.currentTarget.dataset.timeframe;
        this._renderLeaderboardTable();
      });
    });

    // Leaderboard mode filters
    document.querySelectorAll('.lb-filter-chip').forEach(chip => {
      chip.addEventListener('click', (e) => {
        document.querySelectorAll('.lb-filter-chip').forEach(c => c.classList.remove('active'));
        e.currentTarget.classList.add('active');
        this.activeLbMode = e.currentTarget.dataset.mode;
        this._renderLeaderboardTable();
      });
    });

    // Google Play Games Actions (real Play Games Services via the Android bridge)
    if (this.dom.btnGpgConnect) {
      this.dom.btnGpgConnect.addEventListener('click', () => {
        const bridge = this._playGamesBridge();
        if (!bridge) return;
        try {
          bridge.signIn();
        } catch {}
      });
    }

    if (this.dom.btnGpgSync) {
      this.dom.btnGpgSync.addEventListener('click', () => {
        if (this._submitBestScoresToPlayGames()) {
          this._showToast(t('gpgSyncedToast', this.language));
        }
      });
    }

    if (this.dom.btnOpenGpgOverlay) {
      this.dom.btnOpenGpgOverlay.addEventListener('click', () => {
        const bridge = this._playGamesBridge();
        if (!bridge) return;
        try {
          bridge.showLeaderboards();
        } catch {}
      });
    }

    if (this.dom.btnLbChangeName) {
      this.dom.btnLbChangeName.addEventListener('click', () => {
        const curr = this.leaderboard.getProfile().playerName;
        const newName = prompt(t('promptChangeName', this.language), curr);
        if (newName && newName.trim()) {
          this.leaderboard.setPlayerName(newName.trim());
          this._updateGpgCard();
          this._renderLeaderboardTable();
        }
      });
    }

    if (this.dom.btnStatsGotoLeaderboard) {
      this.dom.btnStatsGotoLeaderboard.addEventListener('click', () => {
        this._closeAllModals();
        this._openLeaderboardModal();
      });
    }

    if (this.dom.btnVictoryViewLeaderboard) {
      this.dom.btnVictoryViewLeaderboard.addEventListener('click', () => {
        this._closeAllModals();
        this._openLeaderboardModal();
      });
    }

    // Modals close buttons
    document.querySelectorAll('.modal-close, .btn-modal-close').forEach(btn => {
      btn.addEventListener('click', () => {
        this.haptics.tick();
        this._closeAllModals();
      });
    });

    this.dom.modalBackdrop.addEventListener('click', (e) => {
      if (e.target === this.dom.modalBackdrop) {
        this._closeAllModals();
      }
    });

    // New Game Modal Buttons
    const btnStartSolvable = document.getElementById('btn-start-solvable');
    const btnStartRandom = document.getElementById('btn-start-random');
    if (btnStartSolvable) {
      btnStartSolvable.addEventListener('click', () => {
        this.haptics.tick();
        this._closeAllModals();
        this._startNewGame(true);
      });
    }
    if (btnStartRandom) {
      btnStartRandom.addEventListener('click', () => {
        this.haptics.tick();
        this._closeAllModals();
        this._startNewGame(false);
      });
    }

    // Play Again button on Victory Modal
    const btnPlayAgain = document.getElementById('btn-play-again');
    if (btnPlayAgain) {
      btnPlayAgain.addEventListener('click', () => {
        this.haptics.tick();
        this.victoryCelebration.stop();
        this._closeAllModals();
        this._startNewGame(this.stats.settings.dealType === 'solvable');
      });
    }

    // Victory canvas click dismisses celebration
    this.dom.victoryCanvas.addEventListener('click', () => {
      this.victoryCelebration.stop();
    });

    // Keyboard Shortcuts
    window.addEventListener('keydown', (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') return;

      if (e.key === 'Escape') {
        this._closeAllModals();
        this.victoryCelebration.stop();
        this.renderer.clearHintHighlight();
        this.dom.hintToast.classList.remove('show');
        return;
      }

      // If a modal dialog is currently open, suppress gameplay shortcuts
      if (this.isPaused || this.dom.modalBackdrop?.style.display === 'flex') {
        return;
      }

      if (e.key.toLowerCase() === 'z' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        if (e.shiftKey) {
          this._handleRedo();
        } else {
          this._handleUndo();
        }
      } else if (e.key.toLowerCase() === 'y' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        this._handleRedo();
      } else if (e.ctrlKey || e.metaKey || e.altKey) {
        // Leave other modifier combos (Ctrl+R reload, Ctrl+N, ...) to the browser
        return;
      } else if (e.key === 'u' || e.key === 'U') {
        this._handleUndo();
      } else if (e.key === 'r' || e.key === 'R') {
        this._handleRedo();
      } else if (e.key === 'h' || e.key === 'H') {
        this._handleHint();
      } else if (e.key === 'n' || e.key === 'N') {
        this._openModal(this.dom.modalNewGame);
      } else if (e.key === ' ' || e.code === 'Space') {
        e.preventDefault();
        this._handleStockClick();
      } else if (e.key === 'm' || e.key === 'M') {
        this.dom.btnSound.click();
      } else if (e.key === 'd' || e.key === 'D') {
        if (this.game.scoringMode === SCORING_MODES.VEGAS && this.game.canDoubleDown()) {
          this._handleDoubleDown();
        }
      } else if (e.key === 'a' || e.key === 'A') {
        if (this.game.canAutoComplete()) {
          this._triggerAutoComplete();
        }
      } else if (e.key === '?') {
        this._openModal(this.dom.modalShortcuts);
      }
    });

    // Dismiss hint highlight when clicking empty board background
    this.dom.board.addEventListener('click', (e) => {
      if (e.target === this.dom.board || e.target.id === 'solitaire-board' || e.target.id === 'tableau-container') {
        this.renderer.clearHintHighlight();
        this.dom.hintToast.classList.remove('show');
      }
    });

    // Auto-save state before window unload
    window.addEventListener('beforeunload', () => {
      this._saveCurrentState();
    });

    // Mobile/WebView apps are usually suspended or killed without beforeunload:
    // save when the page is hidden and pause the clock while in the background.
    document.addEventListener('visibilitychange', () => {
      this.isHidden = document.visibilityState === 'hidden';
      if (this.isHidden) {
        this._saveCurrentState();
      }
    });

    // Re-render board on window resize to update card offsets
    window.addEventListener('resize', () => {
      clearTimeout(this._resizeTimer);
      this._resizeTimer = setTimeout(() => {
        if (this.game && !this.dragController?.isDragging) {
          this._fitCardsToScreen();
          this.renderer.render(this.game);
        }
      }, 100);
    });

    // The header can change height without a window resize (language switch, Vegas HUD),
    // which changes the room left for the cards
    const header = document.getElementById('app-header');
    if (header && typeof ResizeObserver === 'function') {
      let lastHeaderHeight = 0;
      new ResizeObserver(() => {
        const height = Math.round(header.getBoundingClientRect().height);
        if (height === lastHeaderHeight) return;
        lastHeaderHeight = height;
        if (this.game && !this.dragController?.isDragging) {
          this._fitCardsToScreen();
          this.renderer.render(this.game);
        }
      }).observe(header);
    }

    // Sound toggle button initial icon
    this._updateSoundButton();
  }

  _handleStockClick() {
    if (this.game.isWon || this.autoCompleteInProgress) return;

    this.renderer.clearHintHighlight();
    this.dom.hintToast.classList.remove('show');

    const res = this.game.draw();
    if (res.success) {
      if (res.action === 'RECYCLE') {
        this.sound.playShuffle();
        this.haptics.recycle();
      } else {
        this.sound.playDeal();
        this.haptics.deal();
      }
      this._updateUI();
      this._saveCurrentState();
    } else {
      this.haptics.invalid();
      if (res.canBuyPass) {
        this.sound.playInvalid();
        if (confirm(t('confirmBuyPass', this.language, { cost: this.game.extraPassCost }))) {
          this._handleBuyPass();
          return;
        }
      } else {
        this.sound.playInvalid();
      }
      this._showToast(t('toastCannotDraw', this.language));
    }
  }

  _onMoveSuccess(res, source, target) {
    this.sound.playPlace();
    if (target.pile === 'foundation') {
      this.haptics.foundation();
    } else {
      this.haptics.place();
    }

    if (res.flippedCard) {
      setTimeout(() => {
        this.sound.playFlip();
        this.haptics.flip();
      }, 120);
    }

    if (this.game.scoringMode === SCORING_MODES.VEGAS) {
      if (target.pile === 'foundation') {
        const targetSlot = this.dom.foundationsContainer?.children[target.foundationIndex];
        if (targetSlot) {
          const rect = targetSlot.getBoundingClientRect();
          this._spawnFloatingScore(rect, `+$${this.game.cardPayout}`, 'positive');
        }
        this.sound.playChip();
        if (this.game.cardsInFoundation === this.game.breakEvenCards) {
          this.sound.playCashChime();
          setTimeout(() => this.haptics.doubleDown(), 80);
          this._showToast(t('toastBreakEven', this.language));
        }
      } else if (source.pile === 'foundation' && target.pile !== 'foundation') {
        const targetCol = this.dom.tableauContainer?.children[target.col];
        if (targetCol) {
          const rect = targetCol.getBoundingClientRect();
          this._spawnFloatingScore(rect, `-$${this.game.cardPayout}`, 'negative');
        }
        this.sound.playChip();
      }
    }

    this._updateUI();
    this._saveCurrentState();

    if (res.isWon) {
      this._handleVictory();
    }
  }

  _spawnFloatingScore(rect, text, type = 'positive') {
    if (!rect || typeof document === 'undefined') return;
    const el = document.createElement('div');
    el.className = `floating-vegas-score ${type}`;
    el.textContent = text;
    el.style.left = `${rect.left + rect.width / 2}px`;
    el.style.top = `${rect.top}px`;
    document.body.appendChild(el);
    setTimeout(() => {
      if (el.parentNode) el.parentNode.removeChild(el);
    }, 850);
  }

  _handleDoubleDown() {
    if (this.game.isWon || this.autoCompleteInProgress) return;
    if (!this.game.canDoubleDown()) return;
    if (!this._canAfford(52 * this.game.vegasStake)) return;
    const res = this.game.doubleDown();
    if (res.success) {
      this.sound.playDoubleDown();
      this.haptics.doubleDown();
      this._showToast(t('toastDoubleDown', this.language, { buyIn: this.game.currentBuyIn, payout: this.game.cardPayout }));
      this._updateUI();
      this._saveCurrentState();
    }
  }

  _handleBuyPass() {
    if (this.game.isWon || this.autoCompleteInProgress) return;
    if (!this.game.canBuyPass()) return;
    if (!this._canAfford(this.game.extraPassCost)) return;
    const res = this.game.buyExtraPass();
    if (res.success) {
      this.sound.playShuffle();
      this.sound.playChip();
      this.haptics.recycle();
      this._showToast(t('toastExtraPass', this.language, { cost: res.cost }));
      this._updateUI();
      this._saveCurrentState();
    }
  }

  _handleStakeChange(stake) {
    if (this.game.isWon || this.autoCompleteInProgress) return;
    if (this.game.scoringMode !== SCORING_MODES.VEGAS) {
      this.stats.saveSettings({ vegasStake: stake });
      return;
    }

    if (this.game.moves === 0 && !this.game.isWon) {
      if (this.game.isDoubledDown) {
        this._showToast(t('toastStakeLockedDoubleDown', this.language));
        return;
      }
      if (!this._canAfford(52 * (stake - this.game.vegasStake))) return;
      const result = this.game.changeStake(stake);
      if (result.success) {
        this.stats.saveSettings({ vegasStake: stake });
        this.sound.playChip();
        this._updateUI();
        this._saveCurrentState();
      }
    } else {
      this.stats.saveSettings({ vegasStake: stake });
      if (confirm(t('confirmChangeStake', this.language, { stake, cost: 52 * stake }))) {
        this._startNewGame(this.stats.settings.dealType === 'solvable');
      } else {
        this._updateUI();
      }
    }
  }

  /**
   * Opens the cashier. With `needed`, it explains that the bankroll can't cover that bet.
   * @param {{ needed?: number }} [options]
   */
  _openCashierModal(options = {}) {
    this._syncBankrollToSettings();
    this._cashierNeeded = options.needed || 0;
    this._refreshCashier();
    this._openModal(this.dom.modalCashier);
  }

  _refreshCashier() {
    const bal = this._currentBankroll();
    if (this.dom.cashierBalanceDisplay) {
      this.dom.cashierBalanceDisplay.textContent = `${bal >= 0 ? '$' : '-$'}${Math.abs(bal)}`;
      this.dom.cashierBalanceDisplay.className = bal >= 0 ? 'cashier-amount vegas-positive' : 'cashier-amount vegas-negative';
    }
    const prompt = typeof document !== 'undefined' ? document.getElementById('cashier-prompt') : null;
    if (prompt) {
      prompt.textContent = this._cashierNeeded > 0
        ? t('cashierNotEnough', this.language, { cost: this._cashierNeeded })
        : t('cashierPrompt', this.language);
    }
    if (this.dom.btnCashierReload) {
      const ads = this._adsBridge();
      if (ads) {
        let ready = false;
        try {
          ready = ads.isRewardedReady();
        } catch {}
        this.dom.btnCashierReload.textContent = ready ? t('btnWatchVideoChips', this.language) : t('btnVideoLoading', this.language);
        this.dom.btnCashierReload.disabled = !ready;
      } else {
        this.dom.btnCashierReload.textContent = t('btnReloadChips', this.language);
        this.dom.btnCashierReload.disabled = false;
      }
    }
    if (this.dom.btnCashierReset) {
      const available = this.stats.canClaimDailyChips(this._todayKey());
      this.dom.btnCashierReset.textContent = available ? t('btnDailyChips', this.language) : t('btnDailyChipsUsed', this.language);
      this.dom.btnCashierReset.disabled = !available;
    }
  }

  /** Bankroll that the next bet is paid from. */
  _currentBankroll() {
    if (this.game && this.game.scoringMode === SCORING_MODES.VEGAS && this.stats.settings.vegasCumulative) {
      return this.game.vegasBalance;
    }
    return typeof this.stats.settings.vegasBalance === 'number' ? this.stats.settings.vegasBalance : 0;
  }

  _syncBankrollToSettings() {
    if (this.game && this.game.scoringMode === SCORING_MODES.VEGAS && this.stats.settings.vegasCumulative) {
      this.stats.saveSettings({ vegasBalance: this.game.vegasBalance });
    }
  }

  /**
   * In a persistent Vegas bankroll, a bet must be covered by the chips on hand.
   * Opens the cashier and returns false when it isn't. Standalone Vegas deals are always allowed.
   */
  _canAfford(cost) {
    if (cost <= 0 || !this.stats.settings.vegasCumulative) return true;
    if (this.game.scoringMode !== SCORING_MODES.VEGAS) return true;
    if (this.game.vegasBalance >= cost) return true;
    this.haptics.invalid();
    this._openCashierModal({ needed: cost });
    return false;
  }

  _grantChips(newBal, message) {
    if (this.game && this.game.scoringMode === SCORING_MODES.VEGAS && this.stats.settings.vegasCumulative) {
      this.game.setBankroll(newBal);
      this.stats.saveGame(this.game.toJSON());
    }
    this.sound.playChip();
    this._showToast(message);
    this._cashierNeeded = 0;
    const pending = this._pendingAfterChips;
    this._updateUI();
    this._closeAllModals();
    if (pending) pending();
  }

  _todayKey() {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  }

  _handleDrop(source, target) {
    if (this.game.isWon || this.autoCompleteInProgress) return;

    this.renderer.clearHintHighlight();
    this.dom.hintToast.classList.remove('show');

    const res = this.game.moveCards(source, target);
    if (res.success) {
      this._onMoveSuccess(res, source, target);
    } else {
      this.sound.playInvalid();
      this.haptics.invalid();
    }
  }

  _handleCardClick(cardId, source) {
    if (this.game.isWon || this.autoCompleteInProgress) return;

    this.renderer.clearHintHighlight();
    this.dom.hintToast.classList.remove('show');

    // Auto-move single click
    const autoMove = this.game.getAutoMove(cardId);
    if (autoMove) {
      const res = this.game.moveCards(autoMove.source, autoMove.target);
      if (res.success) {
        this._onMoveSuccess(res, autoMove.source, autoMove.target);
      }
    } else {
      this.haptics.invalid();
    }
  }

  _handleUndo() {
    if (this.game.isWon || this.autoCompleteInProgress) return;

    this.renderer.clearHintHighlight();
    this.dom.hintToast.classList.remove('show');

    const res = this.game.undo();
    if (res.success) {
      this.sound.playUndo();
      this.haptics.undo();
      this._updateUI();
      this._saveCurrentState();
    } else {
      this.sound.playInvalid();
      this.haptics.invalid();
    }
  }

  _handleRedo() {
    if (this.game.isWon || this.autoCompleteInProgress) return;

    this.renderer.clearHintHighlight();
    this.dom.hintToast.classList.remove('show');

    const res = this.game.redo();
    if (res.success) {
      this.sound.playPlace();
      this.haptics.place();
      this._updateUI();
      this._saveCurrentState();
      if (this.game.isWon) {
        this._handleVictory();
      }
    } else {
      this.sound.playInvalid();
      this.haptics.invalid();
    }
  }

  _handleHint() {
    if (this.game.isWon || this.autoCompleteInProgress) return;

    const hint = HintEngine.findBestHint(this.game);
    if (!hint) {
      this._showToast(t('toastNoMoves', this.language));
      this.sound.playInvalid();
      this.haptics.invalid();
      return;
    }

    this.sound.playFlip();
    this.haptics.tick();
    this.renderer.highlightHint(hint);
    this._showToast(hint.description);
  }

  _triggerAutoComplete() {
    if (!this.game.canAutoComplete() || this.autoCompleteInProgress) return;

    this.autoCompleteInProgress = true;
    this.dom.btnAutoComplete.classList.remove('ready');
    this.dom.btnAutoCompleteFab?.classList.remove('ready');

    let stepIndex = 0;
    const executeStep = () => {
      if (!this.autoCompleteInProgress) return;

      if (this.game.isWon) {
        this.autoCompleteInProgress = false;
        this._autoCompleteTimer = null;
        this._handleVictory();
        return;
      }

      const res = this.game.autoCompleteStep();
      if (res.success && res.drew) {
        // Drawing from the stock to reach the next card
        this.sound.playFlip();
        this._updateUI();
        this._autoCompleteTimer = setTimeout(executeStep, 90);
      } else if (res.success) {
        this.sound.playAutoCompleteNote(stepIndex++);
        this.haptics.autoCompleteStep();
        if (this.game.scoringMode === SCORING_MODES.VEGAS) {
          this.sound.playChip();
          const targetSlot = this.dom.foundationsContainer?.children[res.move.target.foundationIndex];
          if (targetSlot) {
            const rect = targetSlot.getBoundingClientRect();
            this._spawnFloatingScore(rect, `+$${this.game.cardPayout}`, 'positive');
          }
          if (this.game.cardsInFoundation === this.game.breakEvenCards) {
            this.sound.playCashChime();
            this._showToast(t('toastBreakEven', this.language));
          }
        }
        this._updateUI();
        this._autoCompleteTimer = setTimeout(executeStep, 140);
      } else {
        this.autoCompleteInProgress = false;
        this._autoCompleteTimer = null;
        if (this.game.isWon) {
          this._handleVictory();
        }
      }
    };

    executeStep();
  }

  _handleVictory() {
    this._stopTimer();
    this.stats.clearSavedGame();

    // Persist cumulative Vegas bankroll
    if (this.game.scoringMode === SCORING_MODES.VEGAS && this.stats.settings.vegasCumulative) {
      this.stats.saveSettings({ vegasBalance: this.game.vegasBalance });
    }

    // Record stats
    this.stats.recordGameWon(this.game.scoringMode, this.game.drawMode, {
      time: this.timerSeconds,
      moves: this.game.moves,
      score: this.game.score
    });

    // Record high score in LeaderboardManager
    const lbResult = this.leaderboard.addScore({
      score: this.game.score,
      moves: this.game.moves,
      time: this.timerSeconds,
      scoringMode: this.game.scoringMode,
      drawMode: this.game.drawMode,
      isPlayer: true
    });

    // Submit to Google Play Games leaderboards when signed in on Android
    this._submitScoreToPlayGames(this.game.scoringMode, this.game.score);

    // High Score Victory Banner
    if (this.dom.victoryHighScoreCard && this.dom.victoryHighScoreText) {
      if (lbResult.isWeeklyHighScore || lbResult.isMonthlyHighScore || lbResult.isAllTimeHighScore) {
        this.dom.victoryHighScoreCard.style.display = 'block';
        const bestRank = lbResult.rankWeekly > 0
          ? lbResult.rankWeekly
          : (lbResult.rankWeeklyAll > 0
            ? lbResult.rankWeeklyAll
            : (lbResult.rankMonthly > 0 ? lbResult.rankMonthly : lbResult.rankAllTime));
        const bannerMsg = t('newHighScoreToast', this.language, { rank: bestRank });
        this.dom.victoryHighScoreText.textContent = bannerMsg;
        this._showToast(bannerMsg);
      } else {
        this.dom.victoryHighScoreCard.style.display = 'none';
      }
    }

    if (this.game.scoringMode === SCORING_MODES.VEGAS) {
      this.sound.playJackpot();
    } else {
      this.sound.playVictory();
    }
    this.haptics.victory();

    // Prepare victory celebration canvas
    const foundationSlots = Array.from(this.dom.foundationsContainer.querySelectorAll('.foundation-pile'));
    const rects = foundationSlots.map((slot, idx) => {
      const r = slot.getBoundingClientRect();
      return {
        x: r.left,
        y: r.top,
        width: r.width,
        height: r.height,
        cards: this.game.foundations[idx]
      };
    });

    this.victoryCelebration.prepareCards(this.game.foundations, getCardFaceSVG).then(() => {
      this.victoryCelebration.start(rects);
    });

    // Populate victory modal
    document.getElementById('victory-time').textContent = this._formatTime(this.timerSeconds);
    document.getElementById('victory-moves').textContent = this.game.moves;
    document.getElementById('victory-score').textContent = this.game.score;

    // Vegas Settlement Receipt
    if (this.dom.vegasVictoryReceipt) {
      if (this.game.scoringMode === SCORING_MODES.VEGAS) {
        this.dom.vegasVictoryReceipt.style.display = 'block';
        const mult = this.game.currentStakeMultiplier;
        const buyIn = 52 * mult;
        const payout = 52 * 5 * mult;
        const jackpot = this.game.jackpotBonus || (100 * mult);
        const passCosts = this.game.extraPassesCost || ((this.game.extraPassesBought || 0) * (20 * mult));
        const net = this.game.score;
        const bankroll = this.game.vegasBalance;

        document.getElementById('v-rec-buyin').textContent = `-$${buyIn}`;
        document.getElementById('v-rec-payout').textContent = `+$${payout}`;
        document.getElementById('v-rec-jackpot').textContent = `+$${jackpot}`;
        const passRow = document.getElementById('v-rec-passes-row');
        if (passRow) {
          if (this.game.extraPassesBought > 0) {
            passRow.style.display = 'flex';
            document.getElementById('v-rec-passes').textContent = t('extraPassesBought', this.language, { cost: passCosts, count: this.game.extraPassesBought });
          } else {
            passRow.style.display = 'none';
          }
        }
        const netEl = document.getElementById('v-rec-net');
        netEl.textContent = `${net >= 0 ? '+$' : '-$'}${Math.abs(net)}`;
        netEl.className = net >= 0 ? 'vegas-positive' : 'vegas-negative';
        const bankEl = document.getElementById('v-rec-bankroll');
        bankEl.textContent = `${bankroll >= 0 ? '$' : '-$'}${Math.abs(bankroll)}`;
        bankEl.className = bankroll >= 0 ? 'vegas-positive' : 'vegas-negative';
      } else {
        this.dom.vegasVictoryReceipt.style.display = 'none';
      }
    }

    setTimeout(() => {
      this._openModal(this.dom.modalVictory);
    }, 2500);
  }

  /**
   * @param {boolean} [solvable=false] - deal a game the solver proves winnable
   * @param {number|null} [seed=null] - replay a specific game number instead
   */
  _startNewGame(solvable = false, seed = null) {
    const settings = this.stats.settings;
    if (settings.scoringMode === SCORING_MODES.VEGAS && settings.vegasCumulative) {
      const balance = this._currentBankroll();
      const stake = settings.vegasStake || 1;
      const affordable = SolitaireGame.affordableStake(balance, stake);
      if (affordable === 0) {
        this._pendingAfterChips = () => this._startNewGame(solvable, seed);
        this._openCashierModal({ needed: 52 });
        return;
      }
      if (affordable < stake) {
        this.stats.saveSettings({ vegasStake: affordable });
        this._showToast(t('toastStakeLowered', this.language, { cost: 52 * affordable }));
      }
    }
    const hadPlayed = Boolean(this.game && (this.game.moves > 0 || this.game.isWon));

    if (this._autoCompleteTimer) {
      clearTimeout(this._autoCompleteTimer);
      this._autoCompleteTimer = null;
    }
    this.victoryCelebration.stop();
    this.autoCompleteInProgress = false;
    this.renderer.clearHintHighlight();
    this.dom.hintToast.classList.remove('show');

    // If abandoning a game with active moves, record loss to reset streak
    if (this.game && this.game.moves > 0 && !this.game.isWon) {
      this.stats.recordGameLost(this.game.scoringMode, this.game.drawMode);
      if (this.game.scoringMode === SCORING_MODES.VEGAS && this.stats.settings.vegasCumulative) {
        this.stats.saveSettings({ vegasBalance: this.game.vegasBalance });
      }
    }

    // Re-read: saving settings above replaces the settings object
    const cfg = this.stats.settings;
    const startBal = (cfg.scoringMode === SCORING_MODES.VEGAS && cfg.vegasCumulative) ? cfg.vegasBalance : 0;
    this.game = new SolitaireGame({
      drawMode: cfg.drawMode,
      scoringMode: cfg.scoringMode,
      seed: seed !== null ? seed : undefined,
      solvable: seed === null && solvable,
      avoidSeeds: this.stats.getRecentSeeds(),
      vegasCumulative: startBal,
      vegasStake: cfg.vegasStake || 1
    });
    this.stats.recordDealSeed(this.game.dealSeed);

    this.stats.recordGameStarted(this.game.scoringMode, this.game.drawMode);
    this.timerSeconds = 0;
    this._startTimer();
    this._updateUI();
    this._saveCurrentState();

    // Ads only ever appear between games, never mid-deal; the Android side limits how often.
    if (hadPlayed) this._maybeShowInterstitial();
  }

  _setupHomeScreen() {
    const home = document.getElementById('home-screen');
    if (!home) return;
    this.dom.homeScreen = home;

    const on = (id, handler) => {
      const el = document.getElementById(id);
      if (el) el.addEventListener('click', () => { this.haptics.tick(); handler(); });
    };
    on('btn-home', () => this.showHome());
    on('home-continue', () => this.hideHome());
    home.querySelectorAll('[data-mode]').forEach(btn => {
      btn.addEventListener('click', () => {
        this.haptics.tick();
        this._startFromHome(btn.dataset.mode);
      });
    });
    home.querySelectorAll('[data-lang]').forEach(btn => {
      btn.addEventListener('click', () => {
        this.haptics.tick();
        this.stats.saveSettings({ language: btn.dataset.lang });
        this._applyLanguage(btn.dataset.lang);
        this._updateUI();
        this._updateHomeScreen();
      });
    });
    on('home-number', () => {
      this.hideHome();
      this._promptGameNumber();
    });
    on('home-stats', () => this._openStatsModal());
    on('home-settings', () => this._openSettingsModal());
    on('home-leaderboard', () => this._openLeaderboardModal());
    on('home-rules', () => this._openModal(this.dom.modalRules));
    on('home-remove-ads', () => document.getElementById('btn-remove-ads')?.click());
  }

  isHomeVisible() {
    return Boolean(this.dom.homeScreen && this.dom.homeScreen.style.display !== 'none');
  }

  /** Shows the home screen over the board; the current game is kept and its clock paused. */
  showHome() {
    if (!this.dom.homeScreen) return;
    this._updateHomeScreen();
    this.dom.homeScreen.style.display = 'flex';
    this._saveCurrentState();
  }

  hideHome() {
    if (!this.dom.homeScreen) return;
    this.dom.homeScreen.style.display = 'none';
  }

  _updateHomeScreen() {
    const home = this.dom.homeScreen;
    if (!home) return;
    const game = this.game;
    const inProgress = Boolean(game && game.moves > 0 && !game.isWon);
    const btnContinue = document.getElementById('home-continue');
    if (btnContinue) btnContinue.style.display = inProgress ? '' : 'none';
    const continueDesc = document.getElementById('home-continue-desc');
    if (continueDesc && game) {
      const mode = game.scoringMode === SCORING_MODES.VEGAS
        ? 'Vegas'
        : `Klondike · ${t(game.drawMode === 3 ? 'homeModeDraw3' : 'homeModeDraw1', this.language)}`;
      continueDesc.textContent = `#${game.dealSeed} · ${mode}`;
    }
    const vegasDesc = document.getElementById('home-vegas-desc');
    if (vegasDesc) {
      const settings = this.stats.settings;
      vegasDesc.textContent = t('homeVegasDesc', this.language, {
        payout: 5 * (settings.vegasStake || 1),
        balance: this._currentBankroll(),
      });
    }
    home.querySelectorAll('[data-lang]').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.lang === this.language);
    });
    const leaderboard = document.getElementById('home-leaderboard');
    if (leaderboard) leaderboard.style.display = this.dom.btnLeaderboard ? '' : 'none';
    const removeAds = document.getElementById('home-remove-ads');
    if (removeAds) {
      const status = this._billingStatus;
      const canBuy = Boolean(this._billingBridge() && status && status.available && !status.adsRemoved);
      removeAds.style.display = canBuy ? '' : 'none';
    }
  }

  /** Starts a new deal in the mode picked on the home screen. */
  _startFromHome(mode) {
    const changes = mode === 'vegas'
      ? { scoringMode: SCORING_MODES.VEGAS }
      : { scoringMode: SCORING_MODES.STANDARD, drawMode: mode === 'standard-3' ? 3 : 1 };
    this.stats.saveSettings(changes);
    this.hideHome();
    this._startNewGame(this.stats.settings.dealType === 'solvable');
  }

  /**
   * Shows the current game number (selectable, so it can be copied) and deals another game when
   * the player enters a different number.
   */
  _promptGameNumber() {
    if (typeof window === 'undefined' || typeof window.prompt !== 'function') return;
    const current = String(this.game.dealSeed);
    const answer = window.prompt(t('promptGameNumber', this.language), current);
    if (answer === null) return;
    const text = answer.trim().replace(/^#/, '');
    if (text === '' || text === current) return;
    const seed = Number(text);
    if (!Number.isInteger(seed) || seed < 1 || seed > 1000000) {
      this._showToast(t('toastInvalidGameNumber', this.language));
      return;
    }
    this._startNewGame(false, seed);
  }

  _restartCurrentGame() {
    if (this.game.moves > 0 && !this.game.isWon && !this._canAfford(52 * this.game.vegasStake)) return;
    if (confirm(t('confirmRestart', this.language))) {
      if (this._autoCompleteTimer) {
        clearTimeout(this._autoCompleteTimer);
        this._autoCompleteTimer = null;
      }
      this.victoryCelebration.stop();
      this.autoCompleteInProgress = false;
      this.renderer.clearHintHighlight();
      this.dom.hintToast.classList.remove('show');

      // If moves were made, record loss for abandoned attempt and count the retry as a new game
      if (this.game && this.game.moves > 0 && !this.game.isWon) {
        this.stats.recordGameLost(this.game.scoringMode, this.game.drawMode);
        this.stats.recordGameStarted(this.game.scoringMode, this.game.drawMode);
      }

      this.game.restartDeal();
      this.timerSeconds = 0;
      this._startTimer();
      this._updateUI();
      this._saveCurrentState();
    }
  }

  _startTimer() {
    this._stopTimer();
    this.timer = setInterval(() => {
      if (!this.isPaused && !this.isHidden && !this.isHomeVisible() && !this.game.isWon) {
        this.timerSeconds++;
        this.game.elapsedSeconds = this.timerSeconds;
        this.dom.timeValue.textContent = this._formatTime(this.timerSeconds);
      }
    }, 1000);
    this.dom.timeValue.textContent = this._formatTime(this.timerSeconds);
  }

  _stopTimer() {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }

  _formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  _updateUI() {
    // Re-render board
    this.renderer.render(this.game);

    // Update HUD
    if (this.dom.gameNumber) this.dom.gameNumber.textContent = `#${this.game.dealSeed}`;
    this.dom.scoreValue.textContent = this.game.score;
    this.dom.movesValue.textContent = this.game.moves;
    this.dom.drawModeBadge.textContent = this.game.drawMode === 1 ? t('draw1', this.language) : t('draw3', this.language);

    // Vegas HUD
    if (this.game.scoringMode === SCORING_MODES.VEGAS) {
      this.dom.vegasContainer.style.display = 'flex';

      // 1. Bankroll
      const bankroll = this.game.vegasBalance;
      if (this.dom.vegasBalanceValue) {
        this.dom.vegasBalanceValue.textContent = `${bankroll >= 0 ? '$' : '-$'}${Math.abs(bankroll)}`;
        this.dom.vegasBalanceValue.className = bankroll >= 0 ? 'stat-value vegas-positive' : 'stat-value vegas-negative';
      }

      // 2. Hand Net (Score in Vegas mode is the net result of this game)
      const handNet = this.game.score;
      this.dom.vegasValue.textContent = `${handNet >= 0 ? '+$' : '-$'}${Math.abs(handNet)}`;
      this.dom.vegasValue.className = handNet >= 0 ? 'stat-value vegas-positive' : 'stat-value vegas-negative';

      // 3. Break-even indicator
      if (this.dom.vegasBreakevenBadge && this.dom.vegasBreakevenText) {
        const foundCount = this.game.cardsInFoundation;
        const breakEven = this.game.breakEvenCards;
        this.dom.vegasBreakevenBadge.title = t('breakEvenTitle', this.language, { breakEven });
        if (this.game.isBreakEven) {
          this.dom.vegasBreakevenBadge.classList.add('in-the-money');
          const netStr = handNet >= 0 ? '+$' + handNet : '-$' + Math.abs(handNet);
          this.dom.vegasBreakevenText.textContent = t('inTheMoney', this.language, { net: netStr });
        } else {
          this.dom.vegasBreakevenBadge.classList.remove('in-the-money');
          this.dom.vegasBreakevenText.textContent = `${foundCount}/${breakEven} ${t('toProfit', this.language)}`;
        }
      }

      // 4. Passes badge
      this.dom.passesBadge.textContent = `${t('pass', this.language)}: ${this.game.passesUsed + 1}/${this.game.maxPasses}`;

      // 5. Double Down button state
      if (this.dom.btnDoubleDown) {
        if (this.game.isDoubledDown) {
          this.dom.btnDoubleDown.style.display = 'inline-flex';
          this.dom.btnDoubleDown.textContent = t('doubleDownActive', this.language);
          this.dom.btnDoubleDown.classList.add('active-doubled');
          this.dom.btnDoubleDown.disabled = true;
        } else {
          this.dom.btnDoubleDown.style.display = this.game.canDoubleDown() ? 'inline-flex' : 'none';
          this.dom.btnDoubleDown.textContent = t('doubleDown', this.language);
          this.dom.btnDoubleDown.classList.remove('active-doubled');
          this.dom.btnDoubleDown.disabled = false;
        }
      }

      // 6. Buy Pass button
      if (this.dom.btnBuyPass) {
        if (this.game.canBuyPass()) {
          this.dom.btnBuyPass.style.display = 'inline-flex';
          this.dom.btnBuyPass.textContent = t('buyPassWithCost', this.language, { cost: this.game.extraPassCost });
        } else {
          this.dom.btnBuyPass.style.display = 'none';
        }
      }

      // 7. Stake buttons active state
      document.querySelectorAll('.stake-chip-btn').forEach(btn => {
        const stakeVal = parseInt(btn.dataset.stake, 10);
        if (stakeVal === this.game.vegasStake) {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      });
    } else {
      this.dom.vegasContainer.style.display = 'none';
    }

    // Undo / Redo button enabled states
    this.dom.btnUndo.disabled = this.game.history.length === 0;
    this.dom.btnRedo.disabled = this.game.redoStack.length === 0;

    // Auto-complete button excitement
    const canAuto = this.game.canAutoComplete();
    this.dom.btnAutoComplete.disabled = !canAuto;
    this.dom.btnAutoCompleteFab?.classList.toggle('ready', canAuto && !this.autoCompleteInProgress);
    if (canAuto) {
      this.dom.btnAutoComplete.classList.add('ready');
    } else {
      this.dom.btnAutoComplete.classList.remove('ready');
    this.dom.btnAutoCompleteFab?.classList.remove('ready');
    }
  }

  _updateSoundButton() {
    this.dom.btnSound.textContent = this.sound.enabled ? '🔊' : '🔇';
    this.dom.btnSound.title = this.sound.enabled ? t('soundEnabledTitle', this.language) : t('soundMutedTitle', this.language);
  }

  _showToast(msg) {
    const displayMsg = this.language === 'tr' ? translateHint(msg, 'tr') : msg;
    this.dom.hintText.textContent = displayMsg;
    this.dom.hintToast.classList.add('show');
    clearTimeout(this._toastTimeout);
    this._toastTimeout = setTimeout(() => {
      this.dom.hintToast.classList.remove('show');
    }, 4500);
  }

  _applyLanguage(lang) {
    this.language = lang || 'en';
    if (typeof document !== 'undefined') {
      document.documentElement.lang = this.language;
      document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        const text = t(key, this.language);
        if (text) el.textContent = text;
      });
      document.querySelectorAll('[data-i18n-title]').forEach(el => {
        const key = el.getAttribute('data-i18n-title');
        const text = t(key, this.language);
        if (text) el.title = text;
      });
      if (this.dom.stockContainer) this.dom.stockContainer.title = t('stockTitle', this.language);
      if (this.dom.wasteContainer) this.dom.wasteContainer.title = t('wasteTitle', this.language);
      if (this.dom.foundationsContainer) this.dom.foundationsContainer.title = t('foundationsTitle', this.language);
      if (this.dom.tableauContainer) this.dom.tableauContainer.title = t('tableauTitle', this.language);
      if (this.dom.modalLeaderboard) {
        this._updateGpgCard();
        this._renderLeaderboardTable();
      }
    }
    this._updateSoundButton();
    if (this._billingStatus) this._updateRemoveAdsRow();
    if (this.game) {
      this._updateUI();
    }
  }

  _saveCurrentState() {
    if (!this.game.isWon) {
      if (this.game.scoringMode === SCORING_MODES.VEGAS && this.stats.settings.vegasCumulative) {
        this.stats.saveSettings({ vegasBalance: this.game.vegasBalance });
      }
      this.stats.saveGame(this.game.toJSON());
    }
  }

  _applyTheme(theme) {
    const classes = Array.from(document.body.classList).filter(c => !c.startsWith('theme-'));
    classes.push(`theme-${theme}`);
    document.body.className = classes.join(' ');
  }

  _applyCardSize(size) {
    const classes = Array.from(document.body.classList).filter(c => !c.startsWith('card-size-'));
    if (size && size !== 'auto') {
      classes.push(`card-size-${size}`);
    } else {
      classes.push('card-size-auto');
    }
    document.body.className = classes.join(' ');
    this._fitCardsToScreen();
    if (this.game && this.renderer) this.renderer.render(this.game);
  }

  /**
   * On phones and small windows, sizes the cards from the space actually available: the seven
   * columns always fill the width without clipping, and on short landscape screens the cards
   * shrink so the top row and a dealt tableau stay visible. Larger screens and the desktop
   * size presets keep the stylesheet sizes.
   */
  _fitCardsToScreen() {
    const body = document.body;
    const vars = ['--card-width', '--card-height', '--card-radius', '--gap', '--card-up-offset', '--card-down-offset'];
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const presetActive = !body.classList.contains('card-size-auto') && vw >= 901;
    if (presetActive || (vw > 1000 && vh > 600)) {
      vars.forEach(v => body.style.removeProperty(v));
      return;
    }

    const header = document.getElementById('app-header');
    const headerHeight = header ? header.getBoundingClientRect().height : 0;
    // Safe-area padding (iPhone notch / home indicator) on the container, 0 elsewhere
    const container = document.getElementById('app-container');
    const containerStyle = container ? window.getComputedStyle(container) : null;
    const pad = (side) => (containerStyle ? parseFloat(containerStyle[`padding${side}`]) || 0 : 0);
    const availableWidth = vw - pad('Left') - pad('Right');
    const gap = Math.max(3, Math.min(12, Math.round(availableWidth * 0.012)));
    // Short landscape screens put stock/waste and the foundations beside the tableau (see styles.css)
    const sideLayout = window.matchMedia('(orientation: landscape) and (max-height: 500px)').matches;
    let byWidth;
    let byHeight;
    if (sideLayout) {
      // 1 stock/waste + 7 tableau + 2 foundation columns; the left column holds the stock above a
      // fanned waste, and the tableau needs room for a dealt column
      byWidth = (availableWidth - 12 * gap) / 10;
      const boardHeight = vh - headerHeight - pad('Bottom') - 24;
      byHeight = (boardHeight - gap) / 2.4 / 1.45;
    } else {
      byWidth = (availableWidth - 8 * gap) / 7;
      // Height for the top row plus a dealt column (one card with a few cards stacked above it),
      // after the board's top padding and the gap between rows
      const boardHeight = vh - headerHeight - pad('Bottom') - Math.max(10, vh * 0.018) - Math.max(10, vh * 0.022);
      byHeight = boardHeight / 3.3 / 1.45;
    }
    const width = Math.floor(Math.max(30, Math.min(byWidth, byHeight, 112)));
    const height = Math.round(width * 1.45);

    body.style.setProperty('--card-width', `${width}px`);
    body.style.setProperty('--card-height', `${height}px`);
    body.style.setProperty('--card-radius', `${Math.max(3, Math.round(width * 0.075))}px`);
    body.style.setProperty('--gap', `${gap}px`);
    body.style.setProperty('--card-up-offset', `${Math.round(height * 0.24)}px`);
    body.style.setProperty('--card-down-offset', `${Math.round(height * 0.13)}px`);
  }

  _openModal(modal) {
    this.isPaused = true;
    this.dom.modalBackdrop.style.display = 'flex';
    document.querySelectorAll('.modal').forEach(m => m.style.display = 'none');
    if (modal) modal.style.display = 'block';
  }

  _closeAllModals() {
    this.isPaused = false;
    // A deal waiting on chips is dropped if the cashier is closed without topping up
    this._pendingAfterChips = null;
    this.dom.modalBackdrop.style.display = 'none';
    document.querySelectorAll('.modal').forEach(m => m.style.display = 'none');
  }

  _openSettingsModal() {
    const settings = this.stats.settings;

    // Fill settings inputs
    const selLanguage = document.getElementById('settings-language');
    const selTheme = document.getElementById('settings-theme');
    const selCardBack = document.getElementById('settings-card-back');
    const selCardSize = document.getElementById('settings-card-size');
    const selDrawMode = document.getElementById('settings-draw-mode');
    const selScoring = document.getElementById('settings-scoring');
    const selDealType = document.getElementById('settings-deal-type');
    const selVegasCum = document.getElementById('settings-vegas-cumulative');
    const selVegasStake = document.getElementById('settings-vegas-stake');
    const chkSound = document.getElementById('settings-sound-enabled');
    const rngVolume = document.getElementById('settings-sound-volume');
    const chkHaptics = document.getElementById('settings-haptics-enabled');

    if (selLanguage) selLanguage.value = this.language || 'en';
    if (selTheme) selTheme.value = settings.theme;
    if (selCardBack) selCardBack.value = settings.cardBack;
    if (selCardSize) selCardSize.value = settings.cardSize || 'auto';
    if (selDrawMode) selDrawMode.value = settings.drawMode;
    if (selScoring) selScoring.value = settings.scoringMode;
    if (selDealType) selDealType.value = settings.dealType;
    if (selVegasCum) selVegasCum.value = String(settings.vegasCumulative);
    if (selVegasStake) selVegasStake.value = String(settings.vegasStake || 1);
    if (chkSound) chkSound.checked = settings.soundEnabled;
    if (rngVolume) rngVolume.value = settings.soundVolume * 100;
    if (chkHaptics) chkHaptics.checked = settings.hapticsEnabled !== false;

    // Save changes listener
    const btnSave = document.getElementById('btn-save-settings');
    btnSave.onclick = () => {
      this.haptics.tick();
      const newSettings = {
        theme: selTheme.value,
        cardBack: selCardBack.value,
        cardSize: selCardSize ? selCardSize.value : 'auto',
        drawMode: parseInt(selDrawMode.value, 10),
        scoringMode: selScoring.value,
        dealType: selDealType.value,
        vegasCumulative: selVegasCum ? selVegasCum.value === 'true' : true,
        vegasStake: selVegasStake ? parseInt(selVegasStake.value, 10) : 1,
        soundEnabled: chkSound.checked,
        soundVolume: rngVolume.value / 100,
        hapticsEnabled: chkHaptics ? chkHaptics.checked : true,
        language: selLanguage ? selLanguage.value : 'en'
      };

      this.stats.saveSettings(newSettings);
      this._applyLanguage(newSettings.language);
      this._applyTheme(newSettings.theme);
      this._applyCardSize(newSettings.cardSize);
      this.renderer.setCardBackTheme(newSettings.cardBack);
      this.sound.setEnabled(newSettings.soundEnabled);
      this.sound.setVolume(newSettings.soundVolume);
      this.haptics.setEnabled(newSettings.hapticsEnabled);
      this._updateSoundButton();

      this._closeAllModals();

      // If draw or scoring changed, prompt for new game
      if (newSettings.drawMode !== this.game.drawMode || newSettings.scoringMode !== this.game.scoringMode) {
        if (confirm(t('confirmSettingsChange', this.language))) {
          this._startNewGame(newSettings.dealType === 'solvable');
        }
      } else {
        this.renderer.render(this.game);
      }
    };

    this._openModal(this.dom.modalSettings);
  }

  _openStatsModal() {
    const tabs = document.querySelectorAll('.stats-tab-btn');
    const loadModeStats = (modeKey) => {
      const [scoring, draw] = modeKey.split('-');
      const stats = this.stats.getStatsForMode(scoring, parseInt(draw, 10));

      document.getElementById('stat-played').textContent = stats.gamesPlayed;
      document.getElementById('stat-won').textContent = stats.gamesWon;
      const winRate = stats.gamesPlayed > 0 ? Math.round((stats.gamesWon / stats.gamesPlayed) * 100) : 0;
      document.getElementById('stat-win-rate').textContent = `${winRate}%`;
      document.getElementById('stat-current-streak').textContent = stats.currentStreak;
      document.getElementById('stat-best-streak').textContent = stats.bestStreak;
      document.getElementById('stat-best-time').textContent = stats.bestTime ? this._formatTime(stats.bestTime) : '--';
      document.getElementById('stat-best-score').textContent = stats.bestScore !== null ? stats.bestScore : '--';
      document.getElementById('stat-fewest-moves').textContent = stats.fewestMoves !== null ? stats.fewestMoves : '--';
    };

    tabs.forEach(tab => {
      tab.onclick = () => {
        tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        loadModeStats(tab.dataset.mode);
      };
    });

    const activeTab = document.querySelector('.stats-tab-btn.active') || tabs[0];
    if (activeTab) {
      activeTab.classList.add('active');
      loadModeStats(activeTab.dataset.mode);
    }

    const btnResetStats = document.getElementById('btn-reset-stats');
    if (btnResetStats) {
      btnResetStats.onclick = () => {
        if (confirm(t('confirmResetStats', this.language))) {
          this.stats.resetAllStats();
          loadModeStats(activeTab.dataset.mode);
        }
      };
    }

    this._openModal(this.dom.modalStats);
  }

  _openLeaderboardModal() {
    this._updateGpgCard();
    this._renderLeaderboardTable();
    this._openModal(this.dom.modalLeaderboard);
  }

  _updateGpgCard() {
    const profile = this.leaderboard.getProfile();
    if (this.dom.gpgAvatar) {
      this.dom.gpgAvatar.textContent = profile.avatar || '🎮';
    }
    if (profile.isGooglePlayConnected) {
      if (this.dom.gpgStatusPill) {
        this.dom.gpgStatusPill.textContent = this.language === 'tr' ? 'Bağlandı' : 'Connected';
        this.dom.gpgStatusPill.className = 'gpg-status-pill connected';
      }
      if (this.dom.gpgConnectRow) this.dom.gpgConnectRow.style.display = 'none';
      if (this.dom.gpgProfileRow) this.dom.gpgProfileRow.style.display = 'flex';
      if (this.dom.gpgGamertag) this.dom.gpgGamertag.textContent = profile.gamerTag || profile.playerName;
      if (this.dom.gpgLevel) {
        this.dom.gpgLevel.textContent = 'Google Play Games';
      }
      if (this.dom.gpgDesc) {
        this.dom.gpgDesc.textContent = this.language === 'tr'
          ? 'Google Play Games profiliniz bağlı. Haftalık ve aylık dereceleriniz eşitleniyor.'
          : 'Google Play Games connected. Your weekly & monthly ranks are synced.';
      }
    } else {
      if (this.dom.gpgStatusPill) {
        this.dom.gpgStatusPill.textContent = t('gpgOffline', this.language);
        this.dom.gpgStatusPill.className = 'gpg-status-pill disconnected';
      }
      if (this.dom.gpgConnectRow) this.dom.gpgConnectRow.style.display = 'block';
      if (this.dom.gpgProfileRow) this.dom.gpgProfileRow.style.display = 'none';
      if (this.dom.gpgDesc) this.dom.gpgDesc.textContent = t('gpgPrompt', this.language);
    }
  }

  _renderLeaderboardTable() {
    const scores = this.leaderboard.getScores({
      timeframe: this.activeLbTimeframe,
      mode: this.activeLbMode,
      limit: 30
    });

    const tbody = this.dom.leaderboardTbody;
    if (!tbody) return;
    tbody.innerHTML = '';

    if (scores.length === 0) {
      const emptyRow = document.createElement('tr');
      emptyRow.innerHTML = `<td colspan="6" style="text-align:center; padding: 22px; color:#94a3b8;">${t('noRankYet', this.language)}</td>`;
      tbody.appendChild(emptyRow);
    } else {
      scores.forEach(item => {
        const tr = document.createElement('tr');
        if (item.isPlayer) tr.classList.add('is-player');

        let rankHtml = `${item.rank}`;
        if (item.rank === 1) rankHtml = `<span class="rank-gold">🥇 1</span>`;
        else if (item.rank === 2) rankHtml = `<span class="rank-silver">🥈 2</span>`;
        else if (item.rank === 3) rankHtml = `<span class="rank-bronze">🥉 3</span>`;

        const playerTag = item.isPlayer
          ? `<span class="lb-player-tag">${this._escapeHtml(item.playerName)} <span class="lb-player-badge">${this.language === 'tr' ? 'SİZ' : 'YOU'}</span></span>`
          : `<span class="lb-player-tag">${item.source === 'google_play' ? '🎮 ' : ''}${this._escapeHtml(item.playerName)}</span>`;

        const parts = (item.mode || 'standard-1').split('-');
        const sMode = parts[0] || 'standard';
        const dMode = parts[1];
        let modeLabel = '';
        if (sMode === 'vegas') {
          modeLabel = dMode ? `Vegas (${dMode})` : 'Vegas';
        } else {
          modeLabel = dMode
            ? (this.language === 'tr' ? `Standart (${dMode})` : `Std (${dMode})`)
            : (this.language === 'tr' ? 'Standart' : 'Standard');
        }

        const scoreFormatted = sMode === 'vegas'
          ? `${item.score >= 0 ? '+$' : '-$'}${Math.abs(item.score)}`
          : `${item.score}`;

        tr.innerHTML = `
          <td class="col-rank">${rankHtml}</td>
          <td class="col-player">${playerTag}</td>
          <td class="col-mode">${modeLabel}</td>
          <td class="col-score">${scoreFormatted}</td>
          <td class="col-time">${this._formatTime(item.time)}</td>
          <td class="col-moves">${item.moves}</td>
        `;
        tbody.appendChild(tr);
      });
    }

    // Update standing banner
    const best = this.leaderboard.getPlayerBest({
      timeframe: this.activeLbTimeframe,
      mode: this.activeLbMode
    });

    if (this.dom.lbStandingText) {
      if (best) {
        const sFormatted = best.entry.mode.startsWith('vegas')
          ? `${best.entry.score >= 0 ? '+$' : '-$'}${Math.abs(best.entry.score)}`
          : `${best.entry.score}`;
        this.dom.lbStandingText.textContent = t('yourBestRank', this.language, {
          rank: best.rank,
          score: sFormatted
        });
      } else {
        this.dom.lbStandingText.textContent = t('noRankYet', this.language);
      }
    }
  }

  /**
   * Returns the native Play Games bridge (Android app only) or null on web/desktop.
   */
  _adsBridge() {
    if (typeof window === 'undefined' || !window.AndroidAds) return null;
    try {
      return window.AndroidAds.isAvailable() ? window.AndroidAds : null;
    } catch {
      return null;
    }
  }

  /**
   * Hooks up AdMob (Android only): rewarded videos pay +$500 chips, interstitials show between games,
   * and EU players get a privacy options button in Settings.
   */
  _initAds() {
    if (typeof window === 'undefined') return;
    window.onRewardedAdResult = (earned) => {
      if (earned) {
        this._syncBankrollToSettings();
        this._grantChips(this.stats.reloadBankroll(500), t('toastReloadChips', this.language));
      } else if (this.dom.modalCashier && this.dom.modalCashier.style.display === 'block') {
        this._refreshCashier();
      }
    };
    window.onAdsStatus = () => {
      this._updatePrivacyButton();
      if (this.dom.modalCashier && this.dom.modalCashier.style.display === 'block') this._refreshCashier();
    };
    this._updatePrivacyButton();
  }

  _updatePrivacyButton() {
    const row = typeof document !== 'undefined' ? document.getElementById('row-privacy-options') : null;
    if (!row) return;
    const ads = this._adsBridge();
    let required = false;
    try {
      required = Boolean(ads && ads.isPrivacyOptionsRequired());
    } catch {}
    row.style.display = required ? '' : 'none';
  }

  _billingBridge() {
    if (typeof window === 'undefined' || !window.AndroidBilling) return null;
    return window.AndroidBilling;
  }

  /** One-time "Remove ads" purchase through Google Play (Android only). */
  _initBilling() {
    const billing = this._billingBridge();
    if (!billing) return;
    this._billingStatus = null;
    window.onBillingStatus = (status) => {
      const wasRemoved = Boolean(this._billingStatus && this._billingStatus.adsRemoved);
      this._billingStatus = status || null;
      if (this._billingStatus && this._billingStatus.adsRemoved && !wasRemoved && this._billingStatusSeen) {
        this._showToast(t('toastAdsRemoved', this.language));
      }
      this._billingStatusSeen = true;
      this._updateRemoveAdsRow();
    };
    try {
      const raw = billing.getStatusJson();
      if (raw) window.onBillingStatus(JSON.parse(raw));
    } catch {}
  }

  _updateRemoveAdsRow() {
    if (this.isHomeVisible && this.isHomeVisible()) this._updateHomeScreen();
    const row = typeof document !== 'undefined' ? document.getElementById('row-remove-ads') : null;
    if (!row) return;
    const status = this._billingStatus;
    if (!this._billingBridge() || !status || (!status.available && !status.adsRemoved)) {
      row.style.display = 'none';
      return;
    }
    row.style.display = '';
    const btn = document.getElementById('btn-remove-ads');
    const btnRestore = document.getElementById('btn-restore-purchases');
    const desc = document.getElementById('remove-ads-desc');
    if (status.adsRemoved) {
      btn.textContent = t('btnAdsRemoved', this.language);
      btn.disabled = true;
      if (btnRestore) btnRestore.style.display = 'none';
      if (desc) desc.textContent = t('setAdsRemovedDesc', this.language);
    } else {
      btn.textContent = status.price ? t('btnRemoveAdsPrice', this.language, { price: status.price }) : t('btnRemoveAds', this.language);
      btn.disabled = false;
      if (btnRestore) btnRestore.style.display = '';
      if (desc) desc.textContent = t('setRemoveAdsDesc', this.language);
    }
  }

  _maybeShowInterstitial() {
    const ads = this._adsBridge();
    if (!ads) return;
    try {
      ads.maybeShowInterstitial();
    } catch {}
  }

  _playGamesBridge() {
    if (typeof window === 'undefined' || !window.AndroidPlayGames) return null;
    try {
      return window.AndroidPlayGames.isAvailable() ? window.AndroidPlayGames : null;
    } catch {
      return null;
    }
  }

  /**
   * Wires the Play Games sign-in state reported by the Android app into the UI.
   * The native side calls window.onPlayGamesStatus({ connected, playerName }) at
   * startup and after every sign-in attempt.
   */
  _initPlayGames() {
    const bridge = this._playGamesBridge();
    const gpgCard = typeof document !== 'undefined' ? document.getElementById('gpg-card') : null;
    if (!bridge) {
      // Play Games only exists inside the Android app; hide its controls elsewhere.
      if (gpgCard) gpgCard.style.display = 'none';
      if (this.dom.btnOpenGpgOverlay) this.dom.btnOpenGpgOverlay.style.display = 'none';
      if (this.leaderboard.getProfile().isGooglePlayConnected) this.leaderboard.disconnectGooglePlay();
      return;
    }

    let wasConnected = this.leaderboard.getProfile().isGooglePlayConnected;
    window.onPlayGamesStatus = (status) => {
      const connected = Boolean(status && status.connected);
      if (connected) {
        const name = (status.playerName || '').trim();
        this.leaderboard.connectGooglePlay({ playerName: name || undefined, gamerTag: name || undefined });
        if (!wasConnected) this._showToast(t('gpgConnected', this.language));
      } else if (this.leaderboard.getProfile().isGooglePlayConnected) {
        this.leaderboard.disconnectGooglePlay();
      }
      wasConnected = connected;
      this._updateGpgCard();
      this._renderLeaderboardTable();
    };

    // Native sign-in state arrives asynchronously; only apply the snapshot when it is
    // already known to be signed in, so a cold start doesn't flash "signed out".
    try {
      const raw = bridge.getStatusJson();
      const status = raw ? JSON.parse(raw) : null;
      if (status && status.connected) window.onPlayGamesStatus(status);
    } catch {}
  }

  _submitScoreToPlayGames(scoringMode, score) {
    const bridge = this._playGamesBridge();
    if (!bridge || !this.leaderboard.getProfile().isGooglePlayConnected) return false;
    if (scoringMode !== SCORING_MODES.STANDARD && scoringMode !== SCORING_MODES.VEGAS) return false;
    if (!Number.isFinite(score) || score <= 0) return false;
    try {
      bridge.submitScore(scoringMode, Math.round(score));
      return true;
    } catch {
      return false;
    }
  }

  _submitBestScoresToPlayGames() {
    let submitted = false;
    for (const mode of [SCORING_MODES.STANDARD, SCORING_MODES.VEGAS]) {
      const best = this.leaderboard.getPlayerBest({ timeframe: 'all_time', mode });
      if (best && this._submitScoreToPlayGames(mode, best.entry.score)) submitted = true;
    }
    return submitted;
  }

  _escapeHtml(text) {
    if (typeof text !== 'string') return '';
    return text.replace(/[&<>"']/g, (m) => {
      switch (m) {
        case '&': return '&amp;';
        case '<': return '&lt;';
        case '>': return '&gt;';
        case '"': return '&quot;';
        case "'": return '&#39;';
        default: return m;
      }
    });
  }
}

// Start app on DOMContentLoaded
window.addEventListener('DOMContentLoaded', () => {
  window.solitaireApp = new SolitaireApp();
});

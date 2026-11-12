/**
 * Solitaire (Klondike) Rules and Game Engine
 * Implements full game logic, state management, undo/redo, scoring, and auto-complete.
 */

import { Card } from './card.js';
import { dealGame } from './deck.js';
import { findWinnableSeed } from './solver.js';

export const SCORING_MODES = {
  STANDARD: 'standard',
  VEGAS: 'vegas',
  NONE: 'none'
};

export const DRAW_MODES = {
  DRAW_ONE: 1,
  DRAW_THREE: 3
};

/** Vegas stake multipliers offered in the UI ($52, $104, $260, $520 buy-ins). */
export const VEGAS_STAKES = [1, 2, 5, 10];

export class SolitaireGame {
  /**
   * @param {Object} options
   * @param {number} [options.drawMode=1] - 1 or 3
   * @param {string} [options.scoringMode='standard'] - 'standard' | 'vegas' | 'none'
   * @param {number|null} [options.seed=null]
   * @param {boolean} [options.solvable=false]
   * @param {number[]} [options.avoidSeeds] - recent deal seeds a winnable deal should not repeat
   * @param {number} [options.vegasCumulative=0] - starting balance for cumulative Vegas
   * @param {number} [options.vegasStake=1] - stake multiplier: 1 ($52), 2 ($104), 5 ($260), 10 ($520)
   * @param {boolean} [options.isDoubledDown=false] - whether double down is active
   * @param {number} [options.extraPassesBought=0] - additional passes purchased
   * @param {number} [options.jackpotBonus=0] - jackpot bonus awarded on win
   */
  constructor(options = {}) {
    this.drawMode = options.drawMode === 3 ? 3 : 1;
    this.scoringMode = options.scoringMode || SCORING_MODES.STANDARD;
    this.vegasBalance = options.vegasCumulative || 0;
    this.vegasStake = options.vegasStake || 1;
    this.initialOptions = { ...options };

    this.stock = [];
    this.waste = [];
    this.foundations = [[], [], [], []];
    this.tableau = [[], [], [], [], [], [], []];

    this.score = 0;
    this.moves = 0;
    this.passesUsed = 0;
    this.isWon = false;
    this.isDoubledDown = Boolean(options.isDoubledDown);
    this.extraPassesBought = options.extraPassesBought || 0;
    this.extraPassesCost = options.extraPassesCost || 0;
    this.jackpotBonus = options.jackpotBonus || 0;
    this.startTime = null;
    this.elapsedSeconds = 0;

    this.history = [];
    this.redoStack = [];

    if (!options._skipDeal) {
      this.startNewGame(options.seed, options.solvable, options.avoidSeeds);
    }
  }

  /**
   * Starts a brand new game.
   * @param {number|null} [seed=null]
   * @param {boolean} [solvable=false] - deal a fresh random game the solver proves winnable
   * @param {number[]} [avoidSeeds=[]] - recent seeds not to deal again (winnable deals only)
   */
  startNewGame(seed = null, solvable = false, avoidSeeds = []) {
    const useSolver = solvable && (seed === null || seed === undefined);
    const deal = useSolver
      ? dealGame(findWinnableSeed({ drawMode: this.drawMode, avoidSeeds }).seed)
      : dealGame(seed);
    this.dealSeed = deal.seed;

    this.stock = deal.stock;
    this.waste = [];
    this.foundations = [[], [], [], []];
    this.tableau = deal.tableau;

    this.moves = 0;
    this.passesUsed = 0;
    this.isWon = false;
    this.isDoubledDown = false;
    this.extraPassesBought = 0;
    this.extraPassesCost = 0;
    this.jackpotBonus = 0;
    this.history = [];
    this.redoStack = [];
    this.startTime = Date.now();
    this.elapsedSeconds = 0;

    if (this.scoringMode === SCORING_MODES.VEGAS) {
      const buyIn = 52 * this.vegasStake;
      this.score = -buyIn; // Cost to buy deck
      this.vegasBalance -= buyIn;
    } else {
      this.score = 0;
    }
  }

  /**
   * Highest Vegas stake (at most the requested one) whose $52 buy-in the bankroll covers; 0 if none.
   * @param {number} balance
   * @param {number} stake
   */
  static affordableStake(balance, stake) {
    const options = VEGAS_STAKES.filter(s => s <= stake).sort((a, b) => b - a);
    return options.find(s => 52 * s <= balance) || 0;
  }

  /**
   * Restarts the exact same deal from the beginning.
   */
  restartDeal() {
    if (this.scoringMode === SCORING_MODES.VEGAS && this.moves === 0) {
      // If no moves were made, refund the buy-in (including any Double Down) so restart doesn't double-charge
      this.vegasBalance += this.currentBuyIn;
    }
    this.startNewGame(this.dealSeed, false);
  }

  /**
   * Total number of cards currently stored across all 4 foundations.
   */
  get cardsInFoundation() {
    return this.foundations.reduce((sum, pile) => sum + pile.length, 0);
  }

  /**
   * Number of cards required in foundation to break even in Vegas mode (11 cards base, +4 per extra pass).
   * Cost: 52 base + 20 * extraPassesBought. Cards: Math.ceil(cost / 5).
   */
  get breakEvenCards() {
    return Math.ceil((52 + 20 * this.extraPassesBought) / 5);
  }

  /**
   * Whether the player has reached or passed the break-even threshold.
   */
  get isBreakEven() {
    return this.cardsInFoundation >= this.breakEvenCards;
  }

  /**
   * Effective multiplier combining base stake and Double Down.
   */
  get currentStakeMultiplier() {
    return this.vegasStake * (this.isDoubledDown ? 2 : 1);
  }

  /**
   * Foundation placement payout per card in Vegas rules ($5 * stake multiplier).
   */
  get cardPayout() {
    return 5 * this.currentStakeMultiplier;
  }

  /**
   * Current total buy-in cost for this deal ($52 * stake multiplier).
   */
  get currentBuyIn() {
    return 52 * this.currentStakeMultiplier;
  }

  /**
   * Cost to buy an extra deck pass ($20 * stake multiplier).
   */
  get extraPassCost() {
    return 20 * this.currentStakeMultiplier;
  }

  /**
   * Maximum deck passes allowed based on mode:
   * Standard: unlimited
   * Vegas Draw 1: 1 pass total (0 recycles) + extra passes bought
   * Vegas Draw 3: 3 passes total (2 recycles) + extra passes bought
   */
  get maxPasses() {
    if (this.scoringMode !== SCORING_MODES.VEGAS) return Infinity;
    return (this.drawMode === 1 ? 1 : 3) + this.extraPassesBought;
  }

  get passesRemaining() {
    if (this.scoringMode !== SCORING_MODES.VEGAS) return Infinity;
    return Math.max(0, this.maxPasses - (this.passesUsed + 1));
  }

  /**
   * Draws card(s) from Stock into Waste, or recycles Waste back to Stock.
   * @returns {{ success: boolean, action?: string, cardsDrawn?: number, scoreDelta?: number, reason?: string }}
   */
  draw() {
    if (this.isWon) return { success: false, reason: 'Game is already won' };

    if (this.stock.length > 0) {
      // Draw 1 or 3 cards
      const count = Math.min(this.drawMode, this.stock.length);
      const drawnCards = [];
      for (let i = 0; i < count; i++) {
        const card = this.stock.pop();
        card.faceUp = true;
        this.waste.push(card);
        drawnCards.push(card);
      }

      this.moves++;
      const action = {
        type: 'DRAW',
        cards: drawnCards.map(c => c.clone()),
        count,
        scoreDelta: 0
      };
      this.history.push(action);
      this.redoStack = [];

      return { success: true, action: 'DRAW', cardsDrawn: count, scoreDelta: 0 };
    } else if (this.waste.length > 0) {
      // Recycle Waste into Stock
      if (this.scoringMode === SCORING_MODES.VEGAS) {
        if (this.passesUsed + 1 >= this.maxPasses) {
          return { success: false, reason: 'No deck passes remaining in Vegas rules', canBuyPass: true };
        }
      }

      this.passesUsed++;
      let scoreDelta = 0;

      // Penalties for recycling stock in standard scoring:
      if (this.scoringMode === SCORING_MODES.STANDARD) {
        if (this.drawMode === 1 && this.passesUsed >= 2) {
          scoreDelta = -100;
        } else if (this.drawMode === 3 && this.passesUsed >= 4) {
          scoreDelta = -20;
        }
      }

      const previousScore = this.score;
      this.score = Math.max(0, this.score + scoreDelta);
      const actualScoreDelta = this.score - previousScore;

      const recycledCards = [];
      while (this.waste.length > 0) {
        const card = this.waste.pop();
        card.faceUp = false;
        this.stock.push(card);
        recycledCards.push(card);
      }

      this.moves++;
      const action = {
        type: 'RECYCLE',
        count: recycledCards.length,
        scoreDelta: actualScoreDelta,
        previousPasses: this.passesUsed - 1
      };
      this.history.push(action);
      this.redoStack = [];

      return { success: true, action: 'RECYCLE', scoreDelta: actualScoreDelta };
    }

    return { success: false, reason: 'No cards in stock or waste' };
  }

  /**
   * Adjusts the Vegas stake multiplier for an untouched deal (0 moves made).
   * Automatically updates game buy-in score and adjusts vegasBalance by the difference.
   * @param {number} stake - 1, 2, 5 or 10
   * @returns {{ success: boolean, reason?: string, oldStake?: number, newStake?: number, refundDelta?: number }}
   */
  changeStake(stake) {
    if (this.isWon) {
      return { success: false, reason: 'Game is already won' };
    }
    if (this.moves > 0) {
      return { success: false, reason: 'Stake can only be changed before any moves are made' };
    }
    if (this.isDoubledDown) {
      // The Double Down charge was taken at the old stake; changing stake now would mis-price the hand
      return { success: false, reason: 'Stake cannot be changed after Doubling Down' };
    }
    const oldStake = this.vegasStake;
    this.vegasStake = stake;

    if (this.scoringMode === SCORING_MODES.VEGAS) {
      const oldBuyIn = 52 * oldStake;
      const newBuyIn = 52 * stake;
      this.score = -newBuyIn;
      const refundDelta = oldBuyIn - newBuyIn;
      this.vegasBalance += refundDelta;
      return { success: true, oldStake, newStake: stake, refundDelta, newBuyIn };
    }

    return { success: true, oldStake, newStake: stake, refundDelta: 0 };
  }

  /**
   * Sets or synchronizes the player's Vegas bankroll balance.
   * @param {number} newBalance
   */
  setBankroll(newBalance) {
    this.vegasBalance = newBalance;
  }

  /**
   * Checks whether the current game is eligible for Doubling Down.
   * Allowed in Vegas mode during the opening phase (before any cards are sent to foundation).
   */
  canDoubleDown() {
    return (
      this.scoringMode === SCORING_MODES.VEGAS &&
      !this.isDoubledDown &&
      !this.isWon &&
      this.cardsInFoundation === 0 &&
      this.extraPassesBought === 0 &&
      !this.history.some(a => a.type === 'MOVE' && a.target?.pile === 'foundation')
    );
  }

  /**
   * Doubles the player's wager and all foundation payouts for this deal.
   * Deducts an additional buy-in (52 * vegasStake).
   */
  doubleDown() {
    if (!this.canDoubleDown()) {
      return { success: false, reason: 'Double Down is only available before scoring cards to foundation' };
    }

    const additionalCost = 52 * this.vegasStake;
    this.isDoubledDown = true;
    this.score -= additionalCost;
    this.vegasBalance -= additionalCost;

    const action = {
      type: 'DOUBLE_DOWN',
      cost: additionalCost
    };
    this.history.push(action);
    this.redoStack = [];

    return {
      success: true,
      cost: additionalCost,
      newMultiplier: this.currentStakeMultiplier,
      cardPayout: this.cardPayout
    };
  }

  /**
   * Checks whether the player can purchase an extra deck pass in Vegas mode.
   * Available when stock is empty, waste has cards, and pass limit is reached.
   */
  canBuyPass() {
    return (
      this.scoringMode === SCORING_MODES.VEGAS &&
      !this.isWon &&
      this.stock.length === 0 &&
      this.waste.length > 0 &&
      (this.passesUsed + 1) >= this.maxPasses
    );
  }

  /**
   * Purchases an extra deck pass for Vegas mode, reshuffling the waste back to stock.
   */
  buyExtraPass() {
    if (!this.canBuyPass()) {
      return { success: false, reason: 'Extra pass can only be purchased when passes are exhausted and waste has cards' };
    }

    const cost = this.extraPassCost;
    this.extraPassesBought++;
    this.extraPassesCost += cost;
    this.passesUsed++;
    this.score -= cost;
    this.vegasBalance -= cost;

    const recycledCards = [];
    while (this.waste.length > 0) {
      const card = this.waste.pop();
      card.faceUp = false;
      this.stock.push(card);
      recycledCards.push(card);
    }

    const action = {
      type: 'BUY_PASS',
      cost,
      cardsCount: recycledCards.length
    };
    this.history.push(action);
    this.redoStack = [];

    return {
      success: true,
      cost,
      cardsRecycled: recycledCards.length,
      extraPassesBought: this.extraPassesBought
    };
  }

  /**
   * Validates if a move is legal.
   * @param {Object} source - { pile: 'waste' | 'tableau' | 'foundation', col?: number, cardIndex?: number, foundationIndex?: number }
   * @param {Object} target - { pile: 'tableau' | 'foundation', col?: number, foundationIndex?: number }
   * @returns {{ valid: boolean, reason?: string, cards?: Card[] }}
   */
  validateMove(source, target) {
    if (!source || !target) return { valid: false, reason: 'Invalid parameters' };

    // Get cards to move from source
    let cardsToMove = [];

    if (source.pile === 'waste') {
      if (this.waste.length === 0) return { valid: false, reason: 'Waste is empty' };
      cardsToMove = [this.waste[this.waste.length - 1]];
    } else if (source.pile === 'tableau') {
      const col = this.tableau[source.col];
      if (!col || col.length === 0) return { valid: false, reason: 'Tableau column is empty' };
      const idx = source.cardIndex !== undefined ? source.cardIndex : col.length - 1;
      if (idx < 0 || idx >= col.length) return { valid: false, reason: 'Invalid card index' };

      const startCard = col[idx];
      if (!startCard.faceUp) return { valid: false, reason: 'Cannot move face-down card' };

      // Verify that all cards from idx to top form a valid descending alternating stack
      for (let i = idx; i < col.length - 1; i++) {
        if (!col[i + 1].canStackOnTableau(col[i])) {
          return { valid: false, reason: 'Stack is not in valid alternating sequence' };
        }
      }

      cardsToMove = col.slice(idx);
    } else if (source.pile === 'foundation') {
      const fPile = this.foundations[source.foundationIndex];
      if (!fPile || fPile.length === 0) return { valid: false, reason: 'Foundation is empty' };
      cardsToMove = [fPile[fPile.length - 1]];
    } else {
      return { valid: false, reason: `Unknown source pile: ${source.pile}` };
    }

    const leadCard = cardsToMove[0];

    // Validate placement onto target
    if (target.pile === 'foundation') {
      if (source.pile === 'foundation') {
        return { valid: false, reason: 'Cannot move cards between foundation piles' };
      }

      if (cardsToMove.length !== 1) {
        return { valid: false, reason: 'Only 1 card at a time can be moved to Foundation' };
      }

      const fPile = this.foundations[target.foundationIndex];
      if (!fPile) return { valid: false, reason: 'Invalid foundation index' };

      const topCard = fPile.length > 0 ? fPile[fPile.length - 1] : null;
      if (!leadCard.canStackOnFoundation(topCard)) {
        return { valid: false, reason: `Card ${leadCard.rankName}${leadCard.symbol} cannot be placed on foundation` };
      }

      return { valid: true, cards: cardsToMove };
    } else if (target.pile === 'tableau') {
      const col = this.tableau[target.col];
      if (!col) return { valid: false, reason: 'Invalid tableau column' };

      // Avoid moving card to the same column at the same position
      if (source.pile === 'tableau' && source.col === target.col) {
        return { valid: false, reason: 'Source and target are the same tableau column' };
      }

      if (col.length === 0) {
        // Empty column can only accept a King (rank 13)
        if (leadCard.rank !== 13) {
          return { valid: false, reason: 'Only a King can be placed on an empty column' };
        }
      } else {
        const topCard = col[col.length - 1];
        if (!topCard.faceUp) {
          return { valid: false, reason: 'Top card of destination column is not face up' };
        }
        if (!leadCard.canStackOnTableau(topCard)) {
          return { valid: false, reason: `Card ${leadCard.rankName}${leadCard.symbol} cannot be placed on ${topCard.rankName}${topCard.symbol}` };
        }
      }

      return { valid: true, cards: cardsToMove };
    }

    return { valid: false, reason: `Unknown target pile: ${target.pile}` };
  }

  /**
   * Executes a validated card move.
   * @param {Object} source
   * @param {Object} target
   * @returns {{ success: boolean, cardsMoved?: Card[], flippedCard?: Card|null, scoreDelta?: number, reason?: string }}
   */
  moveCards(source, target) {
    if (this.isWon) return { success: false, reason: 'Game is already won' };

    const validation = this.validateMove(source, target);
    if (!validation.valid) {
      return { success: false, reason: validation.reason };
    }

    const cardsCount = validation.cards.length;
    let scoreDelta = 0;
    let flippedCard = null;

    // 1. Remove cards from source
    let movedCards = [];
    if (source.pile === 'waste') {
      movedCards = [this.waste.pop()];
    } else if (source.pile === 'tableau') {
      const col = this.tableau[source.col];
      movedCards = col.splice(source.cardIndex !== undefined ? source.cardIndex : col.length - 1);

      // If source column now has cards and top card is face down, flip it!
      if (col.length > 0 && !col[col.length - 1].faceUp) {
        col[col.length - 1].faceUp = true;
        flippedCard = col[col.length - 1];
        if (this.scoringMode === SCORING_MODES.STANDARD) {
          scoreDelta += 5; // +5 points for turning over a card
        }
      }
    } else if (source.pile === 'foundation') {
      movedCards = [this.foundations[source.foundationIndex].pop()];
    }

    // 2. Add cards to target
    if (target.pile === 'foundation') {
      this.foundations[target.foundationIndex].push(...movedCards);
    } else if (target.pile === 'tableau') {
      this.tableau[target.col].push(...movedCards);
    }

    // 3. Compute score delta
    if (this.scoringMode === SCORING_MODES.STANDARD) {
      if (source.pile === 'waste' && target.pile === 'tableau') {
        scoreDelta += 5;
      } else if (source.pile === 'waste' && target.pile === 'foundation') {
        scoreDelta += 10;
      } else if (source.pile === 'tableau' && target.pile === 'foundation') {
        scoreDelta += 10;
      } else if (source.pile === 'foundation' && target.pile === 'tableau') {
        scoreDelta -= 15;
      }
      const prevScore = this.score;
      this.score = Math.max(0, this.score + scoreDelta);
      scoreDelta = this.score - prevScore;
    } else if (this.scoringMode === SCORING_MODES.VEGAS) {
      const payout = this.cardPayout;
      if (source.pile !== 'foundation' && target.pile === 'foundation') {
        scoreDelta += payout;
        this.vegasBalance += payout;
      } else if (source.pile === 'foundation' && target.pile !== 'foundation') {
        scoreDelta -= payout;
        this.vegasBalance -= payout;
      }
      this.score += scoreDelta;
    }

    this.moves++;

    // 4. Save to undo history
    const action = {
      type: 'MOVE',
      source: { ...source },
      target: { ...target },
      cardsCount,
      flippedCardId: flippedCard ? flippedCard.id : null,
      scoreDelta,
      timeBonus: 0,
      jackpotBonus: 0
    };

    // 5. Check victory
    const wasWon = this.isWon;
    const isNowWon = this.checkWinCondition();
    if (!wasWon && isNowWon) {
      if (this.scoringMode === SCORING_MODES.STANDARD && this.elapsedSeconds > 0) {
        const timeBonus = Math.max(0, Math.floor(700000 / this.elapsedSeconds));
        this.score += timeBonus;
        action.timeBonus = timeBonus;
      } else if (this.scoringMode === SCORING_MODES.VEGAS) {
        // Clearance Jackpot bonus for clearing all 52 cards to foundation!
        const jackpot = 100 * this.currentStakeMultiplier;
        this.score += jackpot;
        this.vegasBalance += jackpot;
        this.jackpotBonus = jackpot;
        action.jackpotBonus = jackpot;
      }
    }

    this.history.push(action);
    this.redoStack = [];

    return {
      success: true,
      cardsMoved: movedCards,
      flippedCard,
      scoreDelta,
      isWon: this.isWon
    };
  }

  /**
   * Checks if all cards are in the foundations.
   */
  checkWinCondition() {
    if (this.isWon) return true;

    let totalFoundationCards = 0;
    for (const fPile of this.foundations) {
      totalFoundationCards += fPile.length;
    }

    if (totalFoundationCards === 52) {
      this.isWon = true;
    }

    return this.isWon;
  }

  /**
   * Undoes the last move.
   * @returns {{ success: boolean, reason?: string, action?: Object }}
   */
  undo() {
    if (this.history.length === 0) {
      return { success: false, reason: 'Nothing to undo' };
    }

    const action = this.history.pop();
    this.redoStack.push(action);

    if (action.type === 'DOUBLE_DOWN') {
      this.isDoubledDown = false;
      this.score += action.cost;
      this.vegasBalance += action.cost;
      return { success: true, action };
    } else if (action.type === 'BUY_PASS') {
      while (this.stock.length > 0) {
        const card = this.stock.pop();
        card.faceUp = true;
        this.waste.push(card);
      }
      this.extraPassesBought--;
      this.extraPassesCost -= action.cost;
      this.passesUsed--;
      this.score += action.cost;
      this.vegasBalance += action.cost;
      return { success: true, action };
    } else if (action.type === 'DRAW') {
      // Revert draw: move cards from waste back to stock
      for (let i = 0; i < action.count; i++) {
        const card = this.waste.pop();
        card.faceUp = false;
        this.stock.push(card);
      }
      this.moves--;
      return { success: true, action };
    } else if (action.type === 'RECYCLE') {
      // Revert recycle: move cards from stock back to waste
      while (this.stock.length > 0) {
        const card = this.stock.pop();
        card.faceUp = true;
        this.waste.push(card);
      }
      this.passesUsed = action.previousPasses || 0;
      this.score -= action.scoreDelta;
      this.moves--;
      return { success: true, action };
    } else if (action.type === 'MOVE') {
      // 1. Move cards back from target to source
      let cards = [];
      if (action.target.pile === 'foundation') {
        cards = this.foundations[action.target.foundationIndex].splice(-action.cardsCount);
      } else if (action.target.pile === 'tableau') {
        cards = this.tableau[action.target.col].splice(-action.cardsCount);
      }

      if (action.source.pile === 'waste') {
        this.waste.push(...cards);
      } else if (action.source.pile === 'tableau') {
        // If a card was flipped in source tableau, flip it back down!
        if (action.flippedCardId) {
          const col = this.tableau[action.source.col];
          if (col.length > 0 && col[col.length - 1].id === action.flippedCardId) {
            col[col.length - 1].faceUp = false;
          }
        }
        this.tableau[action.source.col].push(...cards);
      } else if (action.source.pile === 'foundation') {
        this.foundations[action.source.foundationIndex].push(...cards);
      }

      // Revert score
      this.score -= action.scoreDelta;
      if (action.timeBonus) {
        this.score -= action.timeBonus;
      }
      if (action.jackpotBonus) {
        this.score -= action.jackpotBonus;
        this.jackpotBonus = 0;
      }
      if (this.scoringMode === SCORING_MODES.VEGAS) {
        this.vegasBalance -= action.scoreDelta;
        if (action.jackpotBonus) {
          this.vegasBalance -= action.jackpotBonus;
        }
      }
      this.moves--;
      this.isWon = false;

      return { success: true, action };
    }

    return { success: false, reason: 'Unknown action type' };
  }

  /**
   * Redoes the last undone move.
   * @returns {{ success: boolean, reason?: string, action?: Object }}
   */
  redo() {
    if (this.redoStack.length === 0) {
      return { success: false, reason: 'Nothing to redo' };
    }

    const action = this.redoStack.pop();

    if (action.type === 'DOUBLE_DOWN') {
      this.isDoubledDown = true;
      this.score -= action.cost;
      this.vegasBalance -= action.cost;
      this.history.push(action);
      return { success: true, action };
    } else if (action.type === 'BUY_PASS') {
      this.extraPassesBought++;
      this.extraPassesCost += action.cost;
      this.passesUsed++;
      this.score -= action.cost;
      this.vegasBalance -= action.cost;
      while (this.waste.length > 0) {
        const card = this.waste.pop();
        card.faceUp = false;
        this.stock.push(card);
      }
      this.history.push(action);
      return { success: true, action };
    } else if (action.type === 'DRAW') {
      for (let i = 0; i < action.count; i++) {
        const card = this.stock.pop();
        card.faceUp = true;
        this.waste.push(card);
      }
      this.moves++;
      this.history.push(action);
      return { success: true, action };
    } else if (action.type === 'RECYCLE') {
      this.passesUsed++;
      while (this.waste.length > 0) {
        const card = this.waste.pop();
        card.faceUp = false;
        this.stock.push(card);
      }
      this.score += action.scoreDelta;
      this.moves++;
      this.history.push(action);
      return { success: true, action };
    } else if (action.type === 'MOVE') {
      // Re-execute move
      let cards = [];
      if (action.source.pile === 'waste') {
        cards = this.waste.splice(-action.cardsCount);
      } else if (action.source.pile === 'tableau') {
        const col = this.tableau[action.source.col];
        cards = col.splice(-action.cardsCount);
        if (action.flippedCardId && col.length > 0) {
          col[col.length - 1].faceUp = true;
        }
      } else if (action.source.pile === 'foundation') {
        cards = this.foundations[action.source.foundationIndex].splice(-action.cardsCount);
      }

      if (action.target.pile === 'foundation') {
        this.foundations[action.target.foundationIndex].push(...cards);
      } else if (action.target.pile === 'tableau') {
        this.tableau[action.target.col].push(...cards);
      }

      this.score += action.scoreDelta;
      if (action.timeBonus) {
        this.score += action.timeBonus;
      }
      if (action.jackpotBonus) {
        this.score += action.jackpotBonus;
        this.jackpotBonus = action.jackpotBonus;
      }
      if (this.scoringMode === SCORING_MODES.VEGAS) {
        this.vegasBalance += action.scoreDelta;
        if (action.jackpotBonus) {
          this.vegasBalance += action.jackpotBonus;
        }
      }
      this.moves++;
      this.history.push(action);
      this.checkWinCondition();

      return { success: true, action };
    }

    return { success: false, reason: 'Unknown action' };
  }

  /**
   * Finds the best auto-move destination for a clicked card.
   * Priority:
   * 1. Foundation
   * 2. Tableau
   * @param {string} cardId
   * @returns {{ source: Object, target: Object }|null}
   */
  getAutoMove(cardId) {
    // 1. Locate the card
    let source = null;
    let card = null;

    if (this.waste.length > 0 && this.waste[this.waste.length - 1].id === cardId) {
      source = { pile: 'waste' };
      card = this.waste[this.waste.length - 1];
    } else {
      // Search tableau
      for (let c = 0; c < 7; c++) {
        const col = this.tableau[c];
        for (let i = 0; i < col.length; i++) {
          if (col[i].id === cardId) {
            if (!col[i].faceUp) return null; // Cannot move face down card
            source = { pile: 'tableau', col: c, cardIndex: i };
            card = col[i];
            break;
          }
        }
        if (source) break;
      }

      // Search foundation (allow moving card down to tableau)
      if (!source) {
        for (let f = 0; f < 4; f++) {
          const fPile = this.foundations[f];
          if (fPile.length > 0 && fPile[fPile.length - 1].id === cardId) {
            source = { pile: 'foundation', foundationIndex: f };
            card = fPile[fPile.length - 1];
            break;
          }
        }
      }
    }

    if (!source || !card) return null;

    // Check if single card can go to any foundation
    const isSingleCard = source.pile === 'waste' ||
      (source.pile === 'tableau' && source.cardIndex === this.tableau[source.col].length - 1);

    if (isSingleCard) {
      for (let f = 0; f < 4; f++) {
        const target = { pile: 'foundation', foundationIndex: f };
        if (this.validateMove(source, target).valid) {
          return { source, target };
        }
      }
    }

    // Check if card or stack can go to any tableau column
    for (let c = 0; c < 7; c++) {
      if (source.pile === 'tableau' && source.col === c) continue;

      const target = { pile: 'tableau', col: c };
      if (this.validateMove(source, target).valid) {
        // If moving a King from base of one column to an empty column, ignore as redundant
        if (card.rank === 13 && source.pile === 'tableau' && source.cardIndex === 0 && this.tableau[c].length === 0) {
          continue;
        }
        return { source, target };
      }
    }

    return null;
  }

  /**
   * Determines if the current game is eligible for Auto-Complete.
   * True when every Tableau card is face up. Cards left in the Stock/Waste are then played out by
   * drawing, except in Vegas, where deck passes are limited, so the Stock and Waste must be empty.
   * @returns {boolean}
   */
  canAutoComplete() {
    if (this.isWon) return false;
    if ((this.stock.length > 0 || this.waste.length > 0) && this.scoringMode === SCORING_MODES.VEGAS) return false;

    for (const col of this.tableau) {
      for (const card of col) {
        if (!card.faceUp) return false;
      }
    }

    return true;
  }

  /**
   * Executes a single step of the auto-complete sequence.
   * Moves the lowest rank available card to its corresponding foundation.
   * @returns {{ success: boolean, move?: Object }}
   */
  autoCompleteStep() {
    if (this.isWon) return { success: false, reason: 'Game won' };

    // Find any tableau top card or waste card that can go to foundation
    let bestMove = null;
    let minRank = 999;

    for (let c = 0; c < 7; c++) {
      const col = this.tableau[c];
      if (col.length === 0) continue;
      const topCard = col[col.length - 1];

      for (let f = 0; f < 4; f++) {
        const source = { pile: 'tableau', col: c, cardIndex: col.length - 1 };
        const target = { pile: 'foundation', foundationIndex: f };
        if (this.validateMove(source, target).valid) {
          if (topCard.rank < minRank) {
            minRank = topCard.rank;
            bestMove = { source, target };
          }
        }
      }
    }

    // Also check waste pile if any cards remain
    if (this.waste.length > 0) {
      const wasteCard = this.waste[this.waste.length - 1];
      for (let f = 0; f < 4; f++) {
        const source = { pile: 'waste' };
        const target = { pile: 'foundation', foundationIndex: f };
        if (this.validateMove(source, target).valid) {
          if (wasteCard.rank < minRank) {
            minRank = wasteCard.rank;
            bestMove = { source, target };
          }
        }
      }
    }

    if (bestMove) {
      const res = this.moveCards(bestMove.source, bestMove.target);
      this._autoDrawsWithoutProgress = 0;
      return { success: true, move: bestMove, result: res };
    }

    // Nothing playable on top: draw to dig out the next card, giving up after two full trips
    // through the Stock without a single card reaching the Foundations
    const talonSize = this.stock.length + this.waste.length;
    if (talonSize > 0) {
      const drawsPerPass = Math.ceil(talonSize / this.drawMode) + 1;
      this._autoDrawsWithoutProgress = (this._autoDrawsWithoutProgress || 0) + 1;
      if (this._autoDrawsWithoutProgress <= 2 * drawsPerPass) {
        const res = this.draw();
        if (res.success) return { success: true, drew: true, result: res };
      }
      this._autoDrawsWithoutProgress = 0;
    }

    return { success: false, reason: 'No move found' };
  }

  /**
   * Exports game state to plain JSON for persistence.
   */
  toJSON() {
    return {
      drawMode: this.drawMode,
      scoringMode: this.scoringMode,
      vegasBalance: this.vegasBalance,
      vegasStake: this.vegasStake,
      isDoubledDown: this.isDoubledDown,
      extraPassesBought: this.extraPassesBought,
      extraPassesCost: this.extraPassesCost,
      jackpotBonus: this.jackpotBonus,
      score: this.score,
      moves: this.moves,
      passesUsed: this.passesUsed,
      isWon: this.isWon,
      dealSeed: this.dealSeed,
      elapsedSeconds: this.elapsedSeconds,
      stock: this.stock.map(c => c.toJSON()),
      waste: this.waste.map(c => c.toJSON()),
      foundations: this.foundations.map(pile => pile.map(c => c.toJSON())),
      tableau: this.tableau.map(col => col.map(c => c.toJSON())),
      history: this.history
    };
  }

  /**
   * Restores game state from JSON.
   */
  static fromJSON(data) {
    const game = new SolitaireGame({
      drawMode: data.drawMode,
      scoringMode: data.scoringMode,
      vegasCumulative: data.vegasBalance,
      vegasStake: data.vegasStake || 1,
      isDoubledDown: Boolean(data.isDoubledDown),
      extraPassesBought: data.extraPassesBought || 0,
      extraPassesCost: data.extraPassesCost || 0,
      jackpotBonus: data.jackpotBonus || 0,
      _skipDeal: true
    });

    game.score = data.score;
    game.moves = data.moves;
    game.passesUsed = data.passesUsed;
    game.isWon = data.isWon;
    game.isDoubledDown = Boolean(data.isDoubledDown);
    game.extraPassesBought = data.extraPassesBought || 0;
    game.extraPassesCost = data.extraPassesCost || 0;
    game.jackpotBonus = data.jackpotBonus || 0;
    game.dealSeed = data.dealSeed;
    game.elapsedSeconds = data.elapsedSeconds;
    game.vegasBalance = data.vegasBalance !== undefined ? data.vegasBalance : (data.score || 0);

    game.stock = data.stock.map(c => Card.fromJSON(c));
    game.waste = data.waste.map(c => Card.fromJSON(c));
    game.foundations = data.foundations.map(pile => pile.map(c => Card.fromJSON(c)));
    game.tableau = data.tableau.map(col => col.map(c => Card.fromJSON(c)));
    game.history = data.history || [];
    game.redoStack = [];

    return game;
  }
}

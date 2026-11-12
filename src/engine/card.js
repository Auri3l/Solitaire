/**
 * Solitaire Card Model
 * Represents a standard playing card with suit, rank, color, and state.
 */

export const SUITS = {
  HEARTS: 'H',
  DIAMONDS: 'D',
  CLUBS: 'C',
  SPADES: 'S'
};

export const SUIT_SYMBOLS = {
  H: '♥',
  D: '♦',
  C: '♣',
  S: '♠'
};

export const SUIT_NAMES = {
  H: 'Hearts',
  D: 'Diamonds',
  C: 'Clubs',
  S: 'Spades'
};

export const SUIT_COLORS = {
  H: 'red',
  D: 'red',
  C: 'black',
  S: 'black'
};

export const RANK_NAMES = {
  1: 'A',
  2: '2',
  3: '3',
  4: '4',
  5: '5',
  6: '6',
  7: '7',
  8: '8',
  9: '9',
  10: '10',
  11: 'J',
  12: 'Q',
  13: 'K'
};

export const RANK_FULL_NAMES = {
  1: 'Ace',
  2: 'Two',
  3: 'Three',
  4: 'Four',
  5: 'Five',
  6: 'Six',
  7: 'Seven',
  8: 'Eight',
  9: 'Nine',
  10: 'Ten',
  11: 'Jack',
  12: 'Queen',
  13: 'King'
};

export class Card {
  /**
   * @param {string} suit - 'H', 'D', 'C', or 'S'
   * @param {number} rank - 1 (Ace) to 13 (King)
   * @param {boolean} faceUp - whether card is face up
   */
  constructor(suit, rank, faceUp = false) {
    if (!SUIT_SYMBOLS[suit]) {
      throw new Error(`Invalid suit: ${suit}`);
    }
    if (rank < 1 || rank > 13 || !Number.isInteger(rank)) {
      throw new Error(`Invalid rank: ${rank}. Must be integer 1..13`);
    }

    this.suit = suit;
    this.rank = rank;
    this.faceUp = Boolean(faceUp);
    this.id = `${suit}-${rank}`;
  }

  get color() {
    return SUIT_COLORS[this.suit];
  }

  get symbol() {
    return SUIT_SYMBOLS[this.suit];
  }

  get rankName() {
    return RANK_NAMES[this.rank];
  }

  get fullName() {
    return `${RANK_FULL_NAMES[this.rank]} of ${SUIT_NAMES[this.suit]}`;
  }

  get isRed() {
    return this.color === 'red';
  }

  get isBlack() {
    return this.color === 'black';
  }

  /**
   * Checks if this card can be placed on top of another card in Tableau.
   * Rule: Must be opposite color and exactly one rank lower.
   * @param {Card} targetCard
   * @returns {boolean}
   */
  canStackOnTableau(targetCard) {
    if (!targetCard || !targetCard.faceUp) return false;
    return this.color !== targetCard.color && this.rank === targetCard.rank - 1;
  }

  /**
   * Checks if this card can be placed on a foundation pile.
   * Rule: If foundation is empty, must be an Ace (rank 1).
   * If foundation has a card, must be same suit and exactly one rank higher.
   * @param {Card|null} topFoundationCard
   * @returns {boolean}
   */
  canStackOnFoundation(topFoundationCard) {
    if (!topFoundationCard) {
      return this.rank === 1; // Ace starts the foundation
    }
    return this.suit === topFoundationCard.suit && this.rank === topFoundationCard.rank + 1;
  }

  /**
   * Creates a deep clone of the card.
   * @returns {Card}
   */
  clone() {
    return new Card(this.suit, this.rank, this.faceUp);
  }

  /**
   * Serializes card to plain object.
   */
  toJSON() {
    return {
      suit: this.suit,
      rank: this.rank,
      faceUp: this.faceUp,
      id: this.id
    };
  }

  /**
   * Deserializes from plain object.
   */
  static fromJSON(data) {
    return new Card(data.suit, data.rank, data.faceUp);
  }

  toString() {
    return `${this.faceUp ? '' : '('}${this.rankName}${this.symbol}${this.faceUp ? '' : ')'}`;
  }
}

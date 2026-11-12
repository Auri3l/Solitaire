/**
 * Solitaire Deck Management & Deal Generation
 * Generates 52-card standard deck, Fisher-Yates shuffling, PRNG seeding,
 * and dealing into Tableau and Stock.
 */

import { Card, SUITS } from './card.js';

/**
 * Simple, high-quality 32-bit PRNG (Mulberry32)
 * Produces deterministic sequences given an integer seed.
 */
export function createPRNG(seed = Math.floor(Math.random() * 0x7FFFFFFF)) {
  let s = Math.floor(seed) >>> 0;
  return function nextFloat() {
    s = (s + 0x6D2B79F5) >>> 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * Creates a standard full 52-card deck.
 * @returns {Card[]}
 */
export function createStandardDeck() {
  const deck = [];
  const suitList = [SUITS.HEARTS, SUITS.DIAMONDS, SUITS.CLUBS, SUITS.SPADES];
  for (const suit of suitList) {
    for (let rank = 1; rank <= 13; rank++) {
      deck.push(new Card(suit, rank, false));
    }
  }
  return deck;
}

/**
 * Shuffles an array in place using the Fisher-Yates algorithm.
 * @param {Array} array
 * @param {Function} [randomFn=Math.random]
 * @returns {Array}
 */
export function shuffle(array, randomFn = Math.random) {
  for (let i = array.length - 1; i > 0; i--) {
    const j = Math.floor(randomFn() * (i + 1));
    [array[i], array[j]] = [array[j], array[i]];
  }
  return array;
}

/**
 * Generates a deal given a seed or creates a fresh random deal.
 * Returns { tableau: Card[][], stock: Card[], seed: number }
 *
 * Tableau layout:
 * Column 0: 1 card (face up)
 * Column 1: 2 cards (1 down, 1 up)
 * Column 2: 3 cards (2 down, 1 up)
 * Column 3: 4 cards (3 down, 1 up)
 * Column 4: 5 cards (4 down, 1 up)
 * Column 5: 6 cards (5 down, 1 up)
 * Column 6: 7 cards (6 down, 1 up)
 * Total in tableau: 28 cards.
 * Remaining 24 cards go into Stock (all face down).
 *
 * @param {number|null} [seed=null]
 * @returns {{ tableau: Card[][], stock: Card[], seed: number }}
 */
export function dealGame(seed = null) {
  const chosenSeed = seed !== null && seed !== undefined
    ? Math.abs(Math.floor(seed))
    : Math.floor(Math.random() * 1000000) + 1;

  const prng = createPRNG(chosenSeed);
  const deck = createStandardDeck();
  shuffle(deck, prng);

  const tableau = [[], [], [], [], [], [], []];
  let cardIdx = 0;

  // Deal cards into tableau columns sequentially or row by row
  // Traditional Klondike deals across rows:
  for (let row = 0; row < 7; row++) {
    for (let col = row; col < 7; col++) {
      const card = deck[cardIdx++];
      card.faceUp = (row === col); // Top card of each column is face up
      tableau[col].push(card);
    }
  }

  // Remaining 24 cards into Stock
  const stock = [];
  while (cardIdx < deck.length) {
    const card = deck[cardIdx++];
    card.faceUp = false;
    stock.push(card);
  }

  return {
    tableau,
    stock,
    seed: chosenSeed
  };
}


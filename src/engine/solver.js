/**
 * Klondike Solver
 * Depth-first search over full-information Klondike positions (face-down cards known), used to
 * prove that a deal is winnable before offering it as a "Winnable" deal. Pure logic, no DOM.
 *
 * Cards are encoded as integers: suit * 13 + (rank - 1), suits ordered H, D, C, S (H/D red).
 * The stock and waste are modelled as one "talon" array plus `wp` (how many cards have been
 * drawn into the waste); the waste top is talon[wp - 1]. Redeals are unlimited.
 */

import { dealGame } from './deck.js';

const SUIT_INDEX = { H: 0, D: 1, C: 2, S: 3 };

const suitOf = (card) => Math.floor(card / 13);
const rankOf = (card) => (card % 13) + 1;
const isRed = (card) => suitOf(card) < 2;

function encodeCard(card) {
  return SUIT_INDEX[card.suit] * 13 + (card.rank - 1);
}

/**
 * Builds a solver position from a deal ({ tableau, stock }) or a live game
 * ({ tableau, stock, waste, foundations }).
 */
export function positionFromGame({ tableau, stock = [], waste = [], foundations = [[], [], [], []] }) {
  const found = [0, 0, 0, 0];
  for (const pile of foundations) {
    for (const card of pile) {
      const s = SUIT_INDEX[card.suit];
      found[s] = Math.max(found[s], card.rank);
    }
  }
  const cols = tableau.map((col) => ({
    down: col.filter((c) => !c.faceUp).map(encodeCard),
    up: col.filter((c) => c.faceUp).map(encodeCard),
  }));
  // Waste bottom..top, then the stock in the order it will be drawn (the stock's last element is drawn first)
  const talon = [...waste.map(encodeCard), ...[...stock].reverse().map(encodeCard)];
  return { found, cols, talon, wp: waste.length };
}

function clonePos(pos) {
  return {
    parent: pos,
    moves: [],
    found: pos.found.slice(),
    cols: pos.cols.map((c) => ({ down: c.down.slice(), up: c.up.slice() })),
    talon: pos.talon.slice(),
    wp: pos.wp,
  };
}

function hashPos(pos) {
  let h = pos.found.join('') + '|';
  for (const c of pos.cols) h += c.down.length + ':' + c.up.join(',') + ';';
  return h + '|' + pos.talon.join(',') + '/' + pos.wp;
}

function canGoToFoundation(pos, card) {
  return pos.found[suitOf(card)] === rankOf(card) - 1;
}

function canStack(card, onto) {
  return isRed(card) !== isRed(onto) && rankOf(card) === rankOf(onto) - 1;
}

/** Turns a column's top face-down card up once its face-up cards are gone. */
function flip(col) {
  if (col.up.length === 0 && col.down.length > 0) col.up.push(col.down.pop());
}

/** A foundation move that can never hurt: both opposite-colour piles are high enough. */
function isSafeToFoundation(pos, card) {
  const rank = rankOf(card);
  if (rank <= 2) return true;
  const red = isRed(card);
  const opposite = red ? [2, 3] : [0, 1];
  return opposite.every((s) => pos.found[s] >= rank - 1);
}

/** Plays every safe foundation move (in place). */
function playSafeMoves(pos) {
  let moved = true;
  while (moved) {
    moved = false;
    for (const col of pos.cols) {
      const top = col.up[col.up.length - 1];
      if (top !== undefined && canGoToFoundation(pos, top) && isSafeToFoundation(pos, top)) {
        col.up.pop();
        pos.found[suitOf(top)]++;
        flip(col);
        pos.moves.push({ card: top, to: 'f' });
        moved = true;
      }
    }
    if (pos.wp > 0) {
      const top = pos.talon[pos.wp - 1];
      if (canGoToFoundation(pos, top) && isSafeToFoundation(pos, top)) {
        pos.talon.splice(pos.wp - 1, 1);
        pos.wp--;
        pos.found[suitOf(top)]++;
        pos.moves.push({ card: top, to: 'f' });
        moved = true;
      }
    }
  }
}

/** Indexes of talon cards that can be brought to the top of the waste by drawing (with redeals). */
function reachableTalon(pos, drawMode) {
  const len = pos.talon.length;
  const reach = new Set();
  if (pos.wp > 0) reach.add(pos.wp - 1);
  let w = pos.wp;
  while (w < len) {
    w = Math.min(len, w + drawMode);
    reach.add(w - 1);
  }
  w = 0;
  while (w < pos.wp) {
    w = Math.min(len, w + drawMode);
    reach.add(w - 1);
  }
  return [...reach];
}

function takeFromTalon(pos, index) {
  const next = clonePos(pos);
  const [card] = next.talon.splice(index, 1);
  next.wp = index;
  return { next, card };
}

function isWon(pos) {
  if (pos.found.every((f) => f === 13)) return true;
  // Everything face up with the talon gone: the rest plays straight to the foundations
  return pos.talon.length === 0 && pos.cols.every((c) => c.down.length === 0);
}

/** Successor positions, best candidates first. */
function successors(pos, drawMode) {
  const first = [];   // moves that turn up a face-down card or reach the foundations
  const second = [];  // talon to tableau, building
  const reach = reachableTalon(pos, drawMode);

  // Foundation moves
  pos.cols.forEach((col, ci) => {
    const top = col.up[col.up.length - 1];
    if (top !== undefined && canGoToFoundation(pos, top)) {
      const next = clonePos(pos);
      next.cols[ci].up.pop();
      next.found[suitOf(top)]++;
      flip(next.cols[ci]);
      next.moves.push({ card: top, to: 'f' });
      first.push(next);
    }
  });
  for (const index of reach) {
    if (canGoToFoundation(pos, pos.talon[index])) {
      const { next, card } = takeFromTalon(pos, index);
      next.found[suitOf(card)]++;
      next.moves.push({ card, to: 'f' });
      first.push(next);
    }
  }

  // Tableau to tableau
  pos.cols.forEach((src, si) => {
    for (let i = 0; i < src.up.length; i++) {
      const moving = src.up[i];
      const wholeRun = i === 0;
      const exposesFoundationCard = !wholeRun && canGoToFoundation(pos, src.up[i - 1]);
      // Partial runs only help when they free a card for the foundations
      if (!wholeRun && !exposesFoundationCard) continue;
      pos.cols.forEach((dst, di) => {
        if (di === si) return;
        const target = dst.up[dst.up.length - 1];
        let legal;
        if (target === undefined) {
          // Kings to empty columns, and only when that achieves something
          legal = dst.down.length === 0 && rankOf(moving) === 13 && !(wholeRun && src.down.length === 0);
        } else {
          legal = canStack(moving, target);
        }
        if (!legal) return;
        const next = clonePos(pos);
        const run = next.cols[si].up.splice(i);
        next.cols[di].up.push(...run);
        flip(next.cols[si]);
        next.moves.push({ card: moving, to: di });
        if (wholeRun && src.down.length > 0) first.push(next); else second.push(next);
      });
    }
  });

  // Talon to tableau
  for (const index of reach) {
    const card = pos.talon[index];
    pos.cols.forEach((dst, di) => {
      const target = dst.up[dst.up.length - 1];
      const legal = target === undefined
        ? dst.down.length === 0 && rankOf(card) === 13
        : canStack(card, target);
      if (!legal) return;
      const { next } = takeFromTalon(pos, index);
      next.cols[di].up.push(card);
      next.moves.push({ card, to: di });
      second.push(next);
    });
  }

  return first.concat(second);
}

/** The moves that lead from the search root to pos. */
function movesTo(pos) {
  const chain = [];
  for (let p = pos; p; p = p.parent) chain.push(p.moves);
  return chain.reverse().flat();
}

/**
 * Searches for a win from the given position.
 * @param {Object} start - position from positionFromGame
 * @param {Object} [options]
 * @param {number} [options.drawMode=1]
 * @param {number} [options.maxNodes=20000] - positions to expand before giving up
 * @param {number} [options.deadline=Infinity] - Date.now() value after which to give up
 * @returns {{ solved: boolean, exhausted: boolean, nodes: number, moves?: Array<{card: number, to: 'f'|number}> }}
 *   moves (when solved) lists each card played, to a foundation ('f') or a tableau column;
 *   exhausted is true when every reachable position was searched (the deal is unwinnable for this solver)
 */
export function solvePosition(start, { drawMode = 1, maxNodes = 20000, deadline = Infinity } = {}) {
  const root = clonePos(start);
  root.parent = null;
  playSafeMoves(root);
  const seen = new Set([hashPos(root)]);
  const stack = [root];
  let nodes = 0;

  while (stack.length > 0) {
    const pos = stack.pop();
    if (isWon(pos)) return { solved: true, exhausted: false, nodes, moves: movesTo(pos) };
    nodes++;
    if (nodes > maxNodes || ((nodes & 255) === 0 && Date.now() > deadline)) {
      return { solved: false, exhausted: false, nodes };
    }
    const children = successors(pos, drawMode);
    // Push in reverse so the best candidate is explored first
    for (let i = children.length - 1; i >= 0; i--) {
      const child = children[i];
      playSafeMoves(child);
      const key = hashPos(child);
      if (seen.has(key)) continue;
      seen.add(key);
      stack.push(child);
    }
  }
  return { solved: false, exhausted: true, nodes };
}

/**
 * Checks whether the deal produced by `seed` can be won.
 * @returns {{ solved: boolean, exhausted: boolean, nodes: number }}
 */
export function isSeedWinnable(seed, options = {}) {
  return solvePosition(positionFromGame(dealGame(seed)), options);
}

/**
 * Picks a fresh random deal that the solver proves winnable.
 * @param {Object} [options]
 * @param {number} [options.drawMode=1]
 * @param {Iterable<number>} [options.avoidSeeds] - recently played seeds not to repeat
 * @param {number} [options.budgetMs=350] - total time to spend searching
 * @param {number} [options.maxNodesPerSeed=15000]
 * @param {Function} [options.random=Math.random]
 * @returns {{ seed: number, verified: boolean }} verified is false when no deal was proven in time
 */
export function findWinnableSeed({
  drawMode = 1,
  avoidSeeds = [],
  budgetMs = 350,
  maxNodesPerSeed = 15000,
  random = Math.random,
} = {}) {
  const avoid = new Set(avoidSeeds);
  const deadline = Date.now() + budgetMs;
  const randomSeed = () => {
    let seed;
    do {
      seed = Math.floor(random() * 1000000) + 1;
    } while (avoid.has(seed));
    return seed;
  };

  let lastTried = randomSeed();
  do {
    const seed = lastTried;
    avoid.add(seed);
    const result = isSeedWinnable(seed, { drawMode, maxNodes: maxNodesPerSeed, deadline });
    if (result.solved) return { seed, verified: true };
    lastTried = randomSeed();
  } while (Date.now() < deadline);

  return { seed: lastTried, verified: false };
}

/**
 * Solitaire Smart Hint Engine
 * Analyzes the board state and finds strategically optimal moves.
 */

export class HintEngine {
  /**
   * Evaluates the current game state and returns the best recommended move.
   * @param {import('./solitaire.js').SolitaireGame} game
   * @returns {{ source: Object, target: Object, description: string, priority: number }|null}
   */
  static findBestHint(game) {
    if (game.isWon) return null;

    const candidateMoves = [];

    // 1. Check all Foundation moves
    // From Waste -> Foundation
    if (game.waste.length > 0) {
      const card = game.waste[game.waste.length - 1];
      for (let f = 0; f < 4; f++) {
        const source = { pile: 'waste' };
        const target = { pile: 'foundation', foundationIndex: f };
        if (game.validateMove(source, target).valid) {
          const priority = card.rank <= 2 ? 100 : 80;
          candidateMoves.push({
            source,
            target,
            card,
            description: `Move ${card.rankName}${card.symbol} from Waste to Foundation`,
            priority
          });
        }
      }
    }

    // From Tableau -> Foundation
    for (let c = 0; c < 7; c++) {
      const col = game.tableau[c];
      if (col.length === 0) continue;
      const cardIndex = col.length - 1;
      const card = col[cardIndex];
      if (!card.faceUp) continue;

      for (let f = 0; f < 4; f++) {
        const source = { pile: 'tableau', col: c, cardIndex };
        const target = { pile: 'foundation', foundationIndex: f };
        if (game.validateMove(source, target).valid) {
          // If uncovering a face-down card underneath, extremely high priority!
          const uncoversFaceDown = cardIndex > 0 && !col[cardIndex - 1].faceUp;
          let priority = 70;
          if (uncoversFaceDown) priority = 120;
          else if (card.rank <= 2) priority = 95;
          else if (card.rank >= 3 && this._isSafeFoundationMove(card, game)) priority = 75;
          else priority = 40; // Potentially risky

          candidateMoves.push({
            source,
            target,
            card,
            description: `Move ${card.rankName}${card.symbol} to Foundation${uncoversFaceDown ? ' (uncovers a hidden card!)' : ''}`,
            priority
          });
        }
      }
    }

    // 2. Check Tableau -> Tableau moves (both full stacks and sub-stacks)
    for (let srcCol = 0; srcCol < 7; srcCol++) {
      const sourceCol = game.tableau[srcCol];
      if (sourceCol.length === 0) continue;

      // Find first face-up card in column
      const firstFaceUpIdx = sourceCol.findIndex(card => card.faceUp);
      if (firstFaceUpIdx === -1) continue;

      for (let cardIdx = firstFaceUpIdx; cardIdx < sourceCol.length; cardIdx++) {
        const uncoversFaceDown = cardIdx > 0 && !sourceCol[cardIdx - 1].faceUp;
        const isBaseOfColumn = cardIdx === 0;
        const movingCard = sourceCol[cardIdx];

        for (let destCol = 0; destCol < 7; destCol++) {
          if (srcCol === destCol) continue;
          const source = { pile: 'tableau', col: srcCol, cardIndex: cardIdx };
          const target = { pile: 'tableau', col: destCol };

          if (game.validateMove(source, target).valid) {
            // Disqualify moves that immediately or cyclically reverse recent actions
            if (this._isMoveCycling(game, source, target, movingCard)) {
              continue;
            }

            // If moving a King from base to another empty column, skip as redundant
            if (movingCard.rank === 13 && isBaseOfColumn && game.tableau[destCol].length === 0) {
              continue;
            }

            const destCards = game.tableau[destCol];
            const destCard = destCards.length > 0 ? destCards[destCards.length - 1] : null;

            // Check if moving from a face-up parent card
            if (cardIdx > 0 && sourceCol[cardIdx - 1].faceUp) {
              const parentCard = sourceCol[cardIdx - 1];
              const isParentValidBuild = parentCard.rank === movingCard.rank + 1 && parentCard.isRed !== movingCard.isRed;

              if (isParentValidBuild) {
                // movingCard is already built properly on parentCard.
                // Moving it to destCol is a lateral transfer between identical rank parents.
                // This is ONLY constructive if parentCard can immediately move to Foundation!
                const parentCanGoToFoundation = this._canCardGoToFoundation(game, parentCard);
                if (!parentCanGoToFoundation) {
                  // Pointless lateral move that leads to ping-pong loops
                  continue;
                }

                candidateMoves.push({
                  source,
                  target,
                  card: movingCard,
                  description: `Move ${movingCard.rankName}${movingCard.symbol} onto ${destCard ? destCard.rankName + destCard.symbol : 'empty space'} (frees ${parentCard.rankName}${parentCard.symbol} for Foundation)`,
                  priority: 80
                });
                continue;
              } else {
                // parentCard is NOT a valid build (e.g. custom/edge-case deals),
                // so moving it onto destCard properly builds it!
                candidateMoves.push({
                  source,
                  target,
                  card: movingCard,
                  description: `Move ${movingCard.rankName}${movingCard.symbol} onto ${destCard ? destCard.rankName + destCard.symbol : 'empty space'}`,
                  priority: 60
                });
                continue;
              }
            }

            // Uncovering face-down card
            if (uncoversFaceDown) {
              candidateMoves.push({
                source,
                target,
                card: movingCard,
                description: `Move ${movingCard.rankName}${movingCard.symbol} onto ${destCard ? destCard.rankName + destCard.symbol : 'empty space'} (uncovers a hidden card!)`,
                priority: 110
              });
              continue;
            }

            // Base of column move (clearing an empty column)
            if (isBaseOfColumn && destCards.length > 0) {
              const hasWaitingKing = this._hasWaitingKing(game);
              candidateMoves.push({
                source,
                target,
                card: movingCard,
                description: `Move ${movingCard.rankName}${movingCard.symbol} onto ${destCard.rankName}${destCard.symbol}${hasWaitingKing ? ' (frees an empty column for a King)' : ''}`,
                priority: hasWaitingKing ? 85 : 40
              });
              continue;
            }
          }
        }
      }
    }

    // 3. Check Waste -> Tableau moves
    if (game.waste.length > 0) {
      const wasteCard = game.waste[game.waste.length - 1];
      for (let destCol = 0; destCol < 7; destCol++) {
        const source = { pile: 'waste' };
        const target = { pile: 'tableau', col: destCol };
        if (game.validateMove(source, target).valid) {
          // If placing King on empty column, give high priority if we have cards waiting
          let priority = 65;
          if (wasteCard.rank === 13 && game.tableau[destCol].length === 0) {
            priority = 90;
          }

          candidateMoves.push({
            source,
            target,
            card: wasteCard,
            description: `Move ${wasteCard.rankName}${wasteCard.symbol} from Waste to Tableau`,
            priority
          });
        }
      }
    }

    // 4. Drawing from Stock / Recycling Waste
    if (game.stock.length > 0) {
      const isFresh = game.waste.length === 0 && (!game.history || game.history.length === 0);
      const canYield = this._canStockOrWasteYieldMove(game);
      const isExhausted = this._isStockCycleExhausted(game);

      if (!isExhausted && (isFresh || canYield)) {
        candidateMoves.push({
          source: { pile: 'stock' },
          target: { pile: 'waste' },
          card: null,
          description: `Draw cards from Stock (${game.stock.length} remaining)`,
          priority: 30
        });
      }
    } else if (game.waste.length > 0 && game.passesRemaining > 0) {
      if (!this._isStockCycleExhausted(game) && this._canStockOrWasteYieldMove(game)) {
        candidateMoves.push({
          source: { pile: 'stock' },
          target: { pile: 'stock' },
          card: null,
          description: 'Recycle Waste back to Stock',
          priority: 25
        });
      }
    }

    if (candidateMoves.length === 0) {
      return null;
    }

    // Sort by descending priority
    candidateMoves.sort((a, b) => b.priority - a.priority);
    return candidateMoves[0];
  }

  /**
   * Checks if a card can stack on any of the foundations.
   * @private
   */
  static _canCardGoToFoundation(game, card) {
    if (!card || !card.faceUp) return false;
    for (let f = 0; f < 4; f++) {
      const fPile = game.foundations[f];
      const topCard = fPile.length > 0 ? fPile[fPile.length - 1] : null;
      if (card.canStackOnFoundation(topCard)) {
        return true;
      }
    }
    return false;
  }

  /**
   * Checks if there is a waiting King in waste, stock, or covering face-down cards in tableau.
   * @private
   */
  static _hasWaitingKing(game) {
    if (game.waste.length > 0 && game.waste[game.waste.length - 1].rank === 13) {
      return true;
    }
    for (let c = 0; c < 7; c++) {
      const col = game.tableau[c];
      const firstUp = col.findIndex(card => card.faceUp);
      if (firstUp > 0 && col[firstUp].rank === 13) {
        return true;
      }
    }
    if (game.stock && game.stock.some(card => card.rank === 13)) {
      return true;
    }
    return false;
  }

  /**
   * Checks if drawing or recycling could ever yield a card that can be placed on Tableau or Foundation.
   * Simulates future deck cycling until repetition or pass exhaustion.
   * @private
   */
  static _canStockOrWasteYieldMove(game) {
    if (!game.stock && !game.waste) return false;
    if (game.stock.length === 0 && (game.waste.length === 0 || game.passesRemaining <= 0)) {
      return false;
    }

    const simStock = game.stock.map(c => c.clone());
    const simWaste = game.waste.map(c => c.clone());
    const drawMode = game.drawMode;
    let passes = game.passesRemaining;
    const seen = new Set();

    while (true) {
      const stateSig = simStock.map(c => c.id).join(',') + '|' + (simWaste.length ? simWaste[simWaste.length - 1].id : '');
      if (seen.has(stateSig)) break;
      seen.add(stateSig);

      if (simStock.length > 0) {
        const count = Math.min(drawMode, simStock.length);
        for (let i = 0; i < count; i++) {
          simWaste.push(simStock.pop());
        }
      } else if (simWaste.length > 0 && passes > 0) {
        passes--;
        while (simWaste.length > 0) {
          simStock.push(simWaste.pop());
        }
      } else {
        break;
      }

      if (simWaste.length > 0) {
        const top = simWaste[simWaste.length - 1];
        if (this._canCardGoToFoundation(game, top) || this._canCardGoToTableau(game, top)) {
          return true;
        }
      }
    }
    return false;
  }

  /**
   * Checks if a card can stack on any tableau column.
   * @private
   */
  static _canCardGoToTableau(game, card) {
    if (!card) return false;
    for (let c = 0; c < 7; c++) {
      const col = game.tableau[c];
      if (col.length === 0) {
        if (card.rank === 13) return true;
      } else {
        const top = col[col.length - 1];
        if (top.faceUp && card.canStackOnTableau(top)) return true;
      }
    }
    return false;
  }

  /**
   * Determines if stock/waste has been cycled through without making any progress moves on board.
   * @private
   */
  static _isStockCycleExhausted(game) {
    if (!game.history || game.history.length === 0) return false;

    let recyclesSinceLastMove = 0;
    for (let i = game.history.length - 1; i >= 0; i--) {
      const action = game.history[i];
      if (action.type === 'MOVE') {
        break;
      }
      if (action.type === 'RECYCLE') {
        recyclesSinceLastMove++;
      }
    }

    const totalDeck = (game.stock ? game.stock.length : 0) + (game.waste ? game.waste.length : 0);
    const maxRecycles = (game.drawMode === 1 || totalDeck % 3 === 0) ? 1 : 3;

    if (recyclesSinceLastMove >= maxRecycles && (!game.stock || game.stock.length === 0)) {
      return true;
    }

    return false;
  }

  /**
   * Detects if this move would reverse recent actions and cause an endless loop.
   * @private
   */
  static _isMoveCycling(game, source, target, movingCard) {
    if (!game.history || game.history.length === 0) return false;

    // 1. Check immediate undo of the very last action
    const lastAction = game.history[game.history.length - 1];
    if (lastAction.type === 'MOVE') {
      const isReverseSource = (
        (source.pile === 'tableau' && lastAction.target.pile === 'tableau' && source.col === lastAction.target.col) ||
        (source.pile === 'foundation' && lastAction.target.pile === 'foundation' && source.foundationIndex === lastAction.target.foundationIndex)
      );
      const isReverseTarget = (
        (target.pile === 'tableau' && lastAction.source.pile === 'tableau' && target.col === lastAction.source.col) ||
        (target.pile === 'foundation' && lastAction.source.pile === 'foundation' && target.foundationIndex === lastAction.source.foundationIndex)
      );
      if (isReverseSource && isReverseTarget) {
        return true;
      }
    }

    // 2. Check recent history (last 6 actions) for cycling between columns
    if (source.pile === 'tableau' && target.pile === 'tableau' && movingCard) {
      const windowSize = Math.min(game.history.length, 6);
      for (let i = game.history.length - 1; i >= game.history.length - windowSize; i--) {
        const action = game.history[i];
        // If a card was flipped or moved to foundation, state progressed
        if (action.flippedCardId) break;
        if (action.type === 'MOVE' && (action.source.pile === 'foundation' || action.target.pile === 'foundation')) break;

        // Did we move from target.col to source.col?
        if (action.type === 'MOVE' && action.source.pile === 'tableau' && action.target.pile === 'tableau') {
          if (action.source.col === target.col && action.target.col === source.col) {
            return true;
          }
        }
      }
    }

    return false;
  }

  /**
   * Determines if moving a card to foundation is safe.
   * Safe when both cards of rank - 1 of opposite colors are already in foundations.
   * @private
   */
  static _isSafeFoundationMove(card, game) {
    if (card.rank <= 2) return true;
    const requiredRank = card.rank - 1;
    // Check opposite color foundations
    const oppositeColor = card.isRed ? 'black' : 'red';
    let countSafe = 0;
    for (const pile of game.foundations) {
      if (pile.length > 0) {
        const top = pile[pile.length - 1];
        if (top.color === oppositeColor && top.rank >= requiredRank) {
          countSafe++;
        }
      }
    }
    return countSafe >= 2;
  }
}

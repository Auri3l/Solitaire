"""Hint Engine for Solitaire Suite.

Analyzes available moves across Klondike, FreeCell, and Spider variants,
scoring and prioritizing the most advantageous moves and generating
human-friendly explanations for the player.
"""

from dataclasses import dataclass
from typing import Optional, List, Any
from solitaire.core.base_game import BaseGame, Move
from solitaire.core.card import Card, Suit, Rank


@dataclass
class Hint:
    """Represents a recommended move with contextual description."""
    move: Move
    score: int
    description: str
    source_pile: str
    dest_pile: str
    card: Optional[Card] = None


class HintEngine:
    """Evaluates and ranks legal moves across Solitaire game variants."""

    @staticmethod
    def _format_card_name(card: Optional[Card]) -> str:
        if card is None:
            return "card"
        suit_names = {
            Suit.SPADES: "Spades",
            Suit.HEARTS: "Hearts",
            Suit.DIAMONDS: "Diamonds",
            Suit.CLUBS: "Clubs",
        }
        suit_str = suit_names.get(card.suit, card.suit.name.capitalize())
        rank_str = card.rank.display_str
        if card.rank == Rank.ACE:
            rank_str = "Ace"
        elif card.rank == Rank.JACK:
            rank_str = "Jack"
        elif card.rank == Rank.QUEEN:
            rank_str = "Queen"
        elif card.rank == Rank.KING:
            rank_str = "King"
        return f"{rank_str} of {suit_str}"

    @staticmethod
    def _format_pile_name(pile_id: str) -> str:
        if pile_id.startswith("foundation"):
            idx = pile_id.split("_")[-1]
            return f"Foundation {int(idx)+1 if idx.isdigit() else idx}"
        elif pile_id.startswith("tableau"):
            idx = pile_id.split("_")[-1]
            return f"Column {int(idx)+1 if idx.isdigit() else idx}"
        elif pile_id.startswith("cascade"):
            idx = pile_id.split("_")[-1]
            return f"Cascade {int(idx)+1 if idx.isdigit() else idx}"
        elif pile_id.startswith("freecell") or pile_id.startswith("cell"):
            idx = pile_id.split("_")[-1]
            return f"Free Cell {int(idx)+1 if idx.isdigit() else idx}"
        elif pile_id == "waste":
            return "Waste Pile"
        elif pile_id == "stock":
            return "Stock"
        return pile_id.replace("_", " ").title()

    @classmethod
    def get_hint(cls, game: BaseGame) -> Optional[Hint]:
        """Calculates the best recommended move for the current game state."""
        # Check if the game's internal hint engine found a prioritized move
        game_hint_move = game.get_hint()
        if game_hint_move is not None:
            return cls._build_hint_from_move(game, game_hint_move, score=100)

        # Otherwise evaluate all legal moves
        legal_moves = game.get_legal_moves()
        if not legal_moves:
            return None

        best_hint: Optional[Hint] = None
        for move in legal_moves:
            hint = cls._score_move(game, move)
            if best_hint is None or hint.score > best_hint.score:
                best_hint = hint

        return best_hint

    @classmethod
    def _score_move(cls, game: BaseGame, move: Move) -> Hint:
        src = move.source_pile_id
        dst = move.dest_pile_id
        score = 10

        # Determine target card
        src_pile = game.get_pile(src)
        card: Optional[Card] = None
        if src_pile and src_pile.cards:
            if move.card_id is not None:
                for c in src_pile.cards:
                    if getattr(c, "id", None) == move.card_id:
                        card = c
                        break
            if card is None:
                card = src_pile.top_card

        # Move to foundation (highest priority in Klondike & FreeCell)
        if dst.startswith("foundation"):
            score += 80
            if card and card.rank in (Rank.ACE, Rank.TWO):
                score += 30  # Always safe to move Aces & Twos

        # Uncovering a face-down card in tableau
        if src.startswith("tableau") and src_pile and len(src_pile.cards) > move.card_count:
            uncovered_idx = len(src_pile.cards) - move.card_count - 1
            if uncovered_idx >= 0 and not src_pile.cards[uncovered_idx].face_up:
                score += 50

        # Moving to empty tableau/cascade (valuable for Kings or long runs)
        dst_pile = game.get_pile(dst)
        if (dst.startswith("tableau") or dst.startswith("cascade")) and dst_pile and len(dst_pile) == 0:
            if card and card.rank == Rank.KING:
                score += 40
            else:
                score += 15

        # Stock deal
        if str(move.move_type) == "deal_stock" or src == "stock":
            score = 25  # Only when productive tableau moves are exhausted

        # FreeCell cell moves
        if dst.startswith("freecell") or dst.startswith("cell"):
            score = 15  # Using a free cell is a holding action

        card_desc = cls._format_card_name(card)
        src_desc = cls._format_pile_name(src)
        dst_desc = cls._format_pile_name(dst)

        if str(move.move_type) == "deal_stock" or src == "stock":
            desc = "Deal next cards from the Stock."
        elif dst.startswith("foundation"):
            desc = f"Move {card_desc} to {dst_desc}."
        elif card:
            desc = f"Move {card_desc} from {src_desc} to {dst_desc}."
        else:
            desc = f"Move from {src_desc} to {dst_desc}."

        return Hint(
            move=move,
            score=score,
            description=desc,
            source_pile=src,
            dest_pile=dst,
            card=card
        )

    @classmethod
    def _build_hint_from_move(cls, game: BaseGame, move: Move, score: int = 100) -> Hint:
        src = move.source_pile_id
        dst = move.dest_pile_id
        src_pile = game.get_pile(src)
        card: Optional[Card] = None

        if src_pile and src_pile.cards:
            if move.card_id is not None:
                for c in src_pile.cards:
                    if getattr(c, "id", None) == move.card_id:
                        card = c
                        break
            if card is None:
                card = src_pile.peek()

        card_desc = cls._format_card_name(card)
        src_desc = cls._format_pile_name(src)
        dst_desc = cls._format_pile_name(dst)

        if str(move.move_type) == "deal_stock" or src == "stock":
            desc = "Deal next cards from Stock."
        elif dst.startswith("foundation"):
            desc = f"Move {card_desc} to {dst_desc}."
        elif card:
            desc = f"Move {card_desc} from {src_desc} to {dst_desc}."
        else:
            desc = f"Move cards from {src_desc} to {dst_desc}."

        return Hint(
            move=move,
            score=score,
            description=desc,
            source_pile=src,
            dest_pile=dst,
            card=card
        )

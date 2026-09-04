"""Solitaire Core Layer.

Exports universal card representations, containers, commands, and base game abstractions.
"""

from solitaire.core.card import Color, Suit, Rank, Card
from solitaire.core.pile import PileType, Pile, Deck
from solitaire.core.commands import (
    Command,
    CardMoveCommand,
    MoveCommand,
    StockDealCommand,
    RecycleCommand,
    CommandHistory,
    KlondikeCardMoveCommand,
    KlondikeStockDealCommand,
    KlondikeRecycleCommand,
)
from solitaire.core.base_game import GameStatus, Move, MoveResult, BaseGame, GameState

__all__ = [
    "Color",
    "Suit",
    "Rank",
    "Card",
    "PileType",
    "Pile",
    "Deck",
    "Command",
    "CardMoveCommand",
    "MoveCommand",
    "StockDealCommand",
    "RecycleCommand",
    "CommandHistory",
    "KlondikeCardMoveCommand",
    "KlondikeStockDealCommand",
    "KlondikeRecycleCommand",
    "GameStatus",
    "Move",
    "MoveResult",
    "BaseGame",
    "GameState",
]

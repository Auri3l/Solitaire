"""Core Card models and primitives.

Defines Suit, Rank, Color, and Card data representations.
"""

from enum import Enum, IntEnum, unique
from typing import Dict, Any, Optional, Union


@unique
class Color(Enum):
    """Represents card optical color."""
    BLACK = "black"
    RED = "red"

    def __str__(self) -> str:
        return self.value


@unique
class Suit(Enum):
    """Defines the four standard French playing card suits."""
    SPADES = ("spades", "♠", Color.BLACK)
    HEARTS = ("hearts", "♥", Color.RED)
    DIAMONDS = ("diamonds", "♦", Color.RED)
    CLUBS = ("clubs", "♣", Color.BLACK)

    def __init__(self, suit_name: str, symbol: str, color: Color) -> None:
        self.suit_name = suit_name
        self.symbol = symbol
        self.color = color

    @property
    def is_red(self) -> bool:
        return self.color == Color.RED

    @property
    def is_black(self) -> bool:
        return self.color == Color.BLACK

    @classmethod
    def from_string(cls, value: str) -> "Suit":
        """Accepts 'spades', 'S', '♠', etc. (case-insensitive)."""
        val = value.strip().lower()
        mapping = {
            "spades": cls.SPADES, "spade": cls.SPADES, "s": cls.SPADES, "♠": cls.SPADES,
            "hearts": cls.HEARTS, "heart": cls.HEARTS, "h": cls.HEARTS, "♥": cls.HEARTS,
            "diamonds": cls.DIAMONDS, "diamond": cls.DIAMONDS, "d": cls.DIAMONDS, "♦": cls.DIAMONDS,
            "clubs": cls.CLUBS, "club": cls.CLUBS, "c": cls.CLUBS, "♣": cls.CLUBS,
        }
        if val in mapping:
            return mapping[val]
        raise ValueError(f"Invalid suit representation: {value}")

    def __str__(self) -> str:
        return self.symbol


@unique
class Rank(IntEnum):
    """Defines the thirteen standard ranks with 1-based integer values."""
    ACE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13

    @property
    def display_str(self) -> str:
        _DISPLAY_MAP = {
            1: "A", 2: "2", 3: "3", 4: "4", 5: "5",
            6: "6", 7: "7", 8: "8", 9: "9", 10: "10",
            11: "J", 12: "Q", 13: "K"
        }
        return _DISPLAY_MAP[self.value]

    @property
    def is_face_card(self) -> bool:
        return self.value in (11, 12, 13)

    @property
    def is_ace(self) -> bool:
        return self.value == 1

    @property
    def is_king(self) -> bool:
        return self.value == 13

    @classmethod
    def from_string(cls, value: str) -> "Rank":
        val = value.strip().upper()
        _PARSE_MAP = {
            "A": cls.ACE, "1": cls.ACE, "ACE": cls.ACE,
            "2": cls.TWO, "3": cls.THREE, "4": cls.FOUR, "5": cls.FIVE,
            "6": cls.SIX, "7": cls.SEVEN, "8": cls.EIGHT, "9": cls.NINE, "10": cls.TEN,
            "J": cls.JACK, "JACK": cls.JACK,
            "Q": cls.QUEEN, "QUEEN": cls.QUEEN,
            "K": cls.KING, "KING": cls.KING
        }
        if val in _PARSE_MAP:
            return _PARSE_MAP[val]
        raise ValueError(f"Invalid rank representation: {value}")

    def __str__(self) -> str:
        return self.display_str


class Card:
    """Represents an individual physical playing card instance.

    Attributes:
        card_id: Unique integer identifier across the deck (0..51 or 0..103).
        suit: Suit enum (SPADES, HEARTS, DIAMONDS, CLUBS).
        rank: Rank IntEnum (1..13).
        is_face_up: Boolean indicating if card face is visible to player.
    """
    __slots__ = ("_card_id", "_suit", "_rank", "_is_face_up")

    def __init__(
        self,
        suit: Suit,
        rank: Union[Rank, int],
        is_face_up: bool = False,
        card_id: Optional[int] = None,
        *,
        id: Optional[int] = None,
        face_up: Optional[bool] = None,
    ) -> None:
        if not isinstance(suit, Suit):
            raise TypeError(f"Expected Suit enum, got {type(suit)}")
        if isinstance(rank, int) and not isinstance(rank, bool):
            rank = Rank(rank)
        elif not isinstance(rank, Rank):
            raise TypeError(f"Expected Rank enum or int, got {type(rank)}")

        # Resolve face_up / is_face_up aliases
        effective_face_up = face_up if face_up is not None else is_face_up

        # Resolve id / card_id aliases
        effective_card_id = id if id is not None else (card_id if card_id is not None else 0)

        self._card_id: int = int(effective_card_id)
        self._suit: Suit = suit
        self._rank: Rank = rank
        self._is_face_up: bool = bool(effective_face_up)

    @property
    def card_id(self) -> int:
        return self._card_id

    @property
    def id(self) -> int:
        """Alias for card_id conforming to PROJECT.md."""
        return self._card_id

    @property
    def suit(self) -> Suit:
        return self._suit

    @property
    def rank(self) -> Rank:
        return self._rank

    @property
    def color(self) -> Color:
        return self._suit.color

    @property
    def is_red(self) -> bool:
        return self._suit.is_red

    @property
    def is_black(self) -> bool:
        return self._suit.is_black

    @property
    def is_face_up(self) -> bool:
        return self._is_face_up

    @is_face_up.setter
    def is_face_up(self, value: bool) -> None:
        self._is_face_up = bool(value)

    @property
    def face_up(self) -> bool:
        """Alias for is_face_up conforming to PROJECT.md."""
        return self._is_face_up

    @face_up.setter
    def face_up(self, value: bool) -> None:
        self._is_face_up = bool(value)

    @property
    def display_name(self) -> str:
        """Returns string such as 'A♠', '10♥', or '??' if face-down."""
        if not self._is_face_up:
            return "??"
        return f"{self._rank.display_str}{self._suit.symbol}"

    @property
    def full_name(self) -> str:
        """Unconditional face-up name for logging/debugging (e.g. 'A♠')."""
        return f"{self._rank.display_str}{self._suit.symbol}"

    def flip(self) -> None:
        """Toggles face visibility."""
        self._is_face_up = not self._is_face_up

    def clone(
        self,
        is_face_up: Optional[bool] = None,
        card_id: Optional[int] = None,
        *,
        id: Optional[int] = None,
        face_up: Optional[bool] = None,
    ) -> "Card":
        """Creates an independent copy of this card instance."""
        target_face_up = face_up if face_up is not None else is_face_up
        target_id = id if id is not None else card_id
        return Card(
            suit=self._suit,
            rank=self._rank,
            is_face_up=self._is_face_up if target_face_up is None else target_face_up,
            card_id=self._card_id if target_id is None else target_id,
        )

    def matches_rank_and_suit(self, other: "Card") -> bool:
        """Tests whether two cards share rank and suit, regardless of card_id or face-up state."""
        return self._suit == other._suit and self._rank == other._rank

    def to_dict(self) -> Dict[str, Any]:
        """Serializes card to dictionary."""
        return {
            "card_id": self._card_id,
            "suit": self._suit.name,
            "rank": self._rank.value,
            "is_face_up": self._is_face_up
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Card":
        """Deserializes card from dictionary."""
        suit_raw = data["suit"]
        if isinstance(suit_raw, Suit):
            suit = suit_raw
        elif isinstance(suit_raw, str):
            suit = Suit[suit_raw] if suit_raw in Suit.__members__ else Suit.from_string(suit_raw)
        else:
            raise TypeError(f"Invalid suit representation: {suit_raw}")

        return cls(
            suit=suit,
            rank=data["rank"],
            is_face_up=data.get("is_face_up", data.get("face_up", False)),
            card_id=data.get("card_id", data.get("id", 0)),
        )

    def __eq__(self, other: object) -> bool:
        """Identity and state equality.
        Two cards are strictly equal if they share card_id, suit, and rank.
        """
        if not isinstance(other, Card):
            return NotImplemented
        return (
            self._card_id == other._card_id and
            self._suit == other._suit and
            self._rank == other._rank
        )

    def __hash__(self) -> int:
        """Stable hash based on immutable card_id."""
        return hash(self._card_id)

    def __repr__(self) -> str:
        return (
            f"Card(id={self._card_id}, {self._rank.display_str}{self._suit.symbol}, "
            f"face_up={self._is_face_up})"
        )

    def __str__(self) -> str:
        return self.display_name

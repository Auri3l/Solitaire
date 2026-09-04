"""Core Pile and Deck abstractions.

Defines PileType, Pile container, and Deck generation/shuffling.
"""

from enum import Enum, unique
import random
from typing import List, Tuple, Optional, Dict, Any, Iterator, Union

from solitaire.core.card import Card, Suit, Rank


@unique
class PileType(Enum):
    """Defines functional roles for solitaire piles."""
    STOCK = "stock"
    WASTE = "waste"
    FOUNDATION = "foundation"
    TABLEAU = "tableau"
    FREECELL = "freecell"

    def __str__(self) -> str:
        return self.value


class Pile:
    """Manages an ordered sequence of cards representing a board pile.

    Index convention:
        - Index 0: Bottom-most / base card of the pile.
        - Index len-1: Top-most / currently exposed / accessible card.
    """

    def __init__(
        self,
        arg1: Union[str, PileType] = "",
        arg2: Union[str, PileType] = "",
        index: int = 0,
        pile_id: Optional[str] = None,
        pile_type: Optional[PileType] = None,
        cards: Optional[List[Card]] = None,
    ) -> None:
        # Flexible signature supporting Pile(id, type) or Pile(type, id)
        final_id: str = ""
        final_type: PileType = PileType.TABLEAU

        if pile_id is not None:
            final_id = str(pile_id)
        if pile_type is not None:
            final_type = pile_type

        # Parse positional arguments if keywords not explicitly supplied
        if not final_id or pile_type is None:
            for arg in (arg1, arg2):
                if isinstance(arg, PileType):
                    final_type = arg
                elif isinstance(arg, str) and arg:
                    if not final_id:
                        final_id = arg

        self._pile_id: str = final_id
        self._pile_type: PileType = final_type
        self._index: int = index
        self._cards: List[Card] = list(cards) if cards else []

    @property
    def pile_id(self) -> str:
        return self._pile_id

    @property
    def pile_type(self) -> PileType:
        return self._pile_type

    @property
    def index(self) -> int:
        return self._index

    @property
    def cards(self) -> Tuple[Card, ...]:
        """Returns an immutable tuple view of cards in bottom-to-top order."""
        return tuple(self._cards)

    @property
    def is_empty(self) -> bool:
        return len(self._cards) == 0

    @property
    def size(self) -> int:
        return len(self._cards)

    def __len__(self) -> int:
        return len(self._cards)

    def __iter__(self) -> Iterator[Card]:
        return iter(self._cards)

    def __getitem__(self, idx: int) -> Card:
        """Supports indexing (e.g. pile[-1] for top card)."""
        return self._cards[idx]

    def peek(self) -> Optional[Card]:
        """Returns the top card without removing it, or None if empty."""
        if not self._cards:
            return None
        return self._cards[-1]

    def peek_at(self, idx: int) -> Optional[Card]:
        """Returns card at specific index, or None if out of bounds."""
        if 0 <= idx < len(self._cards) or -len(self._cards) <= idx < 0:
            return self._cards[idx]
        return None

    def push(self, card: Card) -> None:
        """Appends a card to the top of the pile."""
        if not isinstance(card, Card):
            raise TypeError(f"Expected Card instance, got {type(card)}")
        self._cards.append(card)

    def push_many(self, cards: List[Card]) -> None:
        """Appends a sequence of cards to the top of the pile in order."""
        for c in cards:
            self.push(c)

    def pop(self) -> Card:
        """Removes and returns the top card. Raises IndexError if empty."""
        if not self._cards:
            raise IndexError(f"Cannot pop from empty pile: {self._pile_id}")
        return self._cards.pop()

    def slice(self, start_idx: int) -> List[Card]:
        """Returns a shallow copy of cards from start_idx to the top.
        Does not modify the pile.
        """
        if start_idx < 0 or start_idx >= len(self._cards):
            raise IndexError(f"Slice index {start_idx} out of range [0, {len(self._cards)})")
        return list(self._cards[start_idx:])

    def remove_from(self, start_idx: int) -> List[Card]:
        """Removes and returns all cards from start_idx up to the top card."""
        if start_idx < 0 or start_idx > len(self._cards):
            raise IndexError(f"Remove index {start_idx} out of range [0, {len(self._cards)}]")
        removed = self._cards[start_idx:]
        self._cards = self._cards[:start_idx]
        return removed

    def remove_card_by_id(self, card_id: int) -> Card:
        """Removes a single card matching card_id from anywhere in the pile."""
        idx = self.find_card_index(card_id)
        if idx is None:
            raise ValueError(f"Card ID {card_id} not found in pile {self._pile_id}")
        return self._cards.pop(idx)

    def find_card_index(self, card_id: int) -> Optional[int]:
        """Returns 0-based index of card matching card_id, or None."""
        for i, card in enumerate(self._cards):
            if card.card_id == card_id:
                return i
        return None

    def contains_card(self, card_id: int) -> bool:
        return self.find_card_index(card_id) is not None

    def clear(self) -> None:
        """Empties all cards from the pile."""
        self._cards.clear()

    @property
    def face_up_count(self) -> int:
        return sum(1 for c in self._cards if c.is_face_up)

    @property
    def face_down_count(self) -> int:
        return sum(1 for c in self._cards if not c.is_face_up)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes pile state."""
        return {
            "pile_id": self._pile_id,
            "pile_type": self._pile_type.value,
            "index": self._index,
            "cards": [c.to_dict() for c in self._cards]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pile":
        """Deserializes pile state."""
        pile = cls(
            pile_id=data["pile_id"],
            pile_type=PileType(data["pile_type"]),
            index=data.get("index", 0)
        )
        for cd in data.get("cards", []):
            pile.push(Card.from_dict(cd))
        return pile

    def __repr__(self) -> str:
        return (
            f"Pile(id={self._pile_id!r}, type={self._pile_type.value}, "
            f"count={len(self._cards)}, top={self.peek()})"
        )


class Deck:
    """Card deck container, generation, and deterministic shuffling."""

    def __init__(self, cards: Optional[List[Card]] = None) -> None:
        self._cards: List[Card] = list(cards) if cards is not None else []

    @property
    def cards(self) -> List[Card]:
        return self._cards

    @property
    def is_empty(self) -> bool:
        return len(self._cards) == 0

    def __len__(self) -> int:
        return len(self._cards)

    def __iter__(self) -> Iterator[Card]:
        return iter(self._cards)

    def __getitem__(self, idx: int) -> Card:
        return self._cards[idx]

    def draw(self) -> Card:
        """Draws the top card from the deck."""
        if not self._cards:
            raise IndexError("Cannot draw from empty deck")
        return self._cards.pop()

    def shuffle(self, seed: Optional[int] = None) -> List[Card]:
        """In-place deterministic shuffle of this deck."""
        rng = random.Random(seed)
        rng.shuffle(self._cards)
        return self._cards

    @classmethod
    def create_standard(cls) -> "Deck":
        """Generates standard 52-card deck wrapped in Deck instance."""
        cards = cls.create_standard_deck()
        return cls(cards)

    @classmethod
    def create_standard_52(cls) -> "Deck":
        """Alias for create_standard()."""
        return cls.create_standard()

    @staticmethod
    def create_standard_deck() -> List[Card]:
        """Generates a standard 52-card deck with deterministic IDs 0..51.
        All cards are initially face-down.

        ID Allocation Scheme:
            card_id = suit_index * 13 + (rank - 1)
            Suit order: SPADES (0..12), HEARTS (13..25), DIAMONDS (26..38), CLUBS (39..51)
        """
        cards: List[Card] = []
        card_id = 0
        for suit in (Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS):
            for rank in Rank:
                cards.append(Card(suit=suit, rank=rank, is_face_up=False, card_id=card_id))
                card_id += 1
        return cards

    @staticmethod
    def create_spider_deck(num_suits: int = 1) -> List[Card]:
        """Generates a 104-card Spider deck with unique IDs 0..103.

        Args:
            num_suits: 1 (104 Spades), 2 (52 Spades + 52 Hearts), or 4 (standard double deck).
        """
        if num_suits not in (1, 2, 4):
            raise ValueError(f"Spider num_suits must be 1, 2, or 4, got {num_suits}")

        suit_dist: List[Suit]
        if num_suits == 1:
            suit_dist = [Suit.SPADES] * 8
        elif num_suits == 2:
            suit_dist = [Suit.SPADES] * 4 + [Suit.HEARTS] * 4
        else:
            suit_dist = [Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS] * 2

        cards: List[Card] = []
        card_id = 0
        for suit in suit_dist:
            for rank in Rank:
                cards.append(Card(suit=suit, rank=rank, is_face_up=False, card_id=card_id))
                card_id += 1
        return cards

    @staticmethod
    def shuffle_cards(cards: List[Card], seed: Optional[int] = None) -> List[Card]:
        """Returns a deterministically shuffled copy of card list."""
        rng = random.Random(seed)
        shuffled = list(cards)
        rng.shuffle(shuffled)
        return shuffled

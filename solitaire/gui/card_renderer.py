"""Procedural vector card renderer for Solitaire Suite.

100% self-contained offline procedural rendering of playing cards, suits,
ranks, court graphics, and ornamental card backs using pygame drawing primitives.
No external asset files, fonts, or network access required.
"""

import math
from typing import Dict, Tuple, Optional
import pygame
from solitaire.core.card import Card, Suit, Rank, Color
from solitaire.core.pile import PileType


class CardRenderer:
    """Renders and caches playing cards and board piles as Pygame surfaces."""

    def __init__(self) -> None:
        self._cache: Dict[Tuple[Optional[Suit], Optional[int], bool, int, int], pygame.Surface] = {}
        self._empty_pile_cache: Dict[Tuple[str, Optional[Suit], int, int], pygame.Surface] = {}
        self._font_cache: Dict[Tuple[str, int, bool], pygame.font.Font] = {}

    def _get_font(self, size: int, bold: bool = True) -> pygame.font.Font:
        key = ("default", size, bold)
        if key not in self._font_cache:
            try:
                self._font_cache[key] = pygame.font.SysFont("segoe ui,arial,helvetica", size, bold=bold)
            except Exception:
                self._font_cache[key] = pygame.font.Font(None, size)
        return self._font_cache[key]

    # -------------------------------------------------------------------------
    # Procedural Suit Drawing Primitives
    # -------------------------------------------------------------------------
    @staticmethod
    def draw_suit_heart(surface: pygame.Surface, color: Tuple[int, int, int], cx: float, cy: float, size: float) -> None:
        """Draws a crisp procedural vector Heart."""
        w = size * 0.9
        h = size * 0.95
        top_y = cy - h * 0.45
        bot_y = cy + h * 0.48
        r = w * 0.26
        left_cx = cx - r * 0.95
        right_cx = cx + r * 0.95
        arc_cy = top_y + r

        # Two circles for lobes
        pygame.draw.circle(surface, color, (int(left_cx), int(arc_cy)), int(r))
        pygame.draw.circle(surface, color, (int(right_cx), int(arc_cy)), int(r))

        # Triangle connecting lobes to bottom apex
        points = [
            (cx - w * 0.48, arc_cy),
            (cx + w * 0.48, arc_cy),
            (cx, bot_y),
        ]
        pygame.draw.polygon(surface, color, points)

    @staticmethod
    def draw_suit_diamond(surface: pygame.Surface, color: Tuple[int, int, int], cx: float, cy: float, size: float) -> None:
        """Draws a crisp procedural vector Diamond."""
        hw = size * 0.42
        hh = size * 0.52
        points = [
            (cx, cy - hh),
            (cx + hw, cy),
            (cx, cy + hh),
            (cx - hw, cy),
        ]
        pygame.draw.polygon(surface, color, points)

    @staticmethod
    def draw_suit_spade(surface: pygame.Surface, color: Tuple[int, int, int], cx: float, cy: float, size: float) -> None:
        """Draws a crisp procedural vector Spade."""
        w = size * 0.9
        h = size * 0.95
        top_y = cy - h * 0.48
        waist_y = cy + h * 0.12
        r = w * 0.25
        left_cx = cx - r * 0.95
        right_cx = cx + r * 0.95
        arc_cy = waist_y - r * 0.2

        # Inverted heart body (top point + 2 lobes)
        points = [
            (cx, top_y),
            (cx - w * 0.48, arc_cy),
            (cx + w * 0.48, arc_cy),
        ]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.circle(surface, color, (int(left_cx), int(arc_cy)), int(r))
        pygame.draw.circle(surface, color, (int(right_cx), int(arc_cy)), int(r))

        # Spade stem at bottom
        stem_points = [
            (cx, cy),
            (cx - w * 0.28, cy + h * 0.46),
            (cx + w * 0.28, cy + h * 0.46),
        ]
        pygame.draw.polygon(surface, color, stem_points)

    @staticmethod
    def draw_suit_club(surface: pygame.Surface, color: Tuple[int, int, int], cx: float, cy: float, size: float) -> None:
        """Draws a crisp procedural vector Club."""
        w = size * 0.9
        h = size * 0.95
        r = size * 0.23
        top_cy = cy - h * 0.22
        left_cx = cx - w * 0.23
        right_cx = cx + w * 0.23
        bot_cy = cy + h * 0.08

        # Three circular lobes
        pygame.draw.circle(surface, color, (int(cx), int(top_cy)), int(r))
        pygame.draw.circle(surface, color, (int(left_cx), int(bot_cy)), int(r))
        pygame.draw.circle(surface, color, (int(right_cx), int(bot_cy)), int(r))

        # Central filler
        pygame.draw.circle(surface, color, (int(cx), int(cy - h * 0.05)), int(r * 0.9))

        # Stem at bottom
        stem_points = [
            (cx, cy),
            (cx - w * 0.24, cy + h * 0.46),
            (cx + w * 0.24, cy + h * 0.46),
        ]
        pygame.draw.polygon(surface, color, stem_points)

    def draw_suit(self, surface: pygame.Surface, suit: Suit, cx: float, cy: float, size: float, color: Optional[Tuple[int, int, int]] = None) -> None:
        """Draws any of the four suits dynamically centered at (cx, cy)."""
        if color is None:
            color = (215, 25, 25) if suit.is_red else (25, 25, 25)

        if suit == Suit.HEARTS:
            self.draw_suit_heart(surface, color, cx, cy, size)
        elif suit == Suit.DIAMONDS:
            self.draw_suit_diamond(surface, color, cx, cy, size)
        elif suit == Suit.SPADES:
            self.draw_suit_spade(surface, color, cx, cy, size)
        elif suit == Suit.CLUBS:
            self.draw_suit_club(surface, color, cx, cy, size)

    # -------------------------------------------------------------------------
    # Card Surface Rendering
    # -------------------------------------------------------------------------
    def get_card_surface(self, card: Card, width: int, height: int) -> pygame.Surface:
        """Returns a cached surface for the specified card face or back."""
        key = (card.suit, card.rank.value if card.face_up else None, card.face_up, width, height)
        if key in self._cache:
            return self._cache[key]

        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        corner_radius = max(6, int(width * 0.08))

        if not card.face_up:
            self._render_card_back(surf, width, height, corner_radius)
        else:
            self._render_card_face(surf, card, width, height, corner_radius)

        self._cache[key] = surf
        return surf

    def get_card_back_surface(self, width: int, height: int) -> pygame.Surface:
        """Convenience method for card back."""
        key = (None, None, False, width, height)
        if key in self._cache:
            return self._cache[key]
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        self._render_card_back(surf, width, height, max(6, int(width * 0.08)))
        self._cache[key] = surf
        return surf

    def _render_card_back(self, surface: pygame.Surface, width: int, height: int, radius: int) -> None:
        # Subtle drop shadow
        shadow_rect = pygame.Rect(2, 2, width - 2, height - 2)
        pygame.draw.rect(surface, (0, 0, 0, 45), shadow_rect, border_radius=radius)

        # Base card white border
        card_rect = pygame.Rect(0, 0, width - 2, height - 2)
        pygame.draw.rect(surface, (255, 255, 255), card_rect, border_radius=radius)
        pygame.draw.rect(surface, (190, 195, 205), card_rect, width=1, border_radius=radius)

        # Navy blue inner ornamental pattern
        margin = max(4, int(width * 0.06))
        inner_rect = pygame.Rect(margin, margin, width - 2 - 2 * margin, height - 2 - 2 * margin)
        pygame.draw.rect(surface, (28, 48, 105), inner_rect, border_radius=max(3, radius - 2))

        # Diamond lattice or geometric pattern
        grid_step = max(8, int(width * 0.12))
        inner_sub = surface.subsurface(inner_rect)
        iw, ih = inner_rect.width, inner_rect.height
        line_color = (48, 75, 145)
        for x in range(-ih, iw + ih, grid_step):
            pygame.draw.line(inner_sub, line_color, (x, 0), (x + ih, ih), 1)
            pygame.draw.line(inner_sub, line_color, (x, ih), (x + ih, 0), 1)

        # Center crest / medallion
        mcx, mcy = iw // 2, ih // 2
        medallion_r = max(10, int(width * 0.18))
        pygame.draw.circle(inner_sub, (28, 48, 105), (mcx, mcy), medallion_r)
        pygame.draw.circle(inner_sub, (212, 175, 55), (mcx, mcy), medallion_r, width=2)
        # Mini golden star in center
        pygame.draw.circle(inner_sub, (245, 215, 110), (mcx, mcy), max(3, medallion_r // 3))

    def _render_card_face(self, surface: pygame.Surface, card: Card, width: int, height: int, radius: int) -> None:
        # Shadow
        shadow_rect = pygame.Rect(2, 2, width - 2, height - 2)
        pygame.draw.rect(surface, (0, 0, 0, 45), shadow_rect, border_radius=radius)

        # Card body (crisp ivory/off-white)
        card_rect = pygame.Rect(0, 0, width - 2, height - 2)
        pygame.draw.rect(surface, (253, 253, 252), card_rect, border_radius=radius)
        pygame.draw.rect(surface, (185, 185, 190), card_rect, width=1, border_radius=radius)

        suit_color = (215, 25, 25) if card.suit.is_red else (25, 28, 32)
        rank_str = card.rank.display_str

        # Fonts
        font_size = max(14, int(width * 0.22))
        font = self._get_font(font_size, bold=True)
        text_surf = font.render(rank_str, True, suit_color)
        tw, th = text_surf.get_size()

        # Corner margins
        pad_x = max(4, int(width * 0.08))
        pad_y = max(3, int(height * 0.04))
        mini_suit_size = max(8, int(width * 0.14))

        # Top-Left Rank & Suit
        surface.blit(text_surf, (pad_x, pad_y))
        self.draw_suit(surface, card.suit, pad_x + tw / 2, pad_y + th + mini_suit_size * 0.55, mini_suit_size, suit_color)

        # Bottom-Right Rank & Suit (inverted)
        br_x = (width - 2) - pad_x - tw
        br_y = (height - 2) - pad_y - th
        surface.blit(text_surf, (br_x, br_y))
        self.draw_suit(surface, card.suit, br_x + tw / 2, br_y - mini_suit_size * 0.55, mini_suit_size, suit_color)

        # Center Graphic
        cx = (width - 2) / 2
        cy = (height - 2) / 2

        if card.rank == Rank.ACE:
            # Grand ornate center emblem
            large_size = width * 0.44
            self.draw_suit(surface, card.suit, cx, cy, large_size, suit_color)
        elif card.rank.is_face_card:
            # Heraldic frame for court cards
            self._render_court_graphic(surface, card, cx, cy, width, height, suit_color)
        else:
            # Numbered card center display
            center_size = width * 0.32
            self.draw_suit(surface, card.suit, cx, cy, center_size, suit_color)

    def _render_court_graphic(self, surface: pygame.Surface, card: Card, cx: float, cy: float, width: int, height: int, color: Tuple[int, int, int]) -> None:
        """Renders an elegant court card center badge (J, Q, K)."""
        box_w = width * 0.55
        box_h = height * 0.48
        box_rect = pygame.Rect(int(cx - box_w / 2), int(cy - box_h / 2), int(box_w), int(box_h))

        # Ornate frame
        pygame.draw.rect(surface, (245, 243, 238), box_rect, border_radius=4)
        border_gold = (200, 160, 50) if card.suit.is_red else (150, 150, 160)
        pygame.draw.rect(surface, border_gold, box_rect, width=1, border_radius=4)

        # Center letter with subtle gold glow
        letter = card.rank.display_str
        font_size = max(20, int(box_h * 0.6))
        court_font = self._get_font(font_size, bold=True)
        letter_surf = court_font.render(letter, True, color)
        lw, lh = letter_surf.get_size()
        surface.blit(letter_surf, (cx - lw / 2, cy - lh / 2))

        # Small accent suits above & below the letter inside the court box
        accent_size = max(8, int(width * 0.12))
        self.draw_suit(surface, card.suit, cx, cy - box_h * 0.33, accent_size, color)
        self.draw_suit(surface, card.suit, cx, cy + box_h * 0.33, accent_size, color)

    # -------------------------------------------------------------------------
    # Empty Pile Slots & Overlays
    # -------------------------------------------------------------------------
    def get_empty_pile_surface(self, pile_type: str, suit: Optional[Suit], width: int, height: int) -> pygame.Surface:
        """Returns a cached placeholder outline for an empty board pile."""
        key = (pile_type, suit, width, height)
        if key in self._empty_pile_cache:
            return self._empty_pile_cache[key]

        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        radius = max(6, int(width * 0.08))
        rect = pygame.Rect(0, 0, width - 2, height - 2)

        # Translucent dark slot background
        pygame.draw.rect(surf, (0, 0, 0, 35), rect, border_radius=radius)
        # Dotted / dashed white border effect
        pygame.draw.rect(surf, (255, 255, 255, 75), rect, width=2, border_radius=radius)

        cx = (width - 2) / 2
        cy = (height - 2) / 2

        if pile_type == "foundation":
            if suit:
                # Faint watermark suit
                watermark_color = (255, 255, 255, 60)
                self.draw_suit(surf, suit, cx, cy, width * 0.38, watermark_color)
            else:
                # 'A' letter for foundation
                font = self._get_font(max(16, int(width * 0.3)), bold=True)
                txt = font.render("A", True, (255, 255, 255, 65))
                surf.blit(txt, (cx - txt.get_width() / 2, cy - txt.get_height() / 2))
        elif pile_type in ("freecell", "cell"):
            font = self._get_font(max(12, int(width * 0.18)), bold=True)
            txt = font.render("FREE", True, (255, 255, 255, 60))
            surf.blit(txt, (cx - txt.get_width() / 2, cy - txt.get_height() / 2))
        elif pile_type == "stock":
            # Refresh / reload icon circular arrows
            icon_r = max(10, int(width * 0.2))
            pygame.draw.circle(surf, (255, 255, 255, 65), (int(cx), int(cy)), icon_r, width=2)
            pygame.draw.polygon(surf, (255, 255, 255, 65), [
                (cx + icon_r, cy - 4),
                (cx + icon_r + 6, cy + 4),
                (cx + icon_r - 6, cy + 4),
            ])

        self._empty_pile_cache[key] = surf
        return surf

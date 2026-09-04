"""Win celebration animation and victory modal for Solitaire Suite.

Features the iconic Windows Solitaire ballistic bouncing card cascade effect
along with a polished victory modal displaying score, elapsed time, and moves.
"""

import math
import random
import time
from typing import List, Tuple, Optional
import pygame
from solitaire.core.card import Card, Suit, Rank
from solitaire.gui.card_renderer import CardRenderer


class BouncingCard:
    """Simulates a single physics card bouncing off walls and floor."""

    def __init__(self, card: Card, x: float, y: float, vx: float, vy: float, card_w: int, card_h: int) -> None:
        self.card: Card = card
        self.x: float = x
        self.y: float = y
        self.vx: float = vx
        self.vy: float = vy
        self.card_w: int = card_w
        self.card_h: int = card_h
        self.gravity: float = 0.55
        self.bounce_restitution: float = -0.82
        self.is_active: bool = True

    def update(self, screen_w: int, screen_h: int) -> None:
        if not self.is_active:
            return

        self.vy += self.gravity
        self.x += self.vx
        self.y += self.vy

        # Floor bounce
        floor_y = screen_h - self.card_h
        if self.y >= floor_y:
            self.y = floor_y
            self.vy *= self.bounce_restitution
            # Add slight random perturbation to bounce
            self.vx += random.uniform(-0.3, 0.3)

        # Left / Right boundaries
        if self.x < -self.card_w or self.x > screen_w:
            self.is_active = False


class CelebrationController:
    """Manages the victory cascade animation and summary modal."""

    def __init__(self) -> None:
        self.is_active: bool = False
        self.cascade_surface: Optional[pygame.Surface] = None
        self.bouncing_cards: List[BouncingCard] = []
        self.deck_cards: List[Card] = []
        self.card_index: int = 0
        self.spawn_timer: float = 0.0
        self.spawn_interval: float = 0.15
        self.start_time: float = 0.0
        self.font_title: Optional[pygame.font.Font] = None
        self.font_body: Optional[pygame.font.Font] = None

    def start(self, foundation_cards: List[Card], screen_w: int, screen_h: int, card_w: int, card_h: int) -> None:
        """Initializes the celebration cascade."""
        self.is_active = True
        self.start_time = time.time()
        self.cascade_surface = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        self.bouncing_cards.clear()
        self.card_index = 0
        self.spawn_timer = 0.0

        # If foundation cards provided, use them; otherwise create a 52 card deck
        if foundation_cards:
            self.deck_cards = list(reversed(foundation_cards))
        else:
            self.deck_cards = [
                Card(suit, rank, face_up=True)
                for suit in Suit
                for rank in range(13, 0, -1)
            ]

        try:
            self.font_title = pygame.font.SysFont("segoe ui,arial", 36, bold=True)
            self.font_body = pygame.font.SysFont("segoe ui,arial", 20, bold=False)
        except Exception:
            self.font_title = pygame.font.Font(None, 40)
            self.font_body = pygame.font.Font(None, 24)

    def stop(self) -> None:
        self.is_active = False
        self.cascade_surface = None
        self.bouncing_cards.clear()

    def update(self, dt: float, screen_w: int, screen_h: int, card_w: int, card_h: int) -> None:
        if not self.is_active:
            return

        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval and self.card_index < len(self.deck_cards):
            self.spawn_timer = 0.0
            card = self.deck_cards[self.card_index]
            self.card_index += 1

            # Start from top area
            start_x = screen_w * 0.5 + random.uniform(-screen_w * 0.3, screen_w * 0.3)
            start_y = random.uniform(60, 120)
            vx = random.choice([-1, 1]) * random.uniform(3.0, 7.5)
            vy = random.uniform(-4.0, -0.5)

            bc = BouncingCard(card, start_x, start_y, vx, vy, card_w, card_h)
            self.bouncing_cards.append(bc)

        # Update physics
        for bc in self.bouncing_cards:
            bc.update(screen_w, screen_h)

        # Remove cards that have fallen off screen
        self.bouncing_cards = [bc for bc in self.bouncing_cards if bc.is_active]

    def draw(
        self,
        surface: pygame.Surface,
        renderer: CardRenderer,
        screen_w: int,
        screen_h: int,
        card_w: int,
        card_h: int,
        final_score: int,
        elapsed_seconds: int,
        moves_count: int,
    ) -> None:
        if not self.is_active:
            return

        # Stamp current positions onto persistent cascade surface (iconic Solitaire smear)
        if self.cascade_surface:
            for bc in self.bouncing_cards:
                csurf = renderer.get_card_surface(bc.card, card_w, card_h)
                self.cascade_surface.blit(csurf, (int(bc.x), int(bc.y)))
            surface.blit(self.cascade_surface, (0, 0))

        # Render active cards with elevation
        for bc in self.bouncing_cards:
            csurf = renderer.get_card_surface(bc.card, card_w, card_h)
            surface.blit(csurf, (int(bc.x), int(bc.y)))

        # After 3 seconds of cascade, display victory dialog
        if time.time() - self.start_time > 2.5:
            self._draw_modal(surface, screen_w, screen_h, final_score, elapsed_seconds, moves_count)

    def _draw_modal(
        self,
        surface: pygame.Surface,
        screen_w: int,
        screen_h: int,
        final_score: int,
        elapsed_seconds: int,
        moves_count: int,
    ) -> None:
        modal_w = 420
        modal_h = 270
        mx = (screen_w - modal_w) // 2
        my = (screen_h - modal_h) // 2

        # Dim overlay
        dim_surf = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        pygame.draw.rect(dim_surf, (0, 0, 0, 110), (0, 0, screen_w, screen_h))
        surface.blit(dim_surf, (0, 0))

        # Modal body
        modal_rect = pygame.Rect(mx, my, modal_w, modal_h)
        pygame.draw.rect(surface, (26, 32, 44), modal_rect, border_radius=12)
        pygame.draw.rect(surface, (212, 175, 55), modal_rect, width=2, border_radius=12)

        # Title
        if self.font_title:
            title_surf = self.font_title.render("VICTORY!", True, (255, 215, 0))
            surface.blit(title_surf, (mx + (modal_w - title_surf.get_width()) // 2, my + 24))

        # Stats
        if self.font_body:
            mins = elapsed_seconds // 60
            secs = elapsed_seconds % 60
            time_str = f"{mins:02d}:{secs:02d}"

            lines = [
                f"Score: {final_score:,}",
                f"Moves: {moves_count}",
                f"Time: {time_str}",
            ]
            for i, line in enumerate(lines):
                line_surf = self.font_body.render(line, True, (220, 225, 235))
                surface.blit(line_surf, (mx + (modal_w - line_surf.get_width()) // 2, my + 85 + i * 28))

            # Prompt
            hint_font = pygame.font.Font(None, 20)
            hint_txt = hint_font.render("Press 'N' for New Game or click New Game on toolbar", True, (160, 174, 192))
            surface.blit(hint_txt, (mx + (modal_w - hint_txt.get_width()) // 2, my + 215))

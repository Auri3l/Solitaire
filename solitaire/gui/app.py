"""Main Pygame desktop application for Solitaire Suite.

Orchestrates window initialization, event handling, HUD toolbar, game mode
switching across Klondike (Turn 1 & 3), FreeCell, and Spider (1, 2, 4 suits),
live rendering loop, and win celebration.
"""

import ctypes
import os
import sys
import time
from typing import Optional, Dict, Tuple, List, Any
import pygame

from solitaire.core.base_game import BaseGame, GameStatus, MoveResult
from solitaire.core.card import Card, Suit, Rank
from solitaire.games.klondike import KlondikeGame
from solitaire.games.freecell import FreeCellGame
from solitaire.games.spider import SpiderGame
from solitaire.ai.hint_engine import HintEngine, Hint
from solitaire.ai.auto_finish import AutoFinishController
from solitaire.gui.card_renderer import CardRenderer
from solitaire.gui.layout import LayoutManager
from solitaire.gui.interaction import InteractionController
from solitaire.gui.celebration import CelebrationController


class Button:
    """Lightweight UI button for the HUD toolbar."""

    def __init__(self, key: str, label: str, rect: pygame.Rect) -> None:
        self.key: str = key
        self.label: str = label
        self.rect: pygame.Rect = rect
        self.enabled: bool = True
        self.hovered: bool = False

    def check_hover(self, pos: Tuple[int, int]) -> None:
        self.hovered = self.enabled and self.rect.collidepoint(pos)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, active: bool = False) -> None:
        if not self.enabled:
            bg_color = (38, 44, 56)
            text_color = (100, 110, 125)
            border_color = (50, 58, 72)
        elif active:
            bg_color = (40, 100, 180)
            text_color = (255, 255, 255)
            border_color = (80, 150, 240)
        elif self.hovered:
            bg_color = (55, 65, 82)
            text_color = (255, 255, 255)
            border_color = (90, 105, 130)
        else:
            bg_color = (36, 42, 54)
            text_color = (215, 220, 230)
            border_color = (65, 75, 95)

        pygame.draw.rect(surface, bg_color, self.rect, border_radius=6)
        pygame.draw.rect(surface, border_color, self.rect, width=1, border_radius=6)

        txt_surf = font.render(self.label, True, text_color)
        tx = self.rect.x + (self.rect.width - txt_surf.get_width()) // 2
        ty = self.rect.y + (self.rect.height - txt_surf.get_height()) // 2
        surface.blit(txt_surf, (tx, ty))


class SolitaireApp:
    """Desktop Solitaire Suite application."""

    MODES: Dict[str, str] = {
        "klondike1": "Klondike (Turn 1)",
        "klondike3": "Klondike (Turn 3)",
        "freecell": "FreeCell",
        "spider1": "Spider (1 Suit)",
        "spider2": "Spider (2 Suits)",
        "spider4": "Spider (4 Suits)",
    }

    def __init__(self, mode: str = "klondike1", seed: Optional[int] = None, headless: bool = False) -> None:
        self.headless: bool = headless
        self.current_mode_key: str = mode if mode in self.MODES else "klondike1"
        self.seed: Optional[int] = seed

        # Enable High-DPI Windows scaling
        if not self.headless and sys.platform == "win32":
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                pass

        if self.headless:
            os.environ["SDL_VIDEODRIVER"] = "dummy"

        pygame.init()
        pygame.font.init()

        self.screen_width: int = 1200
        self.screen_height: int = 800
        self.toolbar_height: int = 56

        if not self.headless:
            self.screen = pygame.display.set_mode(
                (self.screen_width, self.screen_height),
                pygame.RESIZABLE | pygame.DOUBLEBUF
            )
            pygame.display.set_caption("Solitaire Suite — Offline Desktop Edition")
        else:
            self.screen = pygame.Surface((self.screen_width, self.screen_height))

        self.clock = pygame.time.Clock()
        self.running: bool = True

        # Systems
        self.renderer = CardRenderer()
        self.layout = LayoutManager()
        self.interaction = InteractionController()
        self.celebration = CelebrationController()

        # UI fonts
        try:
            self.font_toolbar = pygame.font.SysFont("segoe ui,arial", 13, bold=True)
            self.font_status = pygame.font.SysFont("segoe ui,arial", 14, bold=False)
            self.font_stat = pygame.font.SysFont("segoe ui,arial", 14, bold=True)
        except Exception:
            self.font_toolbar = pygame.font.Font(None, 18)
            self.font_status = pygame.font.Font(None, 20)
            self.font_stat = pygame.font.Font(None, 20)

        # Status notification banner
        self.status_message: str = "Welcome to Solitaire Suite!"
        self.status_time: float = time.time()
        self.status_duration: float = 4.0

        # Mode dropdown menu state
        self.mode_menu_open: bool = False
        self.mode_menu_rects: Dict[str, pygame.Rect] = {}

        # Buttons
        self.buttons: Dict[str, Button] = {}
        self._init_buttons()

        # Active Game State
        self.game: BaseGame = self._create_game(self.current_mode_key, self.seed)
        self.game.start_new_game(seed=self.seed)
        self.layout.update_layout(self.game, self.screen_width, self.screen_height, self.toolbar_height)

        # Win check tracker
        self.has_celebrated: bool = False

    def _create_game(self, mode_key: str, seed: Optional[int] = None) -> BaseGame:
        if mode_key == "klondike1":
            return KlondikeGame(turn_mode=1, seed=seed)
        elif mode_key == "klondike3":
            return KlondikeGame(turn_mode=3, seed=seed)
        elif mode_key == "freecell":
            return FreeCellGame(seed=seed)
        elif mode_key == "spider1":
            return SpiderGame(num_suits=1, seed=seed)
        elif mode_key == "spider2":
            return SpiderGame(num_suits=2, seed=seed)
        elif mode_key == "spider4":
            return SpiderGame(num_suits=4, seed=seed)
        return KlondikeGame(turn_mode=1, seed=seed)

    def _init_buttons(self) -> None:
        self.buttons.clear()
        btn_h = 32
        by = (self.toolbar_height - btn_h) // 2

        # 1. Mode dropdown button
        self.buttons["mode"] = Button("mode", f"Mode: {self.MODES[self.current_mode_key]} ▾", pygame.Rect(14, by, 180, btn_h))

        # 2. Controls
        bx = 202
        self.buttons["new"] = Button("new", "New Game", pygame.Rect(bx, by, 84, btn_h))
        bx += 90
        self.buttons["restart"] = Button("restart", "Restart", pygame.Rect(bx, by, 72, btn_h))
        bx += 78
        self.buttons["undo"] = Button("undo", "Undo (Z)", pygame.Rect(bx, by, 76, btn_h))
        bx += 82
        self.buttons["redo"] = Button("redo", "Redo (Y)", pygame.Rect(bx, by, 76, btn_h))
        bx += 82
        self.buttons["hint"] = Button("hint", "Hint (H)", pygame.Rect(bx, by, 72, btn_h))
        bx += 78
        self.buttons["auto"] = Button("auto", "Auto-Finish", pygame.Rect(bx, by, 94, btn_h))

    def switch_mode(self, mode_key: str, seed: Optional[int] = None) -> None:
        """Switches game mode and starts a fresh match."""
        if mode_key not in self.MODES:
            return
        self.current_mode_key = mode_key
        self.buttons["mode"].label = f"Mode: {self.MODES[mode_key]} ▾"
        self.game = self._create_game(mode_key, seed)
        self.game.start_new_game(seed=seed)
        self.layout.update_layout(self.game, self.screen_width, self.screen_height, self.toolbar_height)
        self.interaction.clear_hint()
        self.celebration.stop()
        self.has_celebrated = False
        self.set_status(f"Started new {self.MODES[mode_key]} game.")

    def set_status(self, msg: str, duration: float = 4.0) -> None:
        self.status_message = msg
        self.status_time = time.time()
        self.status_duration = duration

    # -------------------------------------------------------------------------
    # Main Event Loop
    # -------------------------------------------------------------------------
    def run(self) -> None:
        """Starts the interactive desktop application loop."""
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self._handle_events()
            self._update(dt)
            self._draw()
            if not self.headless:
                pygame.display.flip()

        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            elif event.type == pygame.VIDEORESIZE and not self.headless:
                self.screen_width = max(640, event.w)
                self.screen_height = max(480, event.h)
                self.screen = pygame.display.set_mode(
                    (self.screen_width, self.screen_height),
                    pygame.RESIZABLE | pygame.DOUBLEBUF
                )
                self.layout.update_layout(self.game, self.screen_width, self.screen_height, self.toolbar_height)
                self._init_buttons()

            elif event.type == pygame.MOUSEMOTION:
                pos = event.pos
                for btn in self.buttons.values():
                    btn.check_hover(pos)
                if not self.mode_menu_open and not self.celebration.is_active:
                    self.interaction.handle_mouse_motion(pos, self.game, self.layout)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                # Handle mode dropdown menu click if open
                if self.mode_menu_open:
                    clicked_item = False
                    for key, r in self.mode_menu_rects.items():
                        if r.collidepoint(pos):
                            self.switch_mode(key)
                            clicked_item = True
                            break
                    self.mode_menu_open = False
                    if clicked_item:
                        continue

                # Check toolbar buttons
                if pos[1] <= self.toolbar_height:
                    self._handle_toolbar_click(pos)
                    continue

                # If celebration is active, click anywhere dismisses it
                if self.celebration.is_active:
                    self.switch_mode(self.current_mode_key)
                    continue

                # Board interaction
                res = self.interaction.handle_mouse_down(pos, self.game, self.layout)
                if res and not res.success and res.error_message:
                    self.set_status(res.error_message)

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if not self.mode_menu_open and not self.celebration.is_active:
                    res = self.interaction.handle_mouse_up(event.pos, self.game, self.layout)
                    if res:
                        if not res.success and res.error_message:
                            self.set_status(res.error_message)
                        elif res.success:
                            self.layout.update_layout(self.game, self.screen_width, self.screen_height, self.toolbar_height)

            elif event.type == pygame.KEYDOWN:
                self._handle_key_down(event)

    def _handle_toolbar_click(self, pos: Tuple[int, int]) -> None:
        if self.buttons["mode"].rect.collidepoint(pos):
            self.mode_menu_open = not self.mode_menu_open
            return

        self.mode_menu_open = False

        if self.buttons["new"].rect.collidepoint(pos):
            self.switch_mode(self.current_mode_key)
        elif self.buttons["restart"].rect.collidepoint(pos):
            self.game.restart()
            self.layout.update_layout(self.game, self.screen_width, self.screen_height, self.toolbar_height)
            self.interaction.clear_hint()
            self.celebration.stop()
            self.has_celebrated = False
            self.set_status("Restarted current deal.")
        elif self.buttons["undo"].rect.collidepoint(pos) and self.buttons["undo"].enabled:
            self._do_undo()
        elif self.buttons["redo"].rect.collidepoint(pos) and self.buttons["redo"].enabled:
            self._do_redo()
        elif self.buttons["hint"].rect.collidepoint(pos):
            self._do_hint()
        elif self.buttons["auto"].rect.collidepoint(pos) and self.buttons["auto"].enabled:
            self._do_auto_finish()

    def _handle_key_down(self, event: pygame.event.Event) -> None:
        ctrl = (event.mod & pygame.KMOD_CTRL) != 0

        if event.key == pygame.K_z and (ctrl or not event.mod):
            self._do_undo()
        elif event.key == pygame.K_y and (ctrl or not event.mod):
            self._do_redo()
        elif event.key == pygame.K_h:
            self._do_hint()
        elif event.key == pygame.K_n:
            self.switch_mode(self.current_mode_key)
        elif event.key == pygame.K_r:
            self.game.restart()
            self.layout.update_layout(self.game, self.screen_width, self.screen_height, self.toolbar_height)
            self.set_status("Restarted current deal.")
        elif event.key == pygame.K_f:
            self._do_auto_finish()
        elif event.key == pygame.K_ESCAPE:
            self.mode_menu_open = False
            self.interaction.clear_hint()
        elif event.key == pygame.K_1:
            self.switch_mode("klondike1")
        elif event.key == pygame.K_2:
            self.switch_mode("klondike3")
        elif event.key == pygame.K_3:
            self.switch_mode("freecell")
        elif event.key == pygame.K_4:
            self.switch_mode("spider1")
        elif event.key == pygame.K_5:
            self.switch_mode("spider2")
        elif event.key == pygame.K_6:
            self.switch_mode("spider4")

    def _do_undo(self) -> None:
        if self.game.can_undo():
            self.game.undo()
            self.layout.update_layout(self.game, self.screen_width, self.screen_height, self.toolbar_height)
            self.interaction.clear_hint()
            self.set_status("Undid last move.")

    def _do_redo(self) -> None:
        if self.game.can_redo():
            self.game.redo()
            self.layout.update_layout(self.game, self.screen_width, self.screen_height, self.toolbar_height)
            self.interaction.clear_hint()
            self.set_status("Redid move.")

    def _do_hint(self) -> None:
        hint = HintEngine.get_hint(self.game)
        if hint:
            self.interaction.set_hint(hint.move)
            self.set_status(f"Hint: {hint.description}", duration=7.0)
        else:
            self.interaction.clear_hint()
            self.set_status("No legal moves available.", duration=3.0)

    def _do_auto_finish(self) -> None:
        if self.game.can_auto_finish():
            steps, won = AutoFinishController.run_to_completion(self.game)
            self.layout.update_layout(self.game, self.screen_width, self.screen_height, self.toolbar_height)
            self.set_status(f"Auto-finish executed {steps} moves.")

    # -------------------------------------------------------------------------
    # Updates & State
    # -------------------------------------------------------------------------
    def _update(self, dt: float) -> None:
        # Update button enabled states
        self.buttons["undo"].enabled = self.game.can_undo()
        self.buttons["redo"].enabled = self.game.can_redo()
        self.buttons["auto"].enabled = self.game.can_auto_finish()

        # Check for victory
        if self.game.is_won() and not self.has_celebrated:
            self.has_celebrated = True
            # Gather foundation cards
            foundation_cards: List[Card] = []
            for pid, p in self.game.piles.items():
                if pid.startswith("foundation") and p.cards:
                    foundation_cards.extend(p.cards)
            self.celebration.start(
                foundation_cards=foundation_cards,
                screen_w=self.screen_width,
                screen_h=self.screen_height,
                card_w=self.layout.card_width,
                card_h=self.layout.card_height,
            )
            self.set_status("Congratulations! You won!")

        # Update celebration physics
        if self.celebration.is_active:
            self.celebration.update(
                dt, self.screen_width, self.screen_height, self.layout.card_width, self.layout.card_height
            )

    # -------------------------------------------------------------------------
    # Rendering
    # -------------------------------------------------------------------------
    def _draw(self) -> None:
        # Casino green felt background
        self.screen.fill((19, 78, 42))

        # Subtle felt gradient / border
        pygame.draw.rect(self.screen, (14, 60, 32), (0, 0, self.screen_width, self.screen_height), width=4)

        # Draw empty pile placeholders
        self._draw_empty_piles()

        # Draw resting cards
        self._draw_cards()

        # Draw highlights (hints, hover)
        self.interaction.draw_highlights(self.screen, self.layout, self.game)

        # Draw dragging cards
        self.interaction.draw_drag(self.screen, self.renderer, self.layout)

        # Draw win celebration if active
        if self.celebration.is_active:
            elapsed_sec = int(time.time() - self.game.start_time)
            self.celebration.draw(
                self.screen,
                self.renderer,
                self.screen_width,
                self.screen_height,
                self.layout.card_width,
                self.layout.card_height,
                self.game.score,
                elapsed_sec,
                self.game.moves_count,
            )

        # Draw Top HUD Toolbar
        self._draw_toolbar()

        # Draw status message toast if active
        self._draw_status_toast()

        # Draw mode menu dropdown if open
        if self.mode_menu_open:
            self._draw_mode_menu()

    def _draw_empty_piles(self) -> None:
        w, h = self.layout.card_width, self.layout.card_height
        for pile_id, rect in self.layout.pile_rects.items():
            pile = self.game.get_pile(pile_id)
            if pile and len(pile.cards) > 0 and not (pile_id.startswith("tableau") or pile_id.startswith("cascade")):
                continue  # Slot is covered

            # Deduce pile type and suit for watermark
            suit: Optional[Suit] = None
            pile_type = "tableau"
            if pile_id.startswith("foundation"):
                pile_type = "foundation"
                idx = pile_id.split("_")[-1]
                if idx.isdigit() and int(idx) < 4:
                    suit = list(Suit)[int(idx)]
            elif pile_id.startswith("freecell") or pile_id.startswith("cell"):
                pile_type = "freecell"
            elif pile_id == "stock":
                pile_type = "stock"

            surf = self.renderer.get_empty_pile_surface(pile_type, suit, w, h)
            self.screen.blit(surf, (rect.x, rect.y))

    def _draw_cards(self) -> None:
        w, h = self.layout.card_width, self.layout.card_height
        drag_cards = self.interaction.drag_ctx.cards if self.interaction.drag_ctx else []
        drag_src = self.interaction.drag_ctx.source_pile_id if self.interaction.drag_ctx else None
        drag_idx = self.interaction.drag_ctx.source_card_index if self.interaction.drag_ctx else -1

        for (pile_id, card_idx), rect in self.layout.card_rects.items():
            pile = self.game.get_pile(pile_id)
            if not pile or card_idx >= len(pile.cards):
                continue

            # Don't draw cards that are currently being dragged
            if pile_id == drag_src and card_idx >= drag_idx:
                continue

            card = pile.cards[card_idx]
            surf = self.renderer.get_card_surface(card, w, h)
            self.screen.blit(surf, (rect.x, rect.y))

    def _draw_toolbar(self) -> None:
        # Toolbar background
        tb_rect = pygame.Rect(0, 0, self.screen_width, self.toolbar_height)
        pygame.draw.rect(self.screen, (22, 28, 38), tb_rect)
        pygame.draw.line(self.screen, (42, 50, 68), (0, self.toolbar_height - 1), (self.screen_width, self.toolbar_height - 1), 1)

        # Buttons
        for btn in self.buttons.values():
            is_active = (btn.key == "mode" and self.mode_menu_open)
            btn.draw(self.screen, self.font_toolbar, active=is_active)

        # Right-side HUD stats: Score, Moves, Timer
        now = time.time()
        elapsed = int(now - self.game.start_time) if self.game.game_status == GameStatus.IN_PROGRESS else int(self.game.elapsed_time)
        mins = elapsed // 60
        secs = elapsed % 60
        time_text = f"{mins:02d}:{secs:02d}"

        stats_str = f"Score: {self.game.score}   |   Moves: {self.game.moves_count}   |   Time: {time_text}"
        stats_surf = self.font_stat.render(stats_str, True, (215, 225, 240))
        sx = self.screen_width - stats_surf.get_width() - 20
        sy = (self.toolbar_height - stats_surf.get_height()) // 2
        self.screen.blit(stats_surf, (sx, sy))

    def _draw_status_toast(self) -> None:
        now = time.time()
        age = now - self.status_time
        if age >= self.status_duration:
            return

        alpha = 255
        if age > self.status_duration - 0.8:
            alpha = int(255 * (self.status_duration - age) / 0.8)

        txt_surf = self.font_status.render(self.status_message, True, (245, 248, 255))
        pad_x = 18
        pad_y = 7
        toast_w = txt_surf.get_width() + 2 * pad_x
        toast_h = txt_surf.get_height() + 2 * pad_y
        tx = (self.screen_width - toast_w) // 2
        ty = self.toolbar_height + 8

        toast_surf = pygame.Surface((toast_w, toast_h), pygame.SRCALPHA)
        pygame.draw.rect(toast_surf, (20, 24, 33, min(230, alpha)), (0, 0, toast_w, toast_h), border_radius=8)
        pygame.draw.rect(toast_surf, (80, 120, 180, alpha), (0, 0, toast_w, toast_h), width=1, border_radius=8)
        toast_surf.blit(txt_surf, (pad_x, pad_y))
        self.screen.blit(toast_surf, (tx, ty))

    def _draw_mode_menu(self) -> None:
        self.mode_menu_rects.clear()
        base_btn = self.buttons["mode"]
        mx = base_btn.rect.x
        my = base_btn.rect.bottom + 4
        mw = 210
        item_h = 32
        total_h = len(self.MODES) * item_h + 8

        menu_surf = pygame.Surface((mw, total_h), pygame.SRCALPHA)
        pygame.draw.rect(menu_surf, (25, 32, 44, 250), (0, 0, mw, total_h), border_radius=8)
        pygame.draw.rect(menu_surf, (60, 75, 100), (0, 0, mw, total_h), width=1, border_radius=8)
        self.screen.blit(menu_surf, (mx, my))

        mouse_pos = pygame.mouse.get_pos()

        for i, (key, label) in enumerate(self.MODES.items()):
            item_r = pygame.Rect(mx + 4, my + 4 + i * item_h, mw - 8, item_h)
            self.mode_menu_rects[key] = item_r
            is_hover = item_r.collidepoint(mouse_pos)
            is_active = (key == self.current_mode_key)

            if is_hover:
                pygame.draw.rect(self.screen, (45, 58, 78), item_r, border_radius=5)
            elif is_active:
                pygame.draw.rect(self.screen, (32, 45, 65), item_r, border_radius=5)

            color = (255, 215, 0) if is_active else ((255, 255, 255) if is_hover else (205, 215, 225))
            txt = self.font_toolbar.render(label, True, color)
            self.screen.blit(txt, (item_r.x + 10, item_r.y + (item_h - txt.get_height()) // 2))

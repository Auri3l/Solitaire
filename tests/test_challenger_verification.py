import unittest
import random
from typing import List, Dict, Any, Optional

from solitaire.core.card import Color, Suit, Rank, Card
from solitaire.core.pile import PileType, Pile, Deck
from solitaire.core.commands import Command, CardMoveCommand, StockDealCommand, CommandHistory
from solitaire.core.base_game import BaseGame, GameStatus, Move, MoveResult
from solitaire.games.freecell import FreeCellGame, FreeCellMoveType
from solitaire.games.spider import SpiderGame, SpiderDifficulty, SpiderMoveType, SpiderClearRunCommand, SpiderDealCommand


class TestAdversarialDefectReevaluations(unittest.TestCase):
    def test_defect1_spider_manual_move_to_foundation_exhaustive(self):
        for diff in [SpiderDifficulty.ONE_SUIT, SpiderDifficulty.TWO_SUIT, SpiderDifficulty.FOUR_SUIT]:
            game = SpiderGame(difficulty=diff, seed=42)
            top_card = game.tableau[0].peek()
            snap_before = game.get_state_snapshot()

            for f_idx in range(8):
                f_id = f'foundation_{f_idx}'
                res = game.make_move(Move('tableau_0', f_id, card_id=top_card.card_id))
                self.assertFalse(res.success, f'Allowed move to {f_id} without move_type')
                self.assertFalse(game.is_legal_move(Move('tableau_0', f_id, card_id=top_card.card_id)))

                res_forged = game.make_move(
                    Move('tableau_0', f_id, card_id=top_card.card_id, move_type=SpiderMoveType.TABLEAU_TO_TABLEAU)
                )
                self.assertFalse(res_forged.success, f'Allowed forged move to {f_id} via TABLEAU_TO_TABLEAU enum')

                res_forged_str = game.make_move(
                    Move('tableau_0', f_id, card_id=top_card.card_id, move_type='tableau_to_tableau')
                )
                self.assertFalse(res_forged_str.success, f'Allowed forged move to {f_id} via string move_type')

                res_multi = game.make_move(Move('tableau_0', f_id, card_count=2))
                self.assertFalse(res_multi.success, f'Allowed multi-card move to {f_id}')

            self.assertEqual(game.get_state_snapshot(), snap_before)

    def test_defect2_spider_move_out_of_foundation_exhaustive(self):
        game = SpiderGame(difficulty=SpiderDifficulty.ONE_SUIT, seed=42)
        game.tableau[0].clear()
        test_card = Card(Suit.SPADES, Rank.KING, is_face_up=True, card_id=99)
        game.foundations[0].push(test_card)
        snap_before = game.get_state_snapshot()

        destinations = ['tableau_0', 'tableau_1', 'stock', 'foundation_1']
        for dst in destinations:
            res = game.make_move(Move('foundation_0', dst, card_id=99))
            self.assertFalse(res.success, f'Allowed move out of foundation_0 to {dst}')
            self.assertFalse(game.is_legal_move(Move('foundation_0', dst, card_id=99)))

            res_forged = game.make_move(
                Move('foundation_0', dst, card_id=99, move_type=SpiderMoveType.TABLEAU_TO_TABLEAU)
            )
            self.assertFalse(res_forged.success, f'Allowed forged move out of foundation_0 to {dst}')

            res_forged_str = game.make_move(
                Move('foundation_0', dst, card_id=99, move_type='tableau_to_tableau')
            )
            self.assertFalse(res_forged_str.success, f'Allowed forged string move out of foundation_0 to {dst}')

        self.assertEqual(game.get_state_snapshot(), snap_before)

    def test_defect3_spider_move_to_stock_exhaustive(self):
        game = SpiderGame(difficulty=SpiderDifficulty.ONE_SUIT, seed=42)
        game.stock.clear()
        game.stock.push(Card(Suit.SPADES, Rank.EIGHT, is_face_up=False, card_id=99))

        game.tableau[0].clear()
        game.tableau[0].push(Card(Suit.SPADES, Rank.SEVEN, is_face_up=True, card_id=100))
        snap_before = game.get_state_snapshot()

        res = game.make_move(Move('tableau_0', 'stock', card_id=100))
        self.assertFalse(res.success, 'Allowed tableau to stock move')
        self.assertFalse(game.is_legal_move(Move('tableau_0', 'stock', card_id=100)))

        res_deal = game.make_move(Move('tableau_0', 'stock', move_type=SpiderMoveType.DEAL_STOCK))
        self.assertFalse(res_deal.success, 'Allowed tableau to stock with DEAL_STOCK')

        res_tab = game.make_move(Move('tableau_0', 'stock', move_type=SpiderMoveType.TABLEAU_TO_TABLEAU))
        self.assertFalse(res_tab.success, 'Allowed tableau to stock with TABLEAU_TO_TABLEAU')

        res_self = game.make_move(Move('stock', 'stock', move_type=SpiderMoveType.TABLEAU_TO_TABLEAU))
        self.assertFalse(res_self.success, 'Allowed stock to stock')

        self.assertEqual(game.get_state_snapshot(), snap_before)

    def test_defect4_freecell_move_between_foundations_exhaustive(self):
        for demotion_setting in [False, True]:
            game = FreeCellGame(seed=42, allow_foundation_demotion=demotion_setting)
            game.foundations[0].push(Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=10))
            game.foundations[0].push(Card(Suit.SPADES, Rank.TWO, is_face_up=True, card_id=11))
            game.foundations[1].push(Card(Suit.SPADES, Rank.THREE, is_face_up=True, card_id=12))
            snap_before = game.get_state_snapshot()

            for f_src, f_dst in [('foundation_0', 'foundation_1'), ('foundation_1', 'foundation_0'), ('foundation_0', 'foundation_2')]:
                res = game.make_move(Move(f_src, f_dst, card_id=11))
                self.assertFalse(res.success, f'Allowed {f_src} to {f_dst} with demotion={demotion_setting}')
                self.assertFalse(game.is_legal_move(Move(f_src, f_dst, card_id=11)))

                for mtype in FreeCellMoveType:
                    res_forged = game.make_move(Move(f_src, f_dst, card_id=11, move_type=mtype))
                    self.assertFalse(res_forged.success, f'Allowed {f_src} to {f_dst} with forged {mtype}')

            self.assertEqual(game.get_state_snapshot(), snap_before)

    def test_defect5_freecell_foundation_demotion_toggle(self):
        game_no_demote = FreeCellGame(seed=42, allow_foundation_demotion=False)
        game_no_demote.foundations[0].push(Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=50))
        snap_no_demote = game_no_demote.get_state_snapshot()

        res_fc = game_no_demote.make_move(Move('foundation_0', 'freecell_0', card_id=50))
        self.assertFalse(res_fc.success)

        res_fc_forged = game_no_demote.make_move(
            Move('foundation_0', 'freecell_0', card_id=50, move_type=FreeCellMoveType.FOUNDATION_TO_FREECELL)
        )
        self.assertFalse(res_fc_forged.success)

        game_no_demote.cascades[0].clear()
        game_no_demote.cascades[0].push(Card(Suit.HEARTS, Rank.TWO, is_face_up=True, card_id=51))
        res_casc = game_no_demote.make_move(Move('foundation_0', 'cascade_0', card_id=50))
        self.assertFalse(res_casc.success)

        game_demote = FreeCellGame(seed=42, allow_foundation_demotion=True)
        game_demote.score = 30
        game_demote.foundations[0].push(Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=50))
        initial_score = game_demote.score

        res_demote_fc = game_demote.make_move(Move('foundation_0', 'freecell_0', card_id=50))
        self.assertTrue(res_demote_fc.success, f'Demotion to freecell failed: {res_demote_fc.error_message}')
        self.assertEqual(len(game_demote.foundations[0]), 0)
        self.assertEqual(len(game_demote.free_cells[0]), 1)
        self.assertEqual(game_demote.free_cells[0].peek().card_id, 50)
        self.assertEqual(game_demote.score, initial_score - 15)

        self.assertTrue(game_demote.undo())
        self.assertEqual(len(game_demote.foundations[0]), 1)
        self.assertEqual(len(game_demote.free_cells[0]), 0)
        self.assertEqual(game_demote.score, initial_score)

        self.assertTrue(game_demote.redo())
        self.assertEqual(len(game_demote.foundations[0]), 0)
        self.assertEqual(len(game_demote.free_cells[0]), 1)
        self.assertEqual(game_demote.score, initial_score - 15)

        game_demote.cascades[0].clear()
        res_fc_to_casc = game_demote.make_move(Move('freecell_0', 'cascade_0', card_id=50))
        self.assertTrue(res_fc_to_casc.success)


class TestIntensiveRandomWalkAndFuzzer(unittest.TestCase):
    def test_freecell_extended_random_walk_200_steps(self):
        for seed in [101, 202, 303]:
            random.seed(seed)
            game = FreeCellGame(seed=seed)
            moves_applied = 0
            for step in range(200):
                all_cards = [c for p in set(game.piles.values()) for c in p.cards]
                self.assertEqual(len(all_cards), 52)
                self.assertEqual(set(c.card_id for c in all_cards), set(range(52)))
                for fc in game.free_cells:
                    self.assertLessEqual(len(fc), 1)

                r = random.random()
                if r < 0.20 and game.can_undo:
                    self.assertTrue(game.undo())
                elif r < 0.35 and game.can_redo:
                    self.assertTrue(game.redo())
                else:
                    legal = game.get_legal_moves()
                    if not legal:
                        if game.can_undo:
                            game.undo()
                        else:
                            break
                    else:
                        m = random.choice(legal)
                        res = game.make_move(m)
                        self.assertTrue(res.success)
                        moves_applied += 1

            self.assertGreater(moves_applied, 40)

    def test_spider_extended_random_walk_all_suits(self):
        for diff in [SpiderDifficulty.ONE_SUIT, SpiderDifficulty.TWO_SUIT, SpiderDifficulty.FOUR_SUIT]:
            random.seed(42 + diff.value)
            game = SpiderGame(difficulty=diff, seed=999 + diff.value)

            for step in range(200):
                all_cards = [c for p in set(game.piles.values()) for c in p.cards]
                self.assertEqual(len(all_cards), 104)
                self.assertEqual(set(c.card_id for c in all_cards), set(range(104)))
                self.assertEqual(len(game.stock) % 10, 0)
                for f in game.foundations:
                    if not f.is_empty:
                        self.assertEqual(len(f), 13)

                r = random.random()
                if r < 0.15 and game.can_undo:
                    self.assertTrue(game.undo())
                elif r < 0.25 and game.can_redo:
                    self.assertTrue(game.redo())
                else:
                    legal = game.get_legal_moves()
                    if not legal:
                        if game.can_undo:
                            game.undo()
                        else:
                            break
                    else:
                        m = random.choice(legal)
                        res = game.make_move(m)
                        self.assertTrue(res.success)

    def test_massive_adversarial_mutation_fuzzer_3000_moves(self):
        random.seed(777)
        fc = FreeCellGame(seed=42)
        sp = SpiderGame(difficulty=SpiderDifficulty.FOUR_SUIT, seed=42)

        fc_piles = list(fc.piles.keys()) + ['dummy', '', 'null', 'cascade_99', 'foundation_99', 'freecell_99']
        sp_piles = list(sp.piles.keys()) + ['dummy', '', 'null', 'tableau_99', 'foundation_99', 'stock_99']

        for i in range(1500):
            src = random.choice(fc_piles)
            dst = random.choice(fc_piles)
            cid = random.choice([None, -1, 0, 51, 52, 999, random.randint(-100, 200)])
            ccnt = random.choice([-5, -1, 0, 1, 2, 13, 52, 53, random.randint(-10, 30)])
            mtype = random.choice([None, *list(FreeCellMoveType)])

            snap_before = fc.get_state_snapshot()
            try:
                move = Move(source_pile_id=src, dest_pile_id=dst, card_id=cid if isinstance(cid, int) else None, card_count=ccnt if isinstance(ccnt, int) else 1, move_type=mtype)
                res = fc.make_move(move)
                if not res.success:
                    self.assertEqual(fc.get_state_snapshot(), snap_before)
            except Exception as e:
                self.fail(f'FreeCell fuzzer crashed on step {i}: {type(e)}: {e}')

        for i in range(1500):
            src = random.choice(sp_piles)
            dst = random.choice(sp_piles)
            cid = random.choice([None, -1, 0, 103, 104, 999, random.randint(-100, 300)])
            ccnt = random.choice([-5, -1, 0, 1, 2, 13, 104, 105, random.randint(-10, 30)])
            mtype = random.choice([None, *list(SpiderMoveType)])

            snap_before = sp.get_state_snapshot()
            try:
                move = Move(source_pile_id=src, dest_pile_id=dst, card_id=cid if isinstance(cid, int) else None, card_count=ccnt if isinstance(ccnt, int) else 1, move_type=mtype)
                res = sp.make_move(move)
                if not res.success:
                    self.assertEqual(sp.get_state_snapshot(), snap_before)
            except Exception as e:
                self.fail(f'Spider fuzzer crashed on step {i}: {type(e)}: {e}')


if __name__ == '__main__':
    unittest.main()

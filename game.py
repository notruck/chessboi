from board import DrawBoard
from time import time

import pyffish as sf


CWDA_TEXT = """
**FIDE mirror**
startFen = rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1
**FIDE vs COLORBOUND**
startFen = ewfakfwe/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1
**FIDE vs KNIGHTS**
startFen = hixokxih/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1
**FIDE vs ROOKIES**
startFen = sydckdys/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1
**COLORBOUND vs FIDE**
startFen = rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/EWFAKFWE w - - 0 1
**COLORBOUND mirror**
startFen = ewfakfwe/pppppppp/8/8/8/8/PPPPPPPP/EWFAKFWE w - - 0 1
**COLORBOUND vs KNIGHTS**
startFen = hixokxih/pppppppp/8/8/8/8/PPPPPPPP/EWFAKFWE w - - 0 1
**COLORBOUND vs ROOKIES**
startFen = sydckdys/pppppppp/8/8/8/8/PPPPPPPP/EWFAKFWE w - - 0 1

Detailed rules here: https://en.wikipedia.org/wiki/Chess_with_different_armies"""


# Variant: (folder, board type, flip pieces, rules)
VARIANTS = {'chess':            ('chess', 'checkerboard', False, 'Ordinary chess.'),
            'dragonfly':        ('chess', 'checkerboard', False, 'Crazyhouse on a smaller board, but with no pawn drops.'),
            'extinction':       ('chess', 'checkerboard', False, 'Win by capturing every piece of a certain type (eg. 1 queen or 2 bishops).'),
            'grand':            ('chess', 'checkerboard', False, 'Chess but bigger. Hawk = B+N, Elephant = R+N. Pawns promote on the 8th rank to a captured piece.'),
            'kamikazerooks':    ('chess', 'checkerboard', False, 'Lose both rooks to win!!! (???)'),
            'racingchess':      ('chess', 'checkerboard', False, 'Win by campmate. No checks allowed.'),
            'twokings':         ('chess', 'checkerboard', False, 'Chess but with two kings. You need to keep both of them safe.'),
            
            'chak':             ('chak', 'custom', False, 'Mesoamerican chess. See detailed rules at https://www.pychess.org/variants/chak'),
            'chennis':          ('chennis', 'custom', False, 'Chess on a tennis court. See detailed rules at https://www.pychess.org/variants/chennis'),
            'cwda':             ('cwda', 'checkerboard', False, CWDA_TEXT),
            'makhouse':         ('makruk', (239, 170, 86), False, 'Makruk combined with crazyhouse.'),
            'mounted':          ('mounted', 'custom', False, 'Win by checkmate or by campmate. This variant has a lot of new pieces as well as piece drops.'),
            'pandemonium':      ('pandemonium', [(168, 200, 224), (192, 240, 255)], True, 'maybe you can figure it out'),
            'shinobimirror':    ('shinobimirror', 'checkerboard', False, 'Shinobi but both sides have the ninja army!')
            }

class Game:
    def __init__(self, variant='chess', wplayer=None, bplayer=None, startpos=None):
        self.variant = variant
        self.wplayer = wplayer
        self.bplayer = bplayer
        self.start = time()
        self.moves = []
        self.drawcount = 0
        self.w_offered_draw = False
        self.b_offered_draw = False
        self.w_offered_takeback = False
        self.b_offered_takeback = False
        self.bot_skill = 0
        self.premove = None
        self.custom_fen = startpos and (startpos != sf.start_fen(variant))
        self.startpos = startpos if self.custom_fen else sf.start_fen(variant)
        self.fen = self.startpos
        self.active = True

    @staticmethod
    def variants_list():
        return sorted(VARIANTS.keys())

    @staticmethod
    def rules(variant):
        return VARIANTS[variant][3]
    
    def get_folder(self):
        return VARIANTS[self.variant][0]

    def board_type(self):
        return VARIANTS[self.variant][1]

    def flip_variant(self):
        return VARIANTS[self.variant][2]

    def age_minutes(self):
        return round((time()-self.start)/60, 2)

    def turn(self, opposite=False):
        white_to_move = "w" in self.fen.split()
        return ["Black", "White"][white_to_move != opposite] # if opposite is True, white_to_move is flipped

    def render(self, img_name):
        upside_down = self.turn() == "Black"
        flip_pieces = self.flip_variant() and upside_down
        lastmove = self.moves[-1] if self.moves else None

        board = DrawBoard(self.fen, self.get_folder(), lastmove,
                          upside_down, self.board_type(), flip_pieces)
        board.render_board(img_name)
        return img_name

    def closest_san(self, input_move):
        legal = self.legal_moves() # All legal moves, in SAN format

        match_casesens = [m for m in legal if m == input_move]
        if len(match_casesens) == 1:
            return match_casesens[0]

        prefix_casesens = [m for m in legal if m.startswith(input_move)]
        if len(prefix_casesens) == 1:
            return prefix_casesens[0]

        match_lower = [m for m in legal if m.lower() == input_move.lower()]
        if len(match_lower) == 1:
            return match_lower[0]
        
        prefix_lower = [m for m in legal if m.lower().startswith(input_move.lower())]
        if len(prefix_lower) == 1:
            return prefix_lower[0]
        
        return None
    
    def make_move(self, san_move):
        uci_legal_moves = sf.legal_moves(self.variant, self.fen, [])
        
        for move in uci_legal_moves:
            if sf.get_san(self.variant, self.fen, move) == san_move:
                self.moves += [move]
                break

        self.cancel_offers()
        self.update_fen()

    def legal_moves(self):
        uci_moves = sf.legal_moves(self.variant, self.fen, [])
        return [sf.get_san(self.variant, self.fen, move) for move in uci_moves]

    def get_moves(self):
        return sf.get_san_moves(self.variant, self.startpos, self.moves)

    def takeback_move(self, count):
        self.moves = self.moves[:-count]
        self.cancel_offers()
        self.update_fen()
        
    def cancel_offers(self):
        self.w_offered_draw = False
        self.b_offered_draw = False
        self.w_offered_takeback = False
        self.b_offered_takeback = False

    def update_fen(self):
        self.fen = sf.get_fen(self.variant, self.startpos, self.moves)

    def player_is_playing(self, player_name):
        return player_name in (self.wplayer, self.bplayer)

    def drawn_game(self):
        return self.drawcount >= 10 and len(self.moves) >= 60
    
    def is_selfplay(self):
        return self.wplayer == self.bplayer
    
    def player_turn(self, player_name, opposite=False):
        white_player = self.wplayer == player_name and self.turn(opposite=opposite) == 'White'
        black_player = self.bplayer == player_name and self.turn(opposite=opposite) == 'Black'
        
        return white_player or black_player
    
    def ended(self):
        uci_legal_moves = sf.legal_moves(self.variant, self.fen, [])
        
        if len(uci_legal_moves) == 0:
            result = sf.game_result(self.variant, self.fen, [])
            turn = self.turn()
            
            if result == sf.VALUE_MATE:
                return self.turn()
            elif result == -sf.VALUE_MATE:
                return self.turn(opposite=True)
            elif result == sf.VALUE_DRAW:
                return 'Draw'

        return False

from clip import GameClip
from board import DrawBoard
from time import time

import pyffish as sf

# really long text so separate variable
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
VARIANTS = {'chess':			('chess', 'checkerboard', False, 'Ordinary chess.'),
			'chessvshp':		('chess', 'checkerboard', False, 'Chess vs the Hoppel-Poppel army.'),
			'crazyhouse':		('chess', 'checkerboard', False, 'Chess but you can AIRDROP pieces?!?!?!11 (It\'s CRAZY)'),
			'dragonfly':		('chess', 'checkerboard', False, 'Crazyhouse on a smaller board, but with no pawn drops.'),
			'extinction':		('chess', 'checkerboard', False, 'Win by capturing every piece of a certain type (eg. 1 queen or 2 bishops).'),
			'grand':			('chess', 'checkerboard', False, 'Chess but bigger. Hawk = B+N, Elephant = R+N. Pawns promote on the 8th rank to a captured piece.'),
			'kamikazerooks':	('chess', 'checkerboard', False, 'Lose both rooks to win!!! (???)'),
			'racingchess':		('chess', 'checkerboard', False, 'Win by campmate. No checks allowed.'),
			'twokings':			('chess', 'checkerboard', False, 'Chess but with two kings. You need to keep both of them safe.'),

			'chak':				('chak', 'custom', False, 'Mesoamerican chess. See detailed rules at https://www.pychess.org/variants/chak'),
			'chennis':			('chennis', 'custom', False, 'Chess on a tennis court. See detailed rules at https://www.pychess.org/variants/chennis'),
			'cwda':				('cwda', 'checkerboard', False, CWDA_TEXT),
			'makhouse':			('makruk', (239, 170, 86), False, 'Makruk combined with crazyhouse.'),
			'mounted':			('mounted', 'custom', False, 'Win by checkmate or by campmate. This variant has a lot of new pieces as well as piece drops.'),
			'ordavsempire':		('ordavsempire', 'checkerboard', False, 'Orda vs Empire army'),
			'pandemonium':		('pandemonium', [(168, 200, 224), (192, 240, 255)], True, 'maybe you can figure it out'),
			'shinobimirror':	('shinobimirror', 'checkerboard', False, 'Shinobi but both sides have the ninja army!')
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
		flip_pieces = self.flip_variant() and upside_down
		upside_down = self.turn() == "Black"
		lastmove = self.moves[-1] if self.moves else None

		DrawBoard(self.board_type(), self.get_folder(), flip_pieces,
				  upside_down, self.fen, lastmove).render_board(img_name)
		
		return img_name

	def render_clip(self, clip_name):
		WIDTH = 800
		HEIGHT = 1000
		FPS = 2
		
		clip = GameClip(WIDTH, HEIGHT, FPS, clip_name)
		curr_moves = []
		flip_pieces = upside_down = lastmove = False
		
		# add start position
		# upside_down and flip_pieces will be false as the board is always from White's view
		board_img = DrawBoard(self.board_type(), self.get_folder(), flip_pieces, upside_down, 
							  self.startpos, lastmove).draw_board(stabilise_pocket=True)
		
		frame = DrawBoard.scale_to_fit(WIDTH, HEIGHT, board_img)
		
		clip.add_img(frame, frames=2)
		
		# loop over each move and repeat
		for i in range(len(self.moves)):
			curr_moves += [self.moves[i]]
			curr_fen = sf.get_fen(self.variant, self.startpos, curr_moves, True)
		
			board_img = DrawBoard(self.board_type(), self.get_folder(), flip_pieces, upside_down, 
								  curr_fen, curr_moves[-1]).draw_board(stabilise_pocket=True)
			
			frame = DrawBoard.scale_to_fit(WIDTH, HEIGHT, board_img)
			
			clip.add_img(frame, frames=1)
		
		# show the end position for another frame
		clip.add_img(frame, frames=1)
		
		# save the clip
		clip.save()
		return clip_name

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
		uci_legal_moves = sf.legal_moves(self.variant, self.fen, [], True)

		for move in uci_legal_moves:
			if sf.get_san(self.variant, self.fen, move, True) == san_move:
				self.moves += [move]
				break

		self.cancel_offers()
		self.update_fen()

	def legal_moves(self):
		uci_moves = sf.legal_moves(self.variant, self.fen, [], True)
		return [sf.get_san(self.variant, self.fen, move, True) for move in uci_moves]

	def get_moves(self):
		return sf.get_san_moves(self.variant, self.startpos, self.moves, True)

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
		self.fen = sf.get_fen(self.variant, self.startpos, self.moves, True)

	def player_is_playing(self, player_name):
		return player_name in (self.wplayer, self.bplayer)

	def drawn_game(self):
		return self.drawcount >= 10 and len(self.moves) >= 80

	def is_selfplay(self):
		return self.wplayer == self.bplayer

	def player_turn(self, player_name, opposite=False):
		white_player = self.wplayer == player_name and self.turn(opposite=opposite) == 'White'
		black_player = self.bplayer == player_name and self.turn(opposite=opposite) == 'Black'

		return white_player or black_player

	def ended(self):
		uci_legal_moves = sf.legal_moves(self.variant, self.fen, [], True)

		if (len(sf.legal_moves(self.variant, self.startpos, self.moves, True)) == 0
			or sf.is_optional_game_end(self.variant, self.startpos, self.moves, True)[0]
			or sf.is_immediate_game_end(self.variant, self.startpos, self.moves, True)[0]
			or all(sf.has_insufficient_material(self.variant, self.startpos, self.moves, True))):

			result = sf.game_result(self.variant, self.startpos, self.moves, True)
			turn = self.turn()

			if result == sf.VALUE_MATE:
				return self.turn()
			elif result == -sf.VALUE_MATE:
				return self.turn(opposite=True)
			elif result == sf.VALUE_DRAW:
				return 'Draw'

		return False

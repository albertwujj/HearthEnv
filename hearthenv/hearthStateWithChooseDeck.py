
# Written by Peter Cowling, Ed Powley, Daniel Whitehouse (University of York, UK) September 2012.
#
# Licence is granted to freely use and distribute for any sensible/legal purpose so long as this comment
# remains in any distributed code.
#
# For more information about Monte Carlo Tree Search check out our web site at www.mcts.ai

from math import *
import copy
import logging
import random
import time
import sys, traceback
import itertools
from enum import Enum
from fireplace import cards
from fireplace.deck import Deck
from hearthstone.enums import CardType, Rarity, PlayState, CardClass
from fireplace.game import Game
from fireplace.player import Player

from fireplace.utils import *

from random import randint

# logging.getLogger().setLevel(logging.DEBUG)
logging.disable(sys.maxint)


class MOVE(Enum):
	PRE_GAME = 1
	PICK_CLASS = 2
	PICK_CARD = 3
	END_TURN = 4
	HERO_POWER = 5
	MINION_ATTACK = 6
	HERO_ATTACK = 7
	PLAY_CARD = 8
	MULLIGAN = 9
	CHOICE = 10


cards.db.initialize()
class HearthState:
	""" A state of the game, i.e. the game board.
    """

	def __init__(self):

		self.playerJustMoved = 2  # At the root pretend the player just moved is p2 - p1 has the first move
		random.seed(1857)

		# The idea of adjacent cards it to ignore minion placement if none of these cards can be found, since it doesn't
		# matter.
		# adjacent_cards = ["Dire Wolf Alpha", "Ancient Mage", "Defender of Argus", "Sunfury Protector",
		#                  "Flametongue Totem", "Explosive Shot", "Cone of Cold", "Betrayal", "Void Terror",
		#                  "Unstable Portal", "Wee Spellstopper", "Piloted Shredder", "Piloted Sky Golem",
		#                  "Recombobulator", "Foe Reaper 4000", "Nefarian"]
		# self.adjacent_cards = adjacent_cards
		self.player1 = None
		self.hero1 = None
		self.deck1 = []

		self.player2 = None
		self.hero2 = None
		self.deck2 = []

		self.game = None



	# Simple Arcane Missiles lethal test
	# self.deck1 = ["EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277",
	#              "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277",
	#              "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277",
	#              "EX1_277", "EX1_277", "EX1_277"]
	# self.hero1 = MAGE
	# self.player1 = Player("one", self.deck1, self.hero1)
	# self.deck2 = ["EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277",
	#              "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277",
	#              "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277",
	#              "EX1_277", "EX1_277", "EX1_277"]
	# self.hero2 = MAGE
	# self.player2 = Player("two", self.deck2, self.hero2)
	# self.game = Game(players=(self.player1, self.player2))
	# self.game.start()
	# for player in self.game.players:
	#    if player.choice:
	#        player.choice.choose()
	# self.game.players[0].hero.hit(24)
	# self.game.players[1].hero.hit(24)


	def Clone(self):
		""" Create a deep clone of this game state.
        """
		st = HearthState()
		st.playerJustMoved = self.playerJustMoved
		st.player1 = self.player1
		st.hero1 = self.hero1
		st.deck1 = copy.copy(self.deck1)
		st.player2 = self.player2
		st.hero2 = self.hero2
		st.deck2 = copy.copy(self.deck2)
		# st.game = copy.copy(self.game)
		st.game = copy.deepcopy(self.game)
		return st

	def DoMove(self, move):
		""" Update a state by carrying out the given move.
        """

		#print("move %s" % move[0])

		if self.game is not None:
			assert self.game.current_player.playstate == PlayState.PLAYING
			if self.game.current_player is not None:
				if self.game.current_player.name == "one":
					self.playerJustMoved = 1
				else:
					self.playerJustMoved = 2
		else:
			self.playerJustMoved = -(self.playerJustMoved - 1) + 2

		try:
			if move[0] == MOVE.PRE_GAME:
				self.player1 = Player("one", self.deck1, self.hero1)
				self.player2 = Player("two", self.deck2, self.hero2)
				self.game = Game(players=(self.player1, self.player2))
				self.game.start()

				for player in self.game.players:
					if player.choice:
						player.choice.choose()
			elif move[0] == MOVE.PICK_CLASS:
				if self.playerJustMoved == 1:
					self.hero1 = move[1]
				else:
					self.hero2 = move[1]
			elif move[0] == MOVE.PICK_CARD:
				if len(self.deck1) < 30:
					self.deck1.append(move[1].id)
				else:
					self.deck2.append(move[1].id)
			elif move[0] == MOVE.MULLIGAN:
				self.game.current_player.choice.choose(*move[1])
			elif move[0] == MOVE.END_TURN:
				self.game.end_turn()
			elif move[0] == MOVE.HERO_POWER:
				heropower = self.game.current_player.hero.power
				if move[3] is None:
					heropower.use()
				else:
					heropower.use(target=heropower.targets[move[3]])
			elif move[0] == MOVE.PLAY_CARD:
				card = self.game.current_player.hand[move[2]]
				if move[3] is None:
					card.play()
				else:
					card.play(target=card.targets[move[3]])
			elif move[0] == MOVE.MINION_ATTACK:
				minion = self.game.current_player.field[move[2]]
				minion.attack(minion.targets[move[3]])
			elif move[0] == MOVE.HERO_ATTACK:
				hero = self.game.current_player.hero
				hero.attack(hero.targets[move[3]])
			elif move[0] == MOVE.CHOICE:
				self.game.current_player.choice.choose(move[1])
			else:
				raise NameError("DoMove ran into unclassified card", move)
		except:
			print("do move failed")
			return




	def GetMoves(self):
		""" Get all possible moves from this state.
		"""

		if self.game is not None:
			if self.game.current_player.playstate != PlayState.PLAYING:
				return []
		valid_moves = []  # Move format is [enum, card, index of card in hand, target index]
		if self.game is None and self.hero1 is None:  # choose p1 hero
			for i in range(2, 10):  # all 8 player classes
				valid_moves.append([MOVE.PICK_CLASS, CardClass(i).default_hero])
		elif self.game is None and len(
			self.deck1) == 30 and self.hero2 is None:  # choose p2 hero after choosing p1 hero and deck
			for i in range(2, 10):
				valid_moves.append([MOVE.PICK_CLASS, CardClass(i).default_hero])
		elif self.game is None and len(self.deck1) < 30 or len(
			self.deck2) < 30:  # will let p1 choose cards until done, then p2
			collection = []
			exclude = []
			if len(self.deck1) < 30:
				hero = cards.db[self.hero1]
				deck = self.deck1
			else:
				hero = cards.db[self.hero2]
				deck = self.deck2

			for card in cards.db.keys():
				if card in exclude:
					continue
				cls = cards.db[card]
				if not cls.collectible:
					continue
				if cls.type == CardType.HERO:
					# Heroes are collectible...
					continue
				if cls.card_class and cls.card_class != hero.card_class:
					continue
				if deck.count(cls.id) < cls.max_count_in_deck:
					valid_moves.append([MOVE.PICK_CARD, cls])
		elif self.game is None:  # all cards have been chosen
			valid_moves.append([MOVE.PRE_GAME])
		elif self.game.current_player.choice is not None:
			for card in self.game.current_player.choice.cards:
				valid_moves.append([MOVE.CHOICE, card])
		else:
			# Play card
			for card in self.game.current_player.hand:
				dupe = False
				for i in range(len(valid_moves)):
					if valid_moves[i][1].id == card.id:
						dupe = True
						break
				if not dupe:
					if card.is_playable():
						if len(card.targets) > 0:
							for t in range(len(card.targets)):
								valid_moves.append(
									[MOVE.PLAY_CARD, card, self.game.current_player.hand.index(card), t])
						else:
							valid_moves.append(
								[MOVE.PLAY_CARD, card, self.game.current_player.hand.index(card), None])

			# Hero Power
			heropower = self.game.current_player.hero.power
			if heropower.is_usable():
				if len(heropower.targets) > 0:
					for t in range(len(heropower.targets)):
						valid_moves.append([MOVE.HERO_POWER, None, None, t])
				else:
					valid_moves.append([MOVE.HERO_POWER, None, None, None])
			# Minion Attack
			for minion in self.game.current_player.field:
				if minion.can_attack():
					for t in range(len(minion.targets)):
						valid_moves.append(
							[MOVE.MINION_ATTACK, minion, self.game.current_player.field.index(minion), t])

			# Hero Attack
			hero = self.game.current_player.hero
			if hero.can_attack():
				for t in range(len(hero.targets)):
					valid_moves.append([MOVE.HERO_ATTACK, hero, None, t])
			valid_moves.append([MOVE.END_TURN])
		return valid_moves

	def FastGetRandomMove(self):
		if self.game is not None:
			if self.game.current_player.playstate != PlayState.PLAYING:
				return []

		# Move format is [enum, card, index of card in hand, target index]

		if self.game is None and self.hero1 is None: # choose p1 hero
			return [MOVE.PICK_CLASS, CardClass(randint(2, 10)).default_hero]
		if self.game is None and len(self.deck1) == 30 and self.hero2 is None:
			return [MOVE.PICK_CLASS, CardClass(randint(2, 10)).default_hero]
		if self.game is None and len(self.deck1) < 30 or len(self.deck2) < 30:
			possible_cards = []
			exclude = []
			if len(self.deck1) < 30:
				hero = cards.db[self.hero1]
				deck = self.deck1
			else:
				hero = cards.db[self.hero2]
				deck = self.deck2

			for card in cards.db.keys():
				if card in exclude:
					continue
				cls = cards.db[card]
				if not cls.collectible:
					continue
				if cls.type == CardType.HERO:
					# Heroes are collectible...
					continue
				if cls.card_class and cls.card_class != hero.card_class:
					continue
				if cls.rarity == Rarity.LEGENDARY and cls.id in deck:
					continue
				if deck.count(cls.id) < Deck.MAX_UNIQUE_CARDS:
					possible_cards.append(cls)

			return [MOVE.PICK_CARD, random.choice(possible_cards)]
		elif self.game is None: # all cards have been chosen
			return [MOVE.PRE_GAME]

		elif self.game.current_player.choice is not None:
			card = random.choice(self.game.current_player.choice.cards)
			return [MOVE.CHOICE, card]
		else:
			chance = random.random()
			threshold = 0
			if chance < threshold + .02:  # 2% chance
				return [MOVE.END_TURN]

			# Play card
			if chance < threshold + .30:  # 30% chance
				card = random.choice(self.game.current_player.hand)
				if card.is_playable():
					if len(card.targets) > 0:
						t = randint(0, len(card.targets) - 1)
						return [MOVE.PLAY_CARD, card, self.game.current_player.hand.index(card), t]
					else:
						return [MOVE.PLAY_CARD, card, self.game.current_player.hand.index(card), None]

			# Hero Power
			if chance < threshold + .10:
				heropower = self.game.current_player.hero.power
				if heropower.is_usable():
					if len(heropower.targets) > 0:
						t = randint(0, len(heropower.targets) - 1)
						return [MOVE.HERO_POWER, None, None, t]
					else:
						return [MOVE.HERO_POWER, None, None, None]

			# Hero Attack
			if chance < threshold + .20:
				hero = self.game.current_player.hero
				if hero.can_attack():
					t = randint(0, len(hero.targets) - 1)
					return [MOVE.HERO_ATTACK, hero, None, t]

			# 30% chance, or if another option selected had no possible moves remaining
			# Minion Attack
			for minion in self.game.current_player.field:
				if minion.can_attack():
					t = randint(0, len(minion.targets) - 1)
					return [MOVE.MINION_ATTACK, minion, self.game.current_player.field.index(minion), t]

			# if no other moves remaining
			return [MOVE.END_TURN]
		return random_move


	def GetResult(self, playerjm):
		""" Get the game result from the viewpoint of playerjm.
        """
		if self.game.players[0].hero.health <= 0 and self.game.players[1].hero.health <= 0:
			return 0.1
		elif self.game.players[playerjm - 1].hero.health <= 0:  # loss
			return 0
		elif self.game.players[2 - playerjm].hero.health <= 0:  # win
			return pow(0.99, self.game.turn)
		else:  # Should not be possible to get here unless we call GetResult() early (before a hero has <= 0 hp)
			return 0.1

	def __repr__(self):
		try:
			s = "Turn: " + str(self.game.turn)
			s += "\n[" + str(self.game.players[0].hero.health) + " hp ~ " + str(
				len(self.game.players[0].hand)) + " in hand ~ " + str(self.game.players[0].tempMana) + "/" + str(
				self.game.players[0].maxMana) + " mana] "
			# s += "\n[" + str(self.game.players[0].hero.health) + " hp ~ " + str(len(self.game.players[0].hand)) + " in hand ~ " + str(self.game.players[0].deck.left) + "/" + str(len(self.game.players[0].deck.cards)) + " in deck ~ " + str(self.game.players[0].mana) + "/" + str(self.game.players[0].max_mana) + " mana] "
			for minion in self.game.players[0].field:
				s += str(minion.atk) + "/" + str(minion.health) + ":"
			s += "\n[" + str(self.game.players[1].hero.health) + " hp ~ " + str(
				len(self.game.players[1].hand)) + " in hand ~ " + str(self.game.players[1].tempMana) + "/" + str(
				self.game.players[1].maxMana) + " mana] "
			# s += "\n[" + str(self.game.players[1].hero.health) + " hp ~ " + str(len(self.game.players[1].hand)) + " in hand ~ " + str(self.game.players[1].deck.left) + "/" + str(len(self.game.players[1].deck.cards)) + " in deck ~ " + str(self.game.players[1].mana) + "/" + str(self.game.players[1].max_mana) + " mana] "
			for minion in self.game.players[1].field:
				s += str(minion.atk) + "/" + str(minion.health) + ":"
			s += "\n" + "Current Player: " + str(self.game.currentPlayer)
			return s
		except:
			s = "Deck 1: " + ", ".join(self.deck1)
			s += "\nDeck 2: " + ", ".join(self.deck2)
			return s

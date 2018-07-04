
import logging
import copy
import random
from random import randint
import sys
from enum import Enum
from fireplace import cards, exceptions, utils
from hearthstone.enums import PlayState, Step, Mulligan, CardClass, Race
from utils import *
from color_card import *
import describe_card as describe
import game_to_input
from sty import fg

logging.disable(logging.CRITICAL)


class AutoNumber(Enum):
	def __new__(cls):
		value = len(cls.__members__)  # note no + 1
		obj = object.__new__(cls)
		obj._value_ = value
		return obj

class Move(AutoNumber):
	end_turn = ()
	hero_power = ()
	minion_attack = ()
	hero_attack = ()
	play_card = ()
	mulligan = ()
	choice = ()



string_to_move = {"end": Move.end_turn, "heropower": Move.hero_power, "minionattack": Move.minion_attack, "heroattack": Move.hero_attack,
				  "play": Move.play_card}
move_to_string = {v: k for k, v in string_to_move.items()}
cards.db.initialize()

class HearthEnv:
	""" A state of the game, i.e. the game board.
    """
	action_space = None
	observation_space = None

	def __init__(self):
		self.playerJustMoved = 2  # At the root pretend the player just moved is p2 - p1 has the first move
		self.playerToMove = 1
		self.players_ordered = None
		self.hero1 = None
		self.deck1 = None

		self.hero2 = None
		self.deck2 = None
		self.game = None
		self.setup_game()
		self.lastMovePlayed = None

	def clone(self):
		""" Create a deep clone of this environment.
        """
		st = HearthEnv()
		st.playerJustMoved = self.playerJustMoved
		st.playerToMove = self.playerToMove
		st.game = copy.deepcopy(self.game)
		st.players_ordered = [st.game.player1, st.game.player2]
		return st

	def get_possible_actions(self):
		actions = []
		for move in self.__getMoves():
			actions.append(self.__moveToAction(move))
		return actions

	def get_random_action(self):
		return self.__moveToAction(self.__fastGetRandomMove())

	def human(self):
		""" allows creating an action from the console
			safe to all input, go ask your friend to play your AI
			entered indices should start from 1
			when indexing into targets,
			the enemy hero comes first (target 1), then their field
		"""
		selection = None
		current_player = self.game.current_player
		i = 0
		print("Player " + str(self.playerToMove) + "'s turn: ")

		if self.game.step == Step.BEGIN_MULLIGAN:
			type = Move.mulligan
			selection = [int(i) - 1 for i in input("Enter the indices of the cards you want to mulligan: \n").strip().split(' ')]
			return [type.value, selection]
		elif current_player.choice is not None:
			type = Move.choice
			selection = [int(i) - 1 for i in input("Enter the indices of the cards you want to choose: \n").strip().split(' ')]
			return [type.value, selection]
		else:
			options = ""
			for k in string_to_move.keys():
				if i == len(string_to_move) - 1:
					options += "\"" + k + "\""
				else:
					options += "\"" + k + "\", "
				i += 1
			while True:
				input_arr = input(
					"Enter move type (Options: " + options +
					"), the selection index (if any), and the target index (if any): (ex. \"heropower 1\")\n").strip().split(' ')
				if input_arr[0] not in string_to_move:
					continue
				type = string_to_move[input_arr[0]]
				input_arr[1:] = [int(i) - 1 for i in input_arr[1:]]
				if type == Move.end_turn:
					return [type.value]
				if type == Move.play_card or type == Move.minion_attack:
					if len(input_arr) < 2:
						continue
					selection = input_arr[1]

				if selection is None:
					action = [type.value, None]
					if len(input_arr) > 1:
						action.append(input_arr[1])
					else:
						action.append(None)
				else:
					action = [type.value, selection]
					if len(input_arr) > 2:
						action.append(input_arr[2])
					else:
						action.append(None)
				if self.__is_safe(action):
					break
		return action


	def setup_game(self):
		if self.hero1 is None or self.hero2 is None or self.deck1 is None or self.deck2 is None:
			self.game = utils.setup_game()
			self.players_ordered = [self.game.player1, self.game.player2]
			self.playerJustMoved = 2  # At the root pretend the player just moved is p2 - p1 has the first move
			self.playerToMove = 1
			self.lastMovePlayed = None

	def step(self, action=None):
		if action is None:
			if self.game is None:
				self.setup_game()
			return
		done = self.__doMove(self.__actionToMove(action))
		return self.__getState(), self.__getReward(), done, self.playerToMove

	def reset(self):
		self.setup_game()

	def render(self, mode='human'):
		""" prints each player's board, and the move last played
		"""
		out = sys.stdout
		player1 = self.game.player1
		player2 = self.game.player2
		if self.game.step == Step.BEGIN_MULLIGAN:
			self.__printMulligan(1, out)
			self.__printMulligan(2, out)
			out.write("\n")
			return
		p1out = self.__renderplayer(player1)
		out.write(p(*p1out, s="\n", last=True))
		out.write("\n")
		p2out = reversed(self.__renderplayer(player2)) # reverse for the style
		out.write(p(*p2out, s="\n", last=True))
		out.write("\n")
		out.write("\n")

	def renderPOV(self, player_num):
		""" prints the game state from a certain player's perspective, hiding
			some information about the other player's board like official Hearthstone
		"""
		out = sys.stdout
		out.write("\n")
		if self.game.step == Step.BEGIN_MULLIGAN:
			self.__printMulligan(player_num, out)
			out.write("\n")
			return
		pout_oppo = self.__renderplayer(self.players_ordered[2 - player_num])
		out.write(p(pout_oppo[0], pout_oppo[2], s='\n', last=True))
		out.write("\n")
		pout = self.__renderplayer(self.players_ordered[player_num - 1])
		out.write(p(*reversed(pout), s= "\n", last=True))
		out.write("\n")

	def seed(self, seed):
		random.seed(seed)

	def __printMulligan(self, player_num, out):
		player = self.players_ordered[player_num - 1]
		out.write("p" + str(player_num) + " - ")
		if player.mulligan_state == Mulligan.INPUT:
			out.write("Before Mulligan: ")
			out.write(p(*describe.hand(*player.choice.cards), s = ", ") + "\n")
		else:
			out.write("After Mulligan: ")
			out.write(p(*describe.hand(*player.hand)) + "\n")

	def __doMove(self, move, exceptionTester=[]):
		""" Update a state by carrying out the given move.
			Move format is [enum, index of selected card, target index, choice]
			Returns True if game is over
			Modified version of function from Ragowit's Fireplace fork
        """
		# print("move %s" % move[0])

		self.lastMovePlayed = move

		current_player = self.game.current_player

		if not self.game.step == Step.BEGIN_MULLIGAN:
			assert current_player.playstate == PlayState.PLAYING
			if current_player.name == "one":
				self.playerJustMoved = 1
			else:
				self.playerJustMoved = 2

		try:
			if move[0] == Move.mulligan:
				cards = [self.__currentMulliganer().choice.cards[i] for i in move[1]]
				self.__currentMulliganer().choice.choose(*cards)
				self.playerToMove = self.playerJustMoved
				self.playerJustMoved = -(self.playerJustMoved - 1) + 2
			elif move[0] == Move.end_turn:
				self.game.end_turn()
			elif move[0] == Move.hero_power:
				heropower = current_player.hero.power
				if move[2] is None:
					heropower.use()
				else:
					heropower.use(target=heropower.targets[move[2]])
			elif move[0] == Move.play_card:
				card = current_player.hand[move[1]]
				args = {'target': None, 'choose': None}
				for i, k in enumerate(args.keys()):
					if len(move) > i + 2 and move[i+2] is not None:
						if k == 'target':
							args[k] = card.targets[move[i+2]]
						elif k == 'choose':
							args[k] = card.choose_cards[move[i+2]]
				card.play(**args)
			elif move[0] == Move.minion_attack:
				minion = current_player.field[move[1]]
				minion.attack(minion.targets[move[2]])
			elif move[0] == Move.hero_attack:
				hero = current_player.hero
				hero.attack(hero.targets[move[2]])
			elif move[0] == Move.choice:
				current_player.choice.choose(move[1])
		except exceptions.GameOver:
			return True
		except Exception as e:
			print("Ran into exception: {} While executing move {} for {}. Game State:".format(str(e), move, current_player))
			self.render()
			exceptionTester.append(1) # array will eval to True
		if not self.game.step == Step.BEGIN_MULLIGAN:
			self.playerToMove = 1 if self.game.current_player is self.game.player1 else 2
		return False

	def __moveToAction(self, move):
		move[0] = move[0].value
		return move

	def __actionToMove(self, action):
		action[0] = Move(action[0])
		return action

	def __getMoves(self):
		""" Get all possible moves from this state.
		    Modified version of function from Ragowit's Fireplace fork
		"""

		if self.game.ended:
			return []

		valid_moves = []

		# Mulligan
		if self.game.step == Step.BEGIN_MULLIGAN:
			player = self.__currentMulliganer()
			for s in indice_subsets(player.choice.cards):
				valid_moves.append([Move.mulligan, s])
			return valid_moves

		current_player = self.game.current_player
		if current_player.playstate != PlayState.PLAYING:
			return []

		# Choose card
		if current_player.choice is not None:
			for card in current_player.choice.cards:
				valid_moves.append([Move.choice, card])
			return valid_moves

		else:
			# Play card
			for card in current_player.hand:
				dupe = False
				for i in range(len(valid_moves)):
					if current_player.hand[valid_moves[i][1]].id == card.id:
						dupe = True
						break
				if not dupe:
					if card.is_playable():
						if card.must_choose_one:
							for i in range(len(card.choose_cards)):
								if len(card.targets) > 0:
									for t in range(len(card.targets)):
										valid_moves.append(
											[Move.play_card, current_player.hand.index(card), t, i])
								else:
									valid_moves.append(
										[Move.play_card, current_player.hand.index(card), None, i])
						elif len(card.targets) > 0:
							for t in range(len(card.targets)):
								valid_moves.append(
									[Move.play_card, current_player.hand.index(card), t, None])
						else:
							valid_moves.append(
								[Move.play_card, current_player.hand.index(card), None, None])

			# Hero Power
			heropower = current_player.hero.power
			if heropower.is_usable():
				if len(heropower.targets) > 0:
					for t in range(len(heropower.targets)):
						valid_moves.append([Move.hero_power, None, t])
				else:
					valid_moves.append([Move.hero_power, None, None])
			# Minion Attack
			for minion in current_player.field:
				if minion.can_attack():
					for t in range(len(minion.targets)):
						valid_moves.append(
							[Move.minion_attack, current_player.field.index(minion), t])

			# Hero Attack
			hero = current_player.hero
			if hero.can_attack():
				for t in range(len(hero.targets)):
					valid_moves.append([Move.hero_attack, None, t])

			valid_moves.append([Move.end_turn])
		return valid_moves

	def __fastGetRandomMove(self):
		""" Get a random possible move from this state.
			Move format is [enum, index of card in hand, target index]
			Modified version of function from Ragowit's Fireplace fork
		"""

		if self.game.ended:
			return None

		if self.game.step == Step.BEGIN_MULLIGAN:
			player = self.__currentMulliganer()
			mull_count = random.randint(0, len(player.choice.cards))
			cards_to_mulligan = random.sample([i for i, x in enumerate(player.choice.cards)], mull_count)
			return [Move.mulligan, cards_to_mulligan]

		current_player = self.game.current_player

		if current_player.playstate != PlayState.PLAYING:
			return []
		# Choose card
		elif current_player.choice is not None:
			card = random.choice(current_player.choice.cards)
			return [Move.choice, card]
		else:
			chance = random.random()
			threshold = 0
			if chance < .02:  # 2% chance
				return [Move.end_turn]

			# 90% chance to minion attack if minion can attack
			# Minion Attack
			if chance < .90:
				for minion in current_player.field:
					if minion.can_attack():
						t = randint(0, len(minion.targets) - 1)
						return [Move.minion_attack, current_player.field.index(minion), t]

			chance = random.random()
			# Play card
			if chance < .50 and len(current_player.hand) > 0: # 50% chance if no minion attack
				card = random.choice(current_player.hand)
				if card.is_playable():
					if len(card.targets) > 0:
						t = randint(0, len(card.targets) - 1)
						valid_card = [Move.play_card, current_player.hand.index(card), t]
					else:
						valid_card = [Move.play_card, current_player.hand.index(card), None]
					if card.must_choose_one:
						valid_card.append(randint(0, len(card.choose_cards) - 1))
					return valid_card
			chance = random.random()
			# Hero Attack
			if chance < .50:
				hero = current_player.hero
				if hero.can_attack():
					t = randint(0, len(hero.targets) - 1)
					return [Move.hero_attack, None, t]

			chance = random.random()
			# Hero Power
			if chance < .30:
				heropower = current_player.hero.power
				if heropower.is_usable():
					if len(heropower.targets) > 0:
						t = randint(0, len(heropower.targets) - 1)
						return [Move.hero_power, None, t]
					else:
						return [Move.hero_power, None, None]

			# if no other moves remaining
			return [Move.end_turn]


	def __is_safe(self, action):
		""" tests the action on a clone of the game state.
		"""
		copy = self.clone()
		exceptionTester = []
		copy.__doMove(copy.__actionToMove(action), exceptionTester=exceptionTester)
		if exceptionTester:
			return False
		else:
			return True

	# TODO render secrets
	def __renderplayer(self, player):
		""" returns a three-line string representing a player's board
			line 1: hero
			line 2: hand
			line 3: field
		"""
		pout = []

		h_health = fg.red + str(player.hero.health) + fg.rs
		h_mana = fg.blue + str(player.mana) + "/" + str(player.max_mana) + fg.rs

		line_1 = p(player.hero, h_health, h_mana)

		if player.hero.armor != 0:
			line_1 += "+" + str(player.hero.armor)
		if player.weapon is not None:
			line_1 += ", " + str(player.weapon.damage) + " " + str(player.weapon.durability)

		pout.append(line_1)
		hand = []

		pout.append(fg.rs + "HAND: " + p(*describe.hand(*player.hand), s=", ")) # line 2
		
		field = []
		for c in player.field:
			card = ""
			specials = []
			if c.windfury:
				specials += "W"
			if c.taunt:
				specials += "T"
			if c.divine_shield:
				specials += "D"
			if c.poisonous:
				specials += "P"
			if c.silenced:
				specials += "S"
			if c.frozen:
				specials += "F"
			if c.cannot_attack_heroes:
				specials += "H"
			c_health = str(c.max_health)
			if c.max_health != c.health:
				c_health = fg.red + str(c.health) + fg.rs + "/" + c_health
			if player is self.game.current_player:
				card += p(*color_can_attack(c), c.atk, c_health, *specials)
			else:
				card += p(c, c.atk, c_health, *specials)
			field.append(card)
		pout.append("FIELD: " + p(*field, s=", ")) # line 3
		return pout

	def getResult(self, playerjm):
		""" Get the game result from the viewpoint of playerjm.
		"""
		if self.players_ordered[0].hero.health <= 0 and self.players_ordered[1].hero.health <= 0: # tie
			return 0.1
		elif self.players_ordered[playerjm - 1].hero.health <= 0:  # loss
			return 0
		elif self.players_ordered[2 - playerjm].hero.health <= 0:  # win
			return pow(0.99, self.game.turn)
		else:  # Should not be possible to get here unless we call GetResult() early (before a hero has <= 0 hp)
			return 0.1

	def __getReward(self):
		""" Get the current reward, from the perspective of the player who just moved
			0 if game is not over
		"""
		player = self.playerJustMoved
		if self.players_ordered[0].hero.health <= 0 and self.players_ordered[1].hero.health <= 0: # tie
			return 0.1
		elif self.players_ordered[player - 1].hero.health <= 0:  # loss
			return -1
		elif self.players_ordered[2 - player].hero.health <= 0:  # win
			return 1
		else:
			return 0

	def __currentMulliganer(self):
		if not self.game.step == Step.BEGIN_MULLIGAN:
			return None
		return self.players_ordered[self.playerToMove - 1]

	def __getState(self):
		""" returns a numpy array representing the game state from playerToMove's pov
		"""
		return game_to_input.get_state(self.game, self.players_ordered[self.playerToMove - 1])
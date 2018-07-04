# This is a very simple implementation of the UCT Monte Carlo Tree Search algorithm in Python 2.7.
# The function UCT(rootstate, itermax, verbose = False) is towards the bottom of the code.
# It aims to have the clearest and simplest possible code, and for the sake of clarity, the code
# is orders of magnitude less efficient than it could be made, particularly by using a
# state.GetRandomMove() or state.DoRandomRollout() function.
#
# Example GameState classes for Nim, OXO and Othello are included to give some idea of how you
# can write your own GameState use UCT in your 2-player game. Change the game to be played in
# the UCTPlayGame() function at the bottom of the code.
#
# Written by Peter Cowling, Ed Powley, Daniel Whitehouse (University of York, UK) September 2012.
#
# Licence is granted to freely use and distribute for any sensible/legal purpose so long as this comment
# remains in any distributed code.
#
# For more information about Monte Carlo Tree Search check out our web site at www.mcts.ai

from math import *
import copy
# import logging
import random
import time
import sys, traceback
import itertools
from enum import Enum
from fireplace import cards

from fireplace.deck import Deck
from hearthstone.enums import CardType, Rarity, PlayState
from fireplace.game import Game
from fireplace.player import Player

from hearthEnv import *


# logging.getLogger().setLevel(logging.DEBUG)



UCTK = 0.05

class Node:
	""" A node in the game tree. Note wins is always from the viewpoint of playerJustMoved.
        Crashes if state not specified.
    """

	def __init__(self, move=None, parent=None, state=None):
		self.move = move  # the move that got us to this node - "None" for the root node
		self.parentNode = parent  # "None" for the root node
		self.childNodes = []
		self.wins = 0
		self.visits = 0
		if move and (move[0] == Move.end_turn):
			self.untriedMoves = []
		else:
			self.untriedMoves = state.__getMoves()  # future child nodes
		self.playerJustMoved = state.playerJustMoved  # the only part of the state that the Node needs later

	def UCTSelectChild(self):
		""" Use the UCB1 formula to select a child node. Often a constant UCTK is applied so we have
            lambda c: c.wins/c.visits + UCTK * sqrt(2*log(self.visits)/c.visits to vary the amount of
            exploration versus exploitation.
        """
		s = sorted(self.childNodes, key=lambda c: c.wins / c.visits + UCTK * sqrt(2 * log(self.visits) / c.visits))[-1]
		return s

	def AddChild(self, m, s):
		""" Remove m from untriedMoves and add a new child node for this move.
            Return the added child node
        """
		n = Node(move=m, parent=self, state=s)
		self.untriedMoves.remove(m)
		self.childNodes.append(n)
		return n

	def Update(self, result):
		""" Update this node - one additional visit and result additional wins. result must be from the viewpoint of playerJustMoved.
        """
		self.visits += 1
		self.wins += result

	def __repr__(self):
		return "[M:" + str(self.move) + " W/V:" + str(self.wins) + "/" + str(self.visits) + " U:" + str(
			self.untriedMoves) + "]"

	def TreeToString(self, indent):
		s = self.IndentString(indent) + str(self)
		for c in sorted(self.childNodes, key=lambda c: c.visits):
			s += c.TreeToString(indent + 1)
		return s

	def IndentString(self, indent):
		s = "\n"
		for i in range(1, indent + 1):
			s += "| "
		return s

	def ChildrenToString(self):
		s = ""
		for c in sorted(self.childNodes, key=lambda c: c.visits):
			s += str(c) + "\n"
		return s[:-2]

	# def clean(self):
	# for child in self.childNodes:
	#    child.clean()
	# del self.childNodes
	# del self.parentNode
	# del self.untriedMoves


def UCT(rootstate, seconds, verbose=False):
	""" Conduct a UCT search for seconds starting from rootstate.
        Return the best move from the rootstate.
        Assumes 2 alternating players (player 1 starts), with game results in the range [0.0, 1.0]."""
	rootnode = Node(state=rootstate)

	iterations = 0
	future = time.time() + seconds
	while time.time() < future:
		node = rootnode
		state = rootstate.clone()

		# Select
		while node.untriedMoves == [] and node.childNodes != []:  # node is fully expanded and non-terminal
			node = node.UCTSelectChild()
			state.__doMove(node.move)

		# Expand
		if node.untriedMoves != []:  # if we can expand (i.e. state/node is non-terminal)
			m = random.choice(node.untriedMoves)
			state.__doMove(m)
			node = node.AddChild(m, state)  # add child and descend tree

		# Rollout - this can often be made orders of magnitude quicker using a state.GetRandomMove() function
		while state.__getMoves() != []:  # while state is non-terminal
			state.__doMove(state.__fastGetRandomMove())
		# Backpropagate
		result = state.getResult(
				node.playerJustMoved)
		while node != None:  # backpropagate from the expanded node and work back to the root node
			node.Update(result)  # state is terminal. Update node with result from POV of node.playerJustMoved
			node = node.parentNode

		iterations += 1

		if iterations % 1000 == 0:
			print("Iteration #" + str(iterations) + "...")

	# Output some information about the tree - can be omitted
	if (verbose):
		print(rootnode.TreeToString(0))
	else:
		pass
		# print(rootnode.ChildrenToString())

	print("Iterations: " + str(iterations) + "\n")

	bestmove = sorted(rootnode.childNodes, key=lambda c: c.visits)[-1].move  # return the move that was most visited
	# rootnode.clean()
	# del rootnode

	return bestmove


def UCTPlayGame():
	""" Play a sample game between two UCT players where each player gets a different number
        of UCT iterations (= simulations = tree nodes).
    """
	state = HearthEnv()
	while (state.__getMoves() != []):
		try:
			m = UCT(rootstate=state, seconds=1, verbose=False)
		except:
			traceback.print_exc()
			sys.exit()
		# print("Best Move: " + str(m) + "\n")
		state.__doMove(m)

		print()

	if state.getResult(state.playerJustMoved) > 0.1:
		print("Player " + str(state.playerJustMoved) + " wins!")
	elif state.getResult(state.playerJustMoved) == 0:
		print("Player " + str(3 - state.playerJustMoved) + " wins!")
	else:
		print("Nobody wins!")


if __name__ == "__main__":
	""" Play a single game to the end using UCT for both players. 
    """
	start = time.time()
	UCTPlayGame()
	print(time.time() - start)

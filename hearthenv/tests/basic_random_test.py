from hearthenv.envs.hearthEnv import HearthEnv
import time

env = HearthEnv()

turns = 0
games = 0

done = False

start_time = time.time()
start_check = time.time()
playerToMove = 1
while start_check - start_time < 20 * 60:

	while not done:
		action = env.get_random_action()
		_, _, done, info = env.step(action)
		turns += 1
	env.reset()
	done = False
	start_check = time.time()
	turns = 0
	games += 1
	if games % 100 == 0:
		total_time = time.time() - start_time
		print("Playing {} games took {} seconds, an average of {} g/s".format(games,total_time, games/total_time))
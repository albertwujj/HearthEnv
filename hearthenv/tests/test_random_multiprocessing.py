from hearthenv.envs.hearthEnv import HearthEnv
from hearthenv.vec_envs.subproc_vec_env_hs import SubprocVecEnvHS
import time
import numpy as np

num_envs = 200
env = SubprocVecEnvHS([HearthEnv for i in range(num_envs)])
num_turns = 100

steps = 0
games = 0
i = 0

done = False

start_time = time.time()
start_check = time.time()
playerToMove = 1
while start_check - start_time < 20 * 60:

	turns = 0
	while turns < num_turns:
		actions = env.get_random_action()
		_, _, dones, infos = env.step(actions)
		steps += num_envs
		turns += 1

	env.reset()
	done = False
	start_check = time.time()
	games += num_envs
	i += 1

	total_time = time.time() - start_time
	print("Playing {} steps took {} seconds, an average of {} steps/s".format(steps,total_time, steps/total_time))
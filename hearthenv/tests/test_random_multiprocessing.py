from hearthenv.envs.hearthEnv import HearthEnv
from hearthenv.vec_envs.subproc_vec_env_hs import SubprocVecEnvHS
import time
import numpy as np
import multiprocessing as mp

# if # of subprocesses is equal to just # of cores each subprocess may only utilize about 50% of a core
# optimal num_ens will depend on machine
num_envs = mp.cpu_count() * 25
print("Num envs == {}".format(num_envs))
env = SubprocVecEnvHS([HearthEnv for i in range(num_envs)])
num_turns = 100

steps = 0
games = 0
i = 0

done = False

start_time = time.time()
start_check = start_time
total_time = 0
steps_prev = 0
playerToMove = 1
while start_check - start_time < 60 * 60:

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

	if i % 1 == 0:
		time_last = time.time() - total_time - start_time
		total_time = time.time() - start_time
		steps_last = steps - steps_prev
		print("Playing {} steps took {} seconds, an average of {} steps/s"
			  .format(steps_last, time_last, steps_last / time_last))
		print("TOTAL: Playing {} steps took {} seconds, an average of {} steps/s".format(steps,total_time, steps/total_time))
		print()
		steps_prev = steps
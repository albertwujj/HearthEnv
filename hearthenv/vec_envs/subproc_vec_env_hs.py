import numpy as np
from baselines.common.vec_env.subproc_vec_env import SubprocVecEnv
from baselines.common.tile_images import tile_images

# a version of subproc_vec_env (which spawns envs in subprocesses for parallel execution) that supports
# HearthEnv methods




class SubprocVecEnvHS(SubprocVecEnv):

    def get_possible_actions(self):
        for remote in self.remotes:
            remote.send(('get_possible_actions', None))
        return [remote.recv() for remote in self.remotes]

    def get_random_action(self):
        for remote in self.remotes:
            remote.send(('get_random_action', None))
        return [remote.recv() for remote in self.remotes]

    def render(self, mode='human'):
        for pipe in self.remotes:
            pipe.send(('render', None))
        imgs = [pipe.recv() for pipe in self.remotes]
        bigimg = tile_images(imgs)
        if mode == 'human':
            import cv2
            cv2.imshow('vecenv', bigimg[:,:,::-1])
            cv2.waitKey(1)
        elif mode == 'rgb_array':
            return bigimg
        else:
            raise NotImplementedError
import numpy as np
from baselines.common.vec_env.subproc_vec_env import SubprocVecEnv
from baselines.common.tile_images import tile_images


def worker(remote, parent_remote, env_fn_wrapper):
    parent_remote.close()
    env = env_fn_wrapper.x()
    while True:
        cmd, data = remote.recv()
        if cmd == 'step':
            ob, reward, done, info = env.step(data)
            if done:
                ob = env.reset()
            remote.send((ob, reward, done, info))
        elif cmd == 'reset':
            ob = env.reset()
            remote.send(ob)
        elif cmd == 'render':
            remote.send(env.render(mode='rgb_array'))
        elif cmd == 'close':
            remote.close()
            break
        elif cmd == 'get_spaces':
            remote.send((env.observation_space, env.action_space))
        elif cmd == 'get_random_action':
            action = env.get_random_action()
            remote.send(action)
        elif cmd == 'get_possible_actions':
            possible_actions = env.get_possible_actions()
            remote.send(possible_actions)
        else:
            raise NotImplementedError


class SubprocVecEnvHS(SubprocVecEnv):

    def get_possible_actions(self):
        for remote in self.remotes:
            remote.send(('get_possible_actions', None))
        return np.stack([remote.recv() for remote in self.remotes])

    def get_random_action(self):
        for remote in self.remotes:
            remote.send(('get_random_action', None))
        return np.stack([remote.recv() for remote in self.remotes])

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
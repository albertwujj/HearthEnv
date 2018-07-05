from hearthEnv import HearthEnv

def make_envs(env_method, count):
    return [env_method for _ in range(count)]


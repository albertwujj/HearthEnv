from hearthEnv import HearthEnv

def make_envs(count):
    return [make_env() for _ in range(count)]

def make_env():
    def _thunk():
        return HearthEnv()

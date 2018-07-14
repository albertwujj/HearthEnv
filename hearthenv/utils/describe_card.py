from hearthenv.utils.color_card import *
from hearthenv.utils.misc import *
from fireplace.card import Minion

def hand(*cards):

    ret = []
    for i, c in enumerate(cards):
        specials = []
        if type(c) is Minion:
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
            ret.append(p(*color_powered(c), fg.blue + str(c.cost) + fg.rs, fg.li_yellow + str(c.atk) + fg.rs + "/" + fg.red + str(c.health) + fg.rs, *specials))
        else:
            ret.append(p(*color_powered(c), fg.blue + str(c.cost) + fg.rs))
    return ret
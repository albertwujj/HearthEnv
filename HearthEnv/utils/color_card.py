from hearthstone.enums import Race
from sty import fg, bg, ef, rs

race_to_color = {Race.BEAST: fg.green, Race.DEMON: fg.magenta, Race.DRAGON: fg.red, Race.ELEMENTAL: fg.yellow, Race.MURLOC : fg.cyan,
				 Race.PIRATE: fg.blue, Race.TOTEM: fg.black }
# unused
def color_race(*card):
	""" colors cards according to their in-game race
	"""
	ret = []
	for i in card:
		if hasattr(i, "race") and i.race in race_to_color:
			ret.append("" + race_to_color[i.race] + str(i) + fg.rs)
		else:

			ret.append(str(i))
	return ret

def color_powered(*cards):
	""" colors cards if they are "powered up" (yellow in hand in official Hearthstone)
	"""
	ret = []
	for i in cards:
		if i.powered_up:
			ret.append(fg.li_yellow + str(i) + fg.rs)
		else:
			ret.append(str(i))
	return ret

def color_can_attack(*cards):
	""" colors cards green if they are can attack
	"""
	ret = []
	for i in cards:
		if i.can_attack:
			ret.append(fg.green + str(i) + fg.rs)
		else:
			ret.append(str(i))
	return ret


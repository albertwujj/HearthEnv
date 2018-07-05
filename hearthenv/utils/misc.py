def p(*tokens, s=" ", last=False):
	""" formats tokens into a string for printing
	"""
	ret = ""
	if last:
		for t in tokens:
			ret += str(t) + s
	else:
		for t in tokens[:-1]:
			ret += str(t) + s
		if len(tokens) > 0:
			ret += str(tokens[-1])

	return ret

def indice_subsets(s):
	""" gets all index subsets of an iterable
	"""
	n= len(s)
	i = 0
	subsets = []
	for i in range(1 << n):
		subset = []
		for j in range(n):
			if i & (1 << j):
				subset.append(j)
		subsets.append(subset)
	return subsets


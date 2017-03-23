import numpy as np
from Cello_scorer import circ_list
import scipy 
from scipy.optimize import least_squares

# Affects k
def change_rbs(rprt,target):
	lower_bound,upper_bound = does_signal_match(rprt)

	rpr = rprt[1]
	x = target['K']/rpr['K']
	rpr['K'] = rpr['K'] * x

	# Signal matching component
	on_threshold = threshold(rpr,rpr['ymin']*2)
	off_threshold = threshold(rpr,rpr['ymax']/2)
	thresholds = [on_threshold,off_threshold]
	if not (min(thresholds) < lower_bound and max(thresholds) > upper_bound):
		rpr['K'] = rpr['K']/x # Now it's @ the K it was originally

		if min(thresholds) < lower_bound:
			on_threshold = threshold(rpr,rpr['ymin']*2)
			off_threshold = threshold(rpr,rpr['ymax']/2)
			real_thresholds = [on_threshold, off_threshold] 

			lower_bound_k = lower_bound/real_thresholds[thresholds.indexof(min(thresholds))]
			x = (lower_bound_k + 0.01)/rpr['K']
		else:
			on_threshold = threshold(rpr,rpr['ymin']*2)
			off_threshold = threshold(rpr,rpr['ymax']/2)
			real_thresholds = [on_threshold, off_threshold] 

			upper_bound_k = upper_bound/real_thresholds[thresholds.indexof(max(thresholds))]
			x = (upper_bound_k - 0.01)/rpr['K']

		rpr['K'] = rpr['K']*x
	
	# Change thresholds 
	rpr['on_threshold'] = threshold(rpr,rpr['ymin']*2)
	rpr['off_threshold'] = threshold(rpr,rpr['ymax']/2)

	if x == 1 or not np.isfinite(x) or x == 0:
		return rpr, ()
	elif x > 1:
		return rpr, ('weaker_rbs', 1/x)
	else:
		return rpr, ('stronger_rbs', x)

# Affects n
def change_slope(rprt,target):
	lower_bound,upper_bound = does_signal_match(rprt)

	rpr = rprt[1]

	x = target['n']/rpr['n']
	rpr['n'] = rpr['n'] * x

	# Signal matching component, not sure how to get the ideal new n value, b/c you can't rearrange threshold equation for n
	on_threshold = threshold(rpr,rpr['ymin']*2)
	off_threshold = threshold(rpr,rpr['ymax']/2)
	thresholds = [on_threshold,off_threshold]
	if not (min(thresholds) < lower_bound and max(thresholds) > upper_bound):
		rpr['n'] = rpr['n']/x # Now it's @ the n it was originally

		if min(thresholds) < lower_bound:
			lower_bound_n = lower_bound #/ ADD SOMETHING HERE? Basically lower_bound < threshold. For K you could just divide, but you can't do the same for n?? plz help
			x = (lower_bound_n + 0.01)/rpr['K']
		else:
			upper_bound_n = upper_bound/thresholds.indexof(max(thresholds))
			x = (upper_bound_n - 0.01)/rpr['n']

		rpr['n'] = rpr['n']*x

	# Change thresholds 
	rpr['on_threshold'] = threshold(rpr,rpr['ymin']*2)
	rpr['off_threshold'] = threshold(rpr,rpr['ymax']/2)

	if x > 1.05:
		x = 1.05

	if x == 1 or not np.isfinite(x) or x == 0:
		return rpr, ()
	elif x > 1:
		return rpr, ('increase_slope', x)
	else:
		return rpr, ('decrease_slope', 1/x)

def change_promoter(rprt,target):
	lower_bound,upper_bound = does_signal_match(rprt)

	rpr = rprt[1]

	ymin_x = target['ymin']/rpr['ymin']
	ymax_x = target['ymax']/rpr['ymax']

	if np.all(np.isfinite([ymin_x,ymax_x])):
		return rpr, ()

	x = np.random.uniform(low=ymin_x,high=ymax_x)

	if x == 1 or not np.isfinite(x) or x == 0:
		return rpr, ()
	elif x > 1:
		rpr['ymax'] = rpr['ymax']*x
		rpr['ymin']= rpr['ymin']*x
		return rpr, ('stronger_promoter', x)
	else:
		rpr['ymax'] = rpr['ymax']/x
		rpr['ymin']= rpr['ymin']/x
		return rpr, ('weaker_promoter', 1/x)

def stretch(rprt,target):
	lower_bound,upper_bound = does_signal_match(rprt)

	rpr = rprt[1]

	ymin_x = target['ymin']/rpr['ymin']
	ymax_x = target['ymax']/rpr['ymax']

	x = np.random.uniform(low=0,high=1)
	if x > 1.5:
		x = 1.5

	rpr['ymax'] = rpr['ymax']*x
	rpr['ymin'] = rpr['ymin']/x

	return rpr,('stretch', x)

def y(x,ymax, ymin, n, K, **kwargs):
	return ymin + (ymax - ymin)/(1 + (x/K)**n)


threshold = lambda gate,y: gate['K'] * ((gate['ymax'] - y)/(y - gate['ymin']) )**(1/gate['n'])

''' Check whether the output matches the input of one gate '''
def signal_bounds(out,inp,val): # Attempting to model this function after Figure 5 in the Yaman paper (suggested reading), feel free to check it over and make sure my logic is sound bc i'm not sure
	noise = 0.001 # Change this value, not sure what an appropriate noise component is

	try:
		inp_on = (threshold(inp,inp['ymin']*2), inp['ymin']*2)
		inp_off = (threshold(inp,inp['ymax']/2), inp['ymax']/2)
	except KeyError:
		inp_on = (inp['ymax'],0)
		inp_off = (inp['ymin'],0)

	out_on = (threshold(out,out['ymin']*2), out['ymin']*2)
	out_off = (threshold(out,out['ymax']/2), out['ymax']/2)

	c = min([inp_on,inp_off], key = lambda t: t[1])[1]
	d = max([inp_on,inp_off], key = lambda t: t[1])[1]
	e = min([out_on,out_off], key = lambda t: t[0])[0]
	f = max([out_on,out_off], key = lambda t: t[0])[0]

	# (c+noise < e < f < d-noise)
	# e > c+noise
	# f < d-noise
	# c < e
	# d > f

	if val == 1: # Case 1: current rpr is the output
		return (c+noise, d-noise)
	elif val == 2: # Case 2: current rpr is the input
		return (f,e)

''' Get lower and upper bounds for the on threshold and off threshold of a particular gate '''
def does_signal_match(rpr):
	affected_gates = [gates for gate_id,gates in circ_list if rpr[0] in gates]
	bounds = []
	for comp in affected_gates:
		print(comp)
		out = dict_of_circuit[comp[0]] if comp[0] != rpr[0] else rpr[1]
		val = 1 if out == rpr[1] else 2

		for inp in comp[1:]:
			inp = dict_of_circuit[inp] if inp != rpr[0] else rpr[1]

			if out is not rpr[1] and inp is not rpr[1]:
				continue

			bounds += (signal_bounds(out,inp,val),)

	zipped_bounds = list(zip(*bounds)) # Turns list like [(1,5),(5,10),(2,7)] ---> [(1, 5, 2), (5, 10, 7)]
	lower_bound, upper_bound = max(zipped_bounds[0]), min(zipped_bounds[1]) # min(on_threshold,off_threshold) < lower_bound, the other one has to be > upper_bound 
	return (lower_bound,upper_bound)








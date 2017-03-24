import numpy as np
from Cello_scorer import circ_list
import scipy 
from scipy.optimize import minimize
import copy

# Affects k
def change_rbs(rprt,target,dict_of_circuit):
	lower_bound,upper_bound = does_signal_match(rprt,dict_of_circuit) # min(on_threshold,off_threshold) < lower_bound, the other one has to be > upper_bound ll

	rpr = rprt[1]

	init_x = target['K']/rpr['K']
	x = find_optimal_x(rpr, target, 'K', 0, upper_bound, lower_bound, init_x)

	rpr['K'] = rpr['K'] * x

	# Change thresholds 
	rpr['on_threshold'] = on_threshold(rpr)
	rpr['off_threshold'] = off_threshold(rpr)

	if x == 1 or not np.isfinite(x) or x == 0:
		return rprt, ()
	elif x > 1:
		return rprt, ('weaker_rbs', 1/x)
	else:
		return rprt, ('stronger_rbs', x)

# Affects n
def change_slope(rprt,target,dict_of_circuit):
	lower_bound,upper_bound = does_signal_match(rprt,dict_of_circuit)

	rpr = rprt[1]

	init_x = target['n']/rpr['n']
	x = find_optimal_x(rpr, target, 'n', 0, upper_bound, lower_bound, init_x)

	rpr['n'] = rpr['n'] * x

	# Change thresholds 
	rpr['on_threshold'] = on_threshold(rpr)
	rpr['off_threshold'] = off_threshold(rpr)

	if x > 1.05:
		x = 1.05

	if x == 1 or not np.isfinite(x) or x == 0:
		return rprt, ()
	elif x > 1:
		return rprt, ('increase_slope', x)
	else:
		return rprt, ('decrease_slope', 1/x)

def change_promoter(rprt,target,dict_of_circuit):
	lower_bound,upper_bound = does_signal_match(rprt,dict_of_circuit)

	rpr = rprt[1]

	ymin_x = target['ymin']/rpr['ymin']
	ymax_x = target['ymax']/rpr['ymax']

	init_x = (ymin_x + ymax_x)/2
	x = find_optimal_x(rpr, target, ('ymax','ymin'), 0, upper_bound, lower_bound, init_x)

	# Change thresholds 
	rpr['on_threshold'] = on_threshold(rpr)
	rpr['off_threshold'] = off_threshold(rpr)

	if x == 1 or not np.isfinite(x) or x == 0:
		return rpr, ()
	elif x > 1:
		rpr['ymax'] = rpr['ymax']*x
		rpr['ymin']= rpr['ymin']*x
		return rprt, ('stronger_promoter', x)
	else:
		rpr['ymax'] = rpr['ymax']/x
		rpr['ymin']= rpr['ymin']/x
		return rprt, ('weaker_promoter', 1/x)

def stretch(rprt,target,dict_of_circuit):
	lower_bound,upper_bound = does_signal_match(rprt,dict_of_circuit)

	rpr = rprt[1]

	ymin_x = target['ymin']/rpr['ymin']
	ymax_x = target['ymax']/rpr['ymax']

	init_x = (ymin_x + ymax_x)/2
	x = find_optimal_x(rpr, target, ('ymax','ymin'), 1, upper_bound, lower_bound, init_x)

	# Change thresholds 
	rpr['on_threshold'] = on_threshold(rpr)
	rpr['off_threshold'] = off_threshold(rpr)

	if x > 1.5:
		x = 1.5

	rpr['ymax'] = rpr['ymax']*x
	rpr['ymin'] = rpr['ymin']/x

	return rprt,('stretch', x)

def y(x,ymax, ymin, n, K, **kwargs):
	return ymin + (ymax - ymin)/(1 + (x/K)**n)


def on_threshold(gate, x=1,param=None,stretch=0):
	if param is not None and len(param) == 1:
		gate[param] = gate[param]*x
	else:
		if stretch:
			gate['ymax'] = gate['ymax'] * x
			gate['ymin'] = gate['ymin'] / x
		else:
			gate['ymax'] = gate['ymax'] * x
			gate['ymin'] = gate['ymin'] * x

	return gate['K'] * ((gate['ymax'] - gate['ymin']*2)/(gate['ymin']*2 - gate['ymin']) )**(1/gate['n'])

def off_threshold(gate, x=1,param=None,stretch=0):
	if param is not None and len(param) == 1:
		gate[param] = gate[param]*x
	else:
		if stretch:
			gate['ymax'] = gate['ymax'] * x
			gate['ymin'] = gate['ymin'] / x
		else:
			gate['ymax'] = gate['ymax'] * x
			gate['ymin'] = gate['ymin'] * x


	return gate['K'] * ((gate['ymax'] - gate['ymax']/2)/(gate['ymax']/2 - gate['ymin']) )**(1/gate['n'])

''' Check whether the output matches the input of one gate '''
def signal_bounds(out,inp,val): # Attempting to model this function after Figure 5 in the Yaman paper (suggested reading), feel free to check it over and make sure my logic is sound bc i'm not sure
	noise = 0.001 # Change this value, not sure what an appropriate noise component is

	try:
		inp_on = (on_threshold(inp), inp['ymin']*2)
		inp_off = (off_threshold(inp), inp['ymax']/2)
	except KeyError:
		inp_on = (inp['ymax'],0)
		inp_off = (inp['ymin'],0)

	out_on = (on_threshold(out), out['ymin']*2)
	out_off = (off_threshold(out), out['ymax']/2)

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
def does_signal_match(rpr,dict_of_circuit):
	affected_gates = [gates for gate_id,gates in circ_list if rpr[0] in gates]
	bounds = []
	for comp in affected_gates:
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


def func(x,rpr,target,param,stretch):
	target_vals = []
	new_vals = []

	if not stretch:
		for p in param: # param will either be a string (ex: 'n' or 'k') or a tuple (ex: ('ymax','ymin')) 
			target_vals += [target[p]]
			new_vals += [rpr[p] * x[0]]
	else:
		new_vals += [rpr['ymax']*x[0]]
		new_vals += [rpr['ymin']/x[0]]

		target_vals += [target['ymax']*x[0]]
		target_vals += [target['ymin']/x[0]]


	return abs(np.array(target_vals) - np.array(new_vals))


# Finds the optimal x value that allows the rpr parameter to get as close to the target as possible w/o changing how it affects the other ones in the circuit
def find_optimal_x(rpr, target, param, stretch, upper_bound, lower_bound, init_x=1):
	cons = ({'type': 'ineq', 'fun': lambda x, rpr, lower_bound, param, stretch: min(on_threshold(copy.deepcopy(rpr),x[0],param,stretch),off_threshold(copy.deepcopy(rpr),x[0],param,stretch)) - lower_bound, 'args': (rpr, lower_bound, param, stretch)},
			{'type': 'ineq', 'fun': lambda x, rpr, upper_bound, param, stretch: upper_bound - max(on_threshold(copy.deepcopy(rpr),x[0],param,stretch),off_threshold(copy.deepcopy(rpr),x[0],param,stretch)), 'args': (rpr, upper_bound, param, stretch)},
			{'type': 'ineq', 'fun': lambda x: x})

	res = minimize(func,np.array([init_x]), args=(rpr,target,param,stretch), constraints=cons, method='COBYLA')

	return res.x[0]













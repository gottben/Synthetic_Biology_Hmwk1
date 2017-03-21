import numpy as np
from scipy.optimize import minimize
import pickle

# Affects n
def increase_slope(rpr,x):
	if x > 1.05:
		x = 1.05

	rpr[2] = rpr[2] * x

def decrease_slope(rpr,x):
	if x > 1.05:
		x = 1.05

	rpr[2] = rpr[2]/x

# Affects ymax and ymin
def stretchssss(rpr,x):
	if x > 1.5:
		x = 1.5

	rpr[0] = rpr[0]*x
	rpr[1]= rpr[1]/x

def stronger_promoter(rpr,x):
	rpr[0] = rpr[0]*x
	rpr[1]= rpr[1]*x
def weaker_promoter(rpr,x):
	rpr[0] = rpr[0]/x
	rpr[1]= rpr[1]/x

# Affects k
def stronger_rbs(rpr,x): rpr[3] = rpr[3]/x
def weaker_rbs(rpr,x): rpr[3] = rpr[3]*x

def change_rbs(rpr,target):
	x = target[3]/rpr[3]
	rpr[3] = rpr[3] * x

	if x == 1 or not np.isfinite(x) or x == 0:
		return rpr, ()
	elif x > 1:
		return rpr, ('weaker_rbs', 1/x)
	else:
		return rpr, ('stronger_rbs', x)

def change_slope(rpr,target):
	x = target[2]/rpr[2]
	if x > 1.05:
		x = 1.05

	rpr[2] = rpr[2] * x

	if x == 1 or not np.isfinite(x) or x == 0:
		return rpr, ()
	elif x > 1:
		return rpr, ('increase_slope', x)
	else:
		return rpr, ('decrease_slope', 1/x)

# TODO: Change the way x is chosen for this, rn I just choose the perfect x value for ymin, maybe choose randomly which one to optimize for?
def change_promoter(rpr,target):
	ymin_x = target[1]/rpr[1]
	ymax_x = target[0]/rpr[0]

	if np.all(np.isfinite([ymin_x,ymax_x])):
		return rpr, ()

	x = np.random.uniform(low=0,high=1)

	if x == 1 or not np.isfinite(x) or x == 0:
		return rpr, ()
	elif x > 1:
		stronger_promoter(rpr,x)
		return rpr, ('stronger_promoter', x)
	else:
		weaker_promoter(rpr,x)
		return rpr, ('weaker_promoter', 1/x)

# TODO: Change way I choose the x
def stretch(rpr,target):
	ymin_x = target[0]/rpr[0]
	ymax_x = target[1]/rpr[1]

	x = np.random.uniform(low=0,high=1)

	stretchssss(rpr,x)
	return rpr,('stretch', x)




x1 = np.array([0.0013, 4.4, 0.0013, 4.4]) #0101
x2 = np.array([0.025,0.025,0.31,0.31]) #0011

# ymax ymin n k
y2_vals = np.array([3.9,0.01,4,0.03]) #0100
y1_vals = np.array([1.3,0.003,2.9,0.01]) #1010


vals0 = []
vals0.extend(y2_vals)
vals0.extend(y1_vals)

def y(x,ymax, ymin, n, k):
	return ymin + (ymax - ymin)/(1 + (x/k)**n)


# This is the equation in the example in the HW.
def func(vals):
	y1 = y(x1,*vals[4:])
	y2 = y(y1 + x2, *vals[:4])
	ONmin = y2[1]
	OFFmax = np.amax(y2[[0,2,3]])

	return -1*ONmin/OFFmax # In order to maximize, you multiply result by -1

def choose_operations(target):
	init = [y2_vals, y1_vals]
	ops = [change_slope, stretch, change_promoter, change_rbs]

	weights = [0.15, 0.15, 0.35, 0.35]

	chosen = [[],[]]

	best_rprs = init[:]
	best_score = -1*func(np.concatenate((y2_vals,y1_vals), axis=0))
	print(best_score)


	for idx,rpr in enumerate(init[:]):
		for i in range(1,100000):
			current_target = target[idx]
			op = np.random.choice(ops, p=weights)

			pot_rpr, current_chosen = op(list(best_rprs[idx]),current_target)
			new_score = -1*func(np.concatenate(tuple([x if idy != idx else pot_rpr for idy,x in enumerate(best_rprs)]), axis=0))

			if new_score > best_score and np.isfinite(new_score) and np.all(np.isfinite(rpr)):
				print("Score:", new_score)
				print(current_chosen)

				best_rprs[idx] = pot_rpr
				print("Iterate:",best_rprs)
				chosen[idx].append(current_chosen)
				best_score = new_score

	return np.concatenate((best_rprs[0],best_rprs[1]),axis=0)




	

def main():
	#bounds = ((0,None),(0,None),(0,None),(0,None),(0,None),(0,None),(0,None),(0,None))
	#res = minimize(func, vals0, method='L-BFGS-B', bounds=bounds, options={'disp': False})
	#target = [res.x[:4],res.x[4:]]


	target = pickle.load( open( "save.p", "rb" ) )

	newvals = choose_operations(target)
	
	orig_score = -1*func(vals0)
	new_score = -1*func(newvals)

	print("Original score:", orig_score)
	print("New score:", new_score)
	print("Gain:", new_score/orig_score)


if __name__ == '__main__':
	main()








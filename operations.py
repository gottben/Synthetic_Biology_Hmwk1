import numpy as np

# Affects k
def change_rbs(rpr,target):
	x = target['K']/rpr['K']
	rpr['K'] = rpr['K'] * x

	if x == 1 or not np.isfinite(x) or x == 0:
		return rpr, ()
	elif x > 1:
		return rpr, ('weaker_rbs', 1/x)
	else:
		return rpr, ('stronger_rbs', x)

# Affects n
def change_slope(rpr,target):
	x = target['n']/rpr['n']
	if x > 1.05:
		x = 1.05

	if x == 1 or not np.isfinite(x) or x == 0:
		return rpr, ()
	elif x > 1:
		rpr['n'] = rpr['n'] * x
		return rpr, ('increase_slope', x)
	else:
		rpr['n'] = rpr['n'] / x
		return rpr, ('decrease_slope', 1/x)

# Never used???
def change_promoter(rpr,target):
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

def stretch(rpr,target):
	ymin_x = target['ymin']/rpr['ymin']
	ymax_x = target['ymax']/rpr['ymax']

	x = np.random.uniform(low=0,high=1)
	if x > 1.5:
		x = 1.5

	rpr['ymax'] = rpr['ymax']*x
	rpr['ymin']= rpr['ymin']/x

	return rpr,('stretch', x)



def y(x,ymax, ymin, n, k):
	return ymin + (ymax - ymin)/(1 + (x/k)**n)




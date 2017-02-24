import numpy as np

pTet = np.array([0.0013, 4.4, 0.0013, 4.4])
pLuxStar = np.array([0.025,0.025,0.31,0.31])

p1 = {'ymax':3.9, 'ymin':0.01, 'n':4,'k':0.03}
s1 = {'ymax':1.3,'ymin':0.003,'n':2.9,'k':0.01}

def y(rpr,x): return rpr['ymin'] + (rpr['ymax'] - rpr['ymin'])/(1 + (x/rpr['k'])**rpr['n'])

def stretch(rpr,x):
	if x > 1.5:
		x = 1.5

	rpr['ymax'] = rpr['ymax']*x
	rpr['ymin']= rpr['ymin']/x

def increase_slope(rpr,x):
	if x > 1.05:
		x = 1.05

	rpr['n'] = rpr['n'] * x

def decrease_slope(rpr,x):
	if x > 1.05:
		x = 1.05

	rpr['n'] = rpr['n']/x

def stronger_promoter(rpr,x):
	rpr['ymax'] = rpr['ymax']*x
	rpr['ymin']= rpr['ymin']*x

def weaker_promoter(rpr,x):
	rpr['ymax'] = rpr['ymax']/x
	rpr['ymin']= rpr['ymin']/x

def stronger_rbs(rpr,x): rpr['k'] = rpr['k']/x

def weaker_rbs(rpr,x): rpr['k'] = rpr['k']*x

def score():
	s1_column = y(s1,pTet)
	print("S1 score:", s1_column[0]/s1_column[1])
	p1_column = y(p1,(pLuxStar+s1_column))
	print("Circuit score:", p1_column[1]/p1_column[3], end="\n\n")
	return p1_column[1]/p1_column[3]

print("===Before===")
before = score()
stronger_promoter(s1,10**-5)

print("===After===")
after = score()

print("Gain:",after/before)




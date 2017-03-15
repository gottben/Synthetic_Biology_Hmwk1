import numpy as np
from scipy.optimize import minimize

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
	print('ONmin:', ONmin, 'OFFmax:', OFFmax, 'Score:', ONmin/OFFmax)

	return -1*ONmin/OFFmax # In order to maximize, you multiply result by -1

bounds = ((0,None),(0,None),(0,None),(0,None),(0,None),(0,None),(0,None),(0,None))

res = minimize(func, vals0, method='L-BFGS-B', bounds=bounds, options={'disp': True})

print("=====Original========")
print("Values:", vals0)
func(vals0)

print("=====After========")
print("Values:", res.x)
func(res.x)



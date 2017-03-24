pt_off = 0.0013
pt_on = 4.4

pb_off = 0.008
pb_on = 2.5

S1_min = 0.003
S1_max = 2.099
Sn = 2.6
Sk = 0.04

A1_min = 0.0722
A1_max = 3.68718
An = 1.6
Ak = 0.07

P3_min = 0.02
P3_max = 6.8
Pn = 4.2
Pk = 0.23

print(P3_min/0.46853764161394118)
print(P3_max*0.46853764161394118)

def equation(x1, x2, ymin, ymax, k, n):
    y = ymin + (ymax - ymin)/(1 + ((x1 + x2)/k)**n)
    return(y)

y1 = equation(pt_off, 0, S1_min, S1_max, Sk, Sn)
y2 = equation(pt_on, 0, S1_min, S1_max, Sk, Sn)
print(y1, y2)
y3 = equation(pb_off, 0, A1_min, A1_max, Ak, An)
y4 = equation(pb_on, 0, A1_min, A1_max, Ak, An)
print(y3, y4)
Py1 = equation(y2, y4, P3_min, P3_max, Pk, Pn)
Py2 = equation(y1, y3, P3_min, P3_max, Pk, Pn)
score = Py1/Py2

print(score)


print(" ")

l1 = equation(1, 3, P3_min, P3_max, Pk, Pn)
l2 = equation(1, 4, P3_min, P3_max, Pk, Pn)
l3 = equation(1, 0.3, P3_min, P3_max, Pk, Pn)
l4 = equation(1, 0.15, P3_min, P3_max, Pk, Pn)

print(l1, l2, l3, l4)

l1 = equation(2, 3, P3_min, P3_max, Pk, Pn)
l2 = equation(2, 4, P3_min, P3_max, Pk, Pn)
l3 = equation(2, 0.003, P3_min, P3_max, Pk, Pn)
l4 = equation(2, 0.0015, P3_min, P3_max, Pk, Pn)
print(l1, l2, l3, l4)

l1 = equation(0.005, 3, P3_min, P3_max, Pk, Pn)
l2 = equation(0.005, 4, P3_min, P3_max, Pk, Pn)
l3 = equation(0.005, 0.003, P3_min, P3_max, Pk, Pn)
l4 = equation(0.005, 0.0015, P3_min, P3_max, Pk, Pn)
print(l1, l2, l3, l4)

l1 = equation(0.072215286942, 0.00301032, 0.085372, 1.5930, Pk, Pn)
l2 = equation(0.0025, 4, P3_min, P3_max, Pk, Pn)
l3 = equation(0.0025, 0.003, P3_min, P3_max, Pk, Pn)
l4 = equation(0.0025, 0.0015, P3_min, P3_max, Pk, Pn)
print(l1, l2, l3, l4)




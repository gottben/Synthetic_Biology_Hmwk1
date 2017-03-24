import numpy as np
from scipy.optimize import minimize
import pickle
from Cello_scorer import *
from operations import *
import copy
from collections import defaultdict, Counter

# GENERAL NOTE: May or may not have overdone it w the deepcopy everywhere, but I just wanted to make sure that the original wouldn't get altered in any way
def choose_operations(dict_of_circuit, dict_of_target):
	init = [(gatename,values) for gatename,values in dict_of_circuit.items() if len(values) > 5]
	input_info = dict([(gatename,values) for gatename,values in dict_of_circuit.items() if len(values) <= 5])
	ops = [change_slope, stretch, change_promoter, change_rbs]

	weights = [0.19,0.01,0.4,0.4] # You want it to be more likely to choose change_promoter & change_rbs, so it's weighted more, we may want to play around w this

	chosen = defaultdict(list) # key = name of gate, values = list of operations performed on it & the x value

	best_rprs = copy.deepcopy(init) # Make sure that it's a copy of the list and not the actual list

	# Converting to parameter form and then to tuple form just to get the score lowkey seems like alot but it works for now
	best_params = create_parameters_array(dict_of_circuit)
	best_dict = convert_parameter_array_to_tuples(best_params, dict_of_circuit)
	best_score = -1*circuit_forward_prop(best_dict,copy.deepcopy(dict_of_circuit))

	for idx,rpr in enumerate(copy.deepcopy(init)):
		loop_counter = 0
		while is_converged and loop_counter <= 1000: # Replace w convergence fxn and while loop
			current_target = dict_of_target[rpr[0]] #rpr[0] is the gatename of the rpr that we're currently attempting to modify
			op = np.random.choice(ops, p=weights)

			pot_rpr, current_chosen = op(copy.deepcopy(best_rprs[idx]),current_target,dict_of_circuit)

			if current_chosen == ():
				continue

			pot_best_rprs = copy.deepcopy(best_rprs)
			pot_best_rprs[idx] = pot_rpr
			pot_best_dict = dict(pot_best_rprs)
			pot_best_dict.update(input_info)

			new_score = -1*circuit_forward_prop(pot_best_dict,None)

			if new_score > best_score + 10**-2 and np.isfinite(new_score):
				print("Score:", new_score)
				print(current_chosen)

				best_rprs[idx] = pot_rpr
				best_dict = pot_best_dict
				#print("Iterate:",best_rprs)
				chosen[rpr[0]].append(current_chosen)
				best_score = new_score

			loop_counter += 1

	print("Loop counter:", loop_counter)
	return best_rprs, chosen, best_score,best_dict

def is_converged(rpr,target):
	rpr_array = np.array([rpr['n'], rpr['k'], rpr['ymax'], rpr['ymin']])
	target_array = np.array([target['n'], target['k'], target['ymax'], target['ymin']])
	return np.all(abs(rpr_array-target_array) > 0.0000001)

def main():
	parameters = create_parameters_array(dict_of_circuit)
	num_of_gates = sum([1 for gatename,values in dict_of_circuit.items() if len(values) > 5])
	bounds = ((0,None),) * (num_of_gates*4) # You need a bound for every parameter, each gate has 4 parameters ~
	res = minimize(circuit_forward_prop, parameters, args=dict_of_circuit, method='L-BFGS-B', bounds=bounds, options={'disp': False})
	
	dict_of_target = convert_parameter_array_to_tuples(res.x,copy.deepcopy(dict_of_circuit))

	n = 2
	'''
	cleaned = pickle.load(open( "cleaned.p", "rb" ) )
	dict_of_target = cleaned
	'''

	newvals,chosen_operations,new_score, best_dict = choose_operations(dict_of_circuit, dict_of_target)
	orig_score= -1*circuit_forward_prop(dict_of_circuit,None)

	best_parameters = create_parameters_array(best_dict)
	new_score, new_dict_of_circuit = -1*circuit_forward_prop(best_parameters,None,flag=True)

	# Gets the first n repressors with the highest scores that have operations performed on them
	gate_scores = sorted([(key,val['score']) for key,val in new_dict_of_circuit.items() if len(val) > 5 and len(chosen_operations[key]) > 0], key = lambda t: t[1], reverse=True)	
	
	chosen_gates = []
	if len(gate_scores) > n:
		chosen_gates = gate_scores[:n]
	else:
		chosen_gates = gate_scores

	outfile = open('output.txt','w')
	new_best_dict = {}

	for gate,score in chosen_gates:
		new_best_dict.update({gate:best_dict_gate[gate]})

		print("Name of gate:", gate,file=outfile)
		print("Operations:",file=outfile)
		for operation in chosen_operations:
			print(operation,end=", ",file=outfile)

		print()


	best_parameters = create_parameters_array(new_best_dict)
	new_score, new_dict_of_circuit = -1*circuit_forward_prop(best_parameters,None,flag=True)


	print("Original score:", orig_score, file=outfile)
	print("New score:", new_score,file=outfile)
	print("Percentage Gain:", (new_score - orig_score)/(sum(new_score + orig_score) - orig_score), file=outfile)

if __name__ == '__main__':
	main()
	#dict_of_target = pickle.load( open( "save_dict.p", "rb" ) )





import numpy as np
from scipy.optimize import minimize
import pickle
from Cello_scorer import *
from operations import *
import copy
from collections import defaultdict

# GENERAL NOTE: May or may not have overdone it w the deepcopy everywhere,
# but I just wanted to make sure that the original wouldn't get altered in
# any way


def choose_operations(dict_of_circuit, dict_of_target):
    init = [(gatename, values)
            for gatename, values in dict_of_circuit.items() if len(values) > 5]
    input_info = dict([(gatename, values) for gatename,
                       values in dict_of_circuit.items() if len(values) <= 5])
    ops = [change_slope, stretch, change_promoter, change_rbs]

    # You want it to be more likely to choose change_promoter & change_rbs, so
    # it's weighted more, we may want to play around w this
    weights = [0.19, 0.01, 0.4, 0.4]

    # key = name of gate, values = list of operations performed on it & the x
    # value
    the_dict = deepcopy(dict_of_circuit)
    chosen = defaultdict(list)

    # Make sure that it's a copy of the list and not the actual list
    best_rprs = copy.deepcopy(init)

    # Converting to parameter form and then to tuple form just to get the
    # score lowkey seems like alot but it works for now
    best_params = create_parameters_array(the_dict)
    best_dict = convert_parameter_array_to_tuples(best_params, the_dict)
    best_score = -1 * \
        circuit_forward_prop(best_dict, copy.deepcopy(the_dict))

    for idx, rpr in enumerate(copy.deepcopy(init)):
        loop_counter = 0
        while is_converged and loop_counter <= 1000:  # Replace w convergence fxn and while loop
            # rpr[0] is the gatename of the rpr that we're currently attempting
            # to modify
            current_target = dict_of_target[rpr[0]]
            op = np.random.choice(ops, p=weights)

            pot_rpr, current_chosen = op(copy.deepcopy(
                best_rprs[idx]), current_target, the_dict)

            if current_chosen == ():
                continue

            pot_best_rprs = copy.deepcopy(best_rprs)
            pot_best_rprs[idx] = pot_rpr
            best_dict = dict(pot_best_rprs)
            best_dict.update(input_info)

            new_score = -1 * \
                circuit_forward_prop(best_dict, copy.deepcopy(the_dict))

            if new_score > best_score + 10**-4 and np.isfinite(new_score):
                print("Score:", new_score)
                print(current_chosen)

                best_rprs[idx] = pot_rpr
                # print("Iterate:",best_rprs)
                chosen[rpr[0]].append(current_chosen)
                best_score = new_score

            loop_counter += 1

    print("Loop counter:", loop_counter)
    return best_rprs, chosen, best_score


def is_converged(rpr, target):
    rpr_array = np.array([rpr['n'], rpr['k'], rpr['ymax'], rpr['ymin']])
    target_array = np.array(
        [target['n'], target['k'], target['ymax'], target['ymin']])
    print(abs(rpr_array - target_array))
    return np.all(abs(rpr_array - target_array) > 0.0000001)


def main():
    parameters = create_parameters_array(dict_of_circuit)
    num_of_gates = sum(
        [1 for gatename, values in dict_of_circuit.items() if len(values) > 5])
    # You need a bound for every parameter, each gate has 4 parameters ~
    bounds = ((0, None),) * (num_of_gates * 4)
    the_dict = deepcopy(dict_of_circuit)
    res = minimize(circuit_forward_prop, parameters, args=the_dict,
                   method='L-BFGS-B', bounds=bounds, options={'disp': False})

    dict_of_target = convert_parameter_array_to_tuples(
        res.x, copy.deepcopy(dict_of_circuit))

    '''
	cleaned = pickle.load(open( "s.p", "rb" ) )
	dict_of_target = cleaned
	'''

    newvals, chosen_operations, new_score = choose_operations(
        dict_of_circuit, dict_of_target)

    orig_score = -1 * circuit_forward_prop(dict_of_circuit, None)
    print("Original score:", orig_score)
    print("New score:", new_score)
    print("Gain:", new_score / orig_score)

if __name__ == '__main__':
    main()
    #dict_of_target = pickle.load( open( "save_dict.p", "rb" ) )

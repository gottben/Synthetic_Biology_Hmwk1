import requests
import os
import json
import numpy as np
from requests.auth import HTTPBasicAuth
from itertools import zip_longest
import re
from copy import deepcopy
import sys


UCF_file = 'gottbenn.UCF.json'
# verilog_file = sys.argv[1]
# num_of_repressors = sys.argv[3]

# Setup the username and password for Cello Authentication
username = 'gottbenn'
password = '123456789'
auth = HTTPBasicAuth(username, password)

# -----------------------------------------------------------#
# Create a circuit in Cello                                 #
# -----------------------------------------------------------#

# url = 'http://cellocad.org/submit'
# ID = username + '_Circuit'
# inputs = './resources/pycello/resources/Inputs.txt'
# outputs = './resources/pycello/resources/Outputs.txt'
# verilog_text = open(verilog_file, 'r').read()
# inputs_text = open(inputs, 'r').read()
# outputs_text = open(outputs, 'r').read()
# params = {'id': ID, 'verilog_text': verilog_text, 'input_promoter_data':
#           inputs_text, 'output_gene_data': outputs_text}
# req = requests.post(url, auth=auth, params=params)
# print(req.text)

# ------------------------------------------------#
#     UCF File processing                       #
# -------------------------------------------------#
with open(UCF_file) as initial_UCF:
    original_UCF = json.load(initial_UCF)

# We are going to grab all the repressor information from the UCF file.
gate_info = []
for info in original_UCF[23:44]:
    # save all the gate_names in an array.
    gate = []
    for key in info.keys():
        if key == 'gate_name':
            gate += [info[key]]
        elif key == 'variables':
            gate += [info[key]]
        elif key == 'parameters':
            gate += [info[key]]
    gate_info += [gate]

# ---------------------------------------------------------#
#       Grab the circuit info from cello             #
# ---------------------------------------------------------#
ID = username + '_Circuit'
filename = ID + '_A000' + '_logic' + '_circuit.txt'
url = 'http://cellocad.org/results/' + ID + '/' + filename
req = requests.get(url, auth=auth)
scores = open('scores.txt', 'w')
print(req.text, file=scores)
scores.close()


# ---------------------------------------------------------------#
#   Process the circuit info into python object       #
# ---------------------------------------------------------------#
gates_in_circuit = []
table = []
count = 1
input_ymax_ymin = []
a = 0
for line in open('scores.txt', 'r'):
    if ('Circuit_score' not in line) and (count != 0):
        table += [line]
        count += 1
    if 'Circuit_score' in line:
        circuit_score = line[15:25]
        count = 0
    if 'Gate' in line:
        index = line.index('Gate')
        gates_in_circuit += [(line[0: index].replace(" ", ""),
                              line[index + 5: index + 15])]
        a += 1
    if 'INPUT' in line:
        try:
            index = line.index(' : ')
            input_ymax_ymin += [(gates_in_circuit[a - 1][0],
                                 line[index + 4: index + 9])]
        except:
            pass
input_ymax_ymin = list(set(input_ymax_ymin))

# ----------------------------------------------------------------#
#  Get ride of any unnecessary string elements     #
# ----------------------------------------------------------------#
list_of_identities = []
for line in table:
    if 'OUTPUT' in line:
        identity = line[25:40] + line[45:60]
        identity = identity.replace("(", "")
        identity = identity.replace(")", "")
        identity = identity.replace(",", " ")
        list_of_identities += [identity.split()]
    elif 'NOR' in line:
        identity = line[25:40] + line[45:60]
        identity = identity.replace("(", "")
        identity = identity.replace(")", "")
        identity = identity.replace(",", " ")
        list_of_identities += [identity.split()]
    elif 'NOT' in line:
        identity = line[25:40] + line[45:60]
        identity = identity.replace("(", "")
        identity = identity.replace(")", "")
        identity = identity.replace(",", " ")
        list_of_identities += [identity.split()]
    elif 'INPUT' in line:
        identity = line[25:40] + line[45:60]
        identity = identity.replace("(", "")
        identity = identity.replace(")", "")
        identity = identity.replace(",", " ")
        list_of_identities += [identity.split()]

# -----------------------------------------------------------#
#  Put the circuit info into a dictionary                    #
# -----------------------------------------------------------#
dict_of_circuit = {}
for sub_list in list_of_identities:
    if sub_list[0] not in dict_of_circuit:
        dict_of_circuit[sub_list[0]] = {'ID': sub_list[1]}
    if len(sub_list) > 2:
        dict_of_circuit[sub_list[0]]['Inputs'] = sub_list[2: len(sub_list)]

for gate in gates_in_circuit:
    if gate[0] in dict_of_circuit:
        dict_of_circuit[gate[0]]['score'] = gate[1][0:len(gate[1]) - 2]

for key in dict_of_circuit.keys():
    for line in gate_info:
        if key in line:
            for element in line:
                if len(element) == 1:
                    dict_of_circuit[key]['on_threshold'] = element[
                        0]['on_threshold']
                    dict_of_circuit[key]['off_threshold'] = element[
                        0]['off_threshold']
                if len(element) == 4:
                    dict_of_circuit[key]['ymax'] = element[0]['value']
                    dict_of_circuit[key]['ymin'] = element[1]['value']
                    dict_of_circuit[key]['K'] = element[2]['value']
                    dict_of_circuit[key]['n'] = element[3]['value']

list_of_circ_elements = []
for key in dict_of_circuit.keys():
    dict_of_circuit[key]['ID'] = int(dict_of_circuit[key]['ID'])
    list_of_circ_elements += [(key, dict_of_circuit[key]['ID'])]


# ------------------------------------------------------#
# Add digital logic information to dict of circuit       #
# ------------------------------------------------------#
scores_txt = open('scores.txt').read()
p = re.compile(r'([0-1]{4})\s+(\w+)')
matches = re.findall(p, scores_txt)
info = [(name, {'logic': [int(d) for d in logic]}) for logic, name in matches]
[dict_of_circuit[t[0]].update(t[1]) for t in info]

# ------------------------------------------------------#
# Add the input ymax and ymin to dict       #
# ------------------------------------------------------#

d = {}
for k, v in input_ymax_ymin:
    d.setdefault(k, [k]). append(float(v))

b = [v for v in d.values()]
for item in b:
    if item[1] > item[2]:
        dict_of_circuit[item[0]]['ymax'] = item[1]
        dict_of_circuit[item[0]]['ymin'] = item[2]
    else:
        dict_of_circuit[item[0]]['ymax'] = item[2]
        dict_of_circuit[item[0]]['ymin'] = item[1]

# ----------------------------------------------------- #
# Convert string values to float values       #
# ----------------------------------------------------- #
for key in dict_of_circuit.keys():
    dict_of_circuit[key]['score'] = float(dict_of_circuit[key]['score'])
    try:
        dict_of_circuit[key]['ymax'] = float(dict_of_circuit[key]['ymax'])
        dict_of_circuit[key]['ymin'] = float(dict_of_circuit[key]['ymin'])
        dict_of_circuit[key]['Inputs'] = list(
            map(int, dict_of_circuit[key]['Inputs']))
        dict_of_circuit[key]['on_threshold'] = float(
            dict_of_circuit[key]['on_threshold'])
        dict_of_circuit[key]['K'] = float(dict_of_circuit[key]['K'])
        dict_of_circuit[key]['off_threshold'] = float(
            dict_of_circuit[key]['off_threshold'])
        dict_of_circuit[key]['n'] = float(dict_of_circuit[key]['n'])
    except:
        # dummy variable to make the except statement happy.
        a = 1

# -----------------------------------------------------------------------------#
#   This block of code recreates the flow of the circuit          #
#   from start to fin.                                                                #
# -----------------------------------------------------------------------------#
output_gate = []
for key in dict_of_circuit.keys():
    if dict_of_circuit[key]['ID'] == 1:
        output_gate += [key]


def circuit_flow(circuit_dict, starting_gate_list):
    # find the inputs to the gates in the starting_gate_list
    for gate in starting_gate_list:
        for key in circuit_dict:
            try:
                if (circuit_dict[key]['ID'] in
                        circuit_dict[gate]['Inputs']):
                    starting_gate_list += [(gate, key)]
            except:
                pass
        if len(gate) == 2:
            for key in circuit_dict:
                try:
                    if(circuit_dict[key]['ID'] in
                            circuit_dict[gate[1]]['Inputs']):
                        starting_gate_list += [(gate[1], key)]
                except:
                    pass

circuit_flow(dict_of_circuit, output_gate)
output_gate = output_gate[1: len(output_gate)]

circ = {}
for k, v in output_gate:
    circ.setdefault(k, [k]). append(v)

circ_list = list(map(tuple, circ.values()))

# -------------------------------------------------------------------------------#
# We order the elements in the circ_list based on their ID       #
# -------------------------------------------------------------------------------#

# this adds the IDs to the circuit list:
for key in dict_of_circuit.keys():
    for elem in circ_list:
        if key == elem[0]:
            element = (dict_of_circuit[key]['ID'], elem)
            circ_list[circ_list.index(elem)] = element

# Sort the circuit elements from greatest to least.
circ_list = sorted(circ_list, reverse=True, key=lambda x: x[0])

# --------------------------------------------------------------------------------#
# Define a combinations function that we will use later            #
# This function was taken from the python website as a          #
# replacement for the itertools library function combos.          #
# --------------------------------------------------------------------------------#


def combinations(iterable, r):
    # combinations('ABCD', 2) --> AB AC AD BC BD CD
    # combinations(range(4), 3) --> 012 013 023 123
    pool = tuple(iterable)
    n = len(pool)
    if r > n:
        return
    indices = list(range(r))
    yield tuple(pool[i] for i in indices)
    while True:
        for i in reversed(range(r)):
            if indices[i] != i + n - r:
                break
        else:
            return
        indices[i] += 1
        for j in range(i + 1, r):
            indices[j] = indices[j - 1] + 1
        yield tuple(pool[i] for i in indices)

# -------------------------------------------------------------------------------#
# Function that turns the dictionary of circuit elements into    #
# a vector of circuit elements                                                   #
# -------------------------------------------------------------------------------#


def create_parameters_array(dict_of_circuit):
    gates = [{gatename: values} for gatename, values in dict_of_circuit.items(
    ) if len(values) > 5]  # Get only the gates that are not the initial inputs
    params = np.array([[gatevalues['n'], gatevalues['K'], gatevalues['ymax'],
                        gatevalues['ymin']] for gate in gates for gatename,
                       gatevalues in gate.items()])
    flat_params = params.flatten()  # creates linear array
    return flat_params


# -------------------------------------------------------------------------------#
# Grouper Function from python recipes                                  #
# --------------------------------------------------------------------------------#
# From Python Recipes "Collect data into fixed-length chunks or blocks"
# grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
def grouper(iterable, n, fillvalue=None):

    args = [iter(iterable)] * n
    return(zip_longest(*args, fillvalue=fillvalue))

# --------------------------------------------------------------------------------#
# Convert the parameter array to array of tuples                    #
# --------------------------------------------------------------------------------#


def convert_parameter_array_to_tuples(params, dict_of_circuit):
    gates = [gatename for gatename, values in dict_of_circuit.items() if len(
        values) > 5]  # Name of gates that aren't the initial input
    params_per_gate = grouper(params, 4)
    dict_values = [(gatename,) + tuple(zip(['n', 'K', 'ymax', 'ymin'],
                                           gate_params))
                   for gatename, gate_params in zip(gates, params_per_gate)]

    # Updates dict_of_circuit
    for x in dict_values:
        for y in x:
            if isinstance(y, tuple):
                dict_of_circuit[x[0]][y[0]] = y[1]

    return dict_of_circuit

# ---------------------------------------------------------------------------------------------#
# Get the X value for stretch given a target score and repressor name  #
# and the inputs into that specific repressor for the high and low output #
# This code is for experimental purposes only and is not used in our       #
# final outcome.
# ---------------------------------------------------------------------------------------------#


new_dict_of_circuit = deepcopy(dict_of_circuit)


def stretch_x_value(TS, org_list, dict_of_circuit):
    x_list = []
    for ele in org_list:
        high = 1 + ((sum(ele[1][0])) /
                    dict_of_circuit[ele[0]]['K'])**dict_of_circuit[ele[0]]['n']
        low = 1 + ((sum(ele[1][1])) /
                   dict_of_circuit[ele[0]]['K'])**dict_of_circuit[ele[0]]['n']
        x = ((((TS * high) / low) * dict_of_circuit[ele[0]]['ymin'] * (low - 1)
              - dict_of_circuit[ele[0]]['ymin'] * (high - 1)) /
             ((dict_of_circuit[ele[0]]['ymax'] - ((TS * high) / low))
              * dict_of_circuit[ele[0]]['ymax']))**(1 / 2)
        x_list += [(ele[0], x)]
    return x_list


def circuit_forward_prop_stretch_list(parameters, a_dict):
    global circ_list
    stretch_inputs = []
    if isinstance(parameters, dict):
        a_dict = parameters
    else:
        a_dict = (convert_parameter_array_to_tuples(
            parameters, a_dict))

    for ele in circ_list:
        count = 1
        for item in ele[1]:
            if item != ele[1][0]:
                count += 1
                y_min = a_dict[ele[1][0]]['ymin']
                y_max = a_dict[ele[1][0]]['ymax']
                k = a_dict[ele[1][0]]['K']
                n = a_dict[ele[1][0]]['n']
                if count > 2:
                    input_list += [(a_dict[item]['ymin'],
                                    a_dict[item]['ymax'])]
                else:
                    input_list = [(a_dict[item]['ymin'],
                                   a_dict[item]['ymax'])]
                the_input = [x for t in input_list for x in t]
                x_list = list(combinations(the_input, int(len(the_input) / 2)))
                for item in input_list:
                    if item in x_list:
                        x_list.remove(item)
                on_values = []
                off_values = []
                index = 0
                on_indices = []
                off_indices = []
                for b_x in x_list:
                    x = sum(b_x)
                    the_y = y_min + (y_max - y_min) / (1 + (x / k)**n)
                    if the_y > (y_max / 2):
                        on_values += [the_y]
                        on_indices += [index]
                    elif the_y < (y_min * 2):
                        off_values += [the_y]
                        off_indices += [index]
                    index += 1
        on_index = on_values.index(min(on_values))
        off_index = off_values.index(max(off_values))
        stretch_inputs += [(x_list[on_indices[on_index]],
                            x_list[off_indices[off_index]])]
        a_dict[ele[1][0]]['ymin'] = max(off_values)
        a_dict[ele[1][0]]['ymax'] = min(on_values)
        score = min(on_values) / max(off_values)
    return stretch_inputs


def assign_x_values(stretch_inputs, circ_list):
    output = []
    for index in range(0, len(circ_list)):
        output += [(circ_list[index][1][0], stretch_inputs[index])]
    return output

# parameters = create_parameters_array(new_dict_of_circuit)
# stretch_inputs = circuit_forward_prop_stretch_list(
#     parameters, new_dict_of_circuit)
# org_stre_input = assign_x_values(stretch_inputs, circ_list)
# the_exes = stretch_x_value(328, org_stre_input, dict_of_circuit)
# -----------------------------------------------------------------------------------#
# Recreates the genetic circuit using forward propagation          #
# -----------------------------------------------------------------------------------#


def circuit_forward_prop(parameters, dict_of_circuit, flag=False):
    global circ_list
    score = 0
    a_dict = deepcopy(dict_of_circuit)
    if isinstance(parameters, dict):
        dict_of_circuit = parameters
    else:
        dict_of_circuit = (convert_parameter_array_to_tuples(
            parameters, dict_of_circuit))
    for ele in circ_list:
        try:
            count = 1
            for item in ele[1]:
                if item != ele[1][0]:
                    count += 1
                    y_min = dict_of_circuit[ele[1][0]]['ymin']
                    y_max = dict_of_circuit[ele[1][0]]['ymax']
                    k = dict_of_circuit[ele[1][0]]['K']
                    n = dict_of_circuit[ele[1][0]]['n']
                    if count > 2:
                        input_list += [(dict_of_circuit[item]['ymin'],
                                        dict_of_circuit[item]['ymax'])]
                    else:
                        input_list = [(dict_of_circuit[item]['ymin'],
                                       dict_of_circuit[item]['ymax'])]
                    the_input = [x for t in input_list for x in t]
                    x_list = list(combinations(
                        the_input, int(len(the_input) / 2)))
            for it in input_list:
                if it in x_list:
                    x_list.remove(it)
            if len(x_list) == 2:
                x_list += x_list
            on_values = []
            off_values = []
            highs = dict_of_circuit[ele[1][0]]['logic']
            lows = dict_of_circuit[ele[1][0]]['logic']
            highs = highs.count(1)
            lows = lows.count(0)
            for b_x in x_list:
                x = sum(b_x)
                the_y = y_min + (y_max - y_min) / (1 + (x / k)**n)
                if the_y > y_max / 2:
                    on_values += [the_y]
                elif the_y < y_min * 2:
                    off_values += [the_y]
            if len(on_values) > highs:
                if not flag:
                    return -1 * score
                else:
                    return -1 * score, dict_of_circuit
            elif len(off_values) > lows:
                if not flag:
                    return -1 * score
                else:
                    return -1 * score, dict_of_circuit

            try:
                dict_of_circuit[ele[1][0]]['ymin'] = max(off_values)
                dict_of_circuit[ele[1][0]]['ymax'] = min(on_values)
                score = min(on_values) / max(off_values)
                len_circ_list = len(circ_list)
                if ele[1][0] not in circ_list[len_circ_list - 1][1]:
                    dict_of_circuit[ele[1][0]]['score'] = score
            except:
                break
        except:
            score = dict_of_circuit[ele[1][0]]['score']
    if not flag:
        return -1 * score
    else:
        return score, dict_of_circuit


# ---------------------------------------------------------------------------#
# Run the functions that were made previously                  #
# ---------------------------------------------------------------------------#
# print(dict_of_circuit)
# parameters = create_parameters_array(dict_of_circuit)
# circuit_forward_prop(parameters, dict_of_circuit)

import requests
import os
import json
import numpy as np
from requests.auth import HTTPBasicAuth
from itertools import zip_longest


# Setup the username and password for Cello Authentication
username = 'gottbenn'
password = '123456789'
auth = HTTPBasicAuth(username, password)

# ------------------------------------------------#
#     UCF File processing                       #
# -------------------------------------------------#
with open('gottbenn.UCF.json') as initial_UCF:
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
#  Put the circuit info    into a dictionary           #
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
    ) if len(values) > 4]  # Get only the gates that are not the initial inputs
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
        values) > 4]  # Name of gates that aren't the initial input
    # Groups the linear array into tuples of size 4 ex: [1,2,3,4,5,6,7,8] -->
    # (1,2,3,4), (5,6,7,8)
    params_per_gate = grouper(params, 4)
    dict_values = [(gatename,) + tuple(zip(['n', 'K', 'ymax', 'ymin'],
                                           gate_params))
                   for gatename, gate_params in zip(gates, params_per_gate)]
    return dict_values

# -----------------------------------------------------------------------------------#
# Recreates the genetic circuit using forward propagation          #
# -----------------------------------------------------------------------------------#


def circuit_forward_prop(parameters):
    global dict_of_circuit
    global circ_list

    parameter_list = (convert_parameter_array_to_tuples(parameters,
                                                        dict_of_circuit))

    # update the dict_of_circuit
    for x in parameter_list:
        for y in x:
            if isinstance(y, tuple):
                dict_of_circuit[x[0]][y[0]] = y[1]

    for ele in circ_list:
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
                x_list = list(combinations(the_input, int(len(the_input) / 2)))
                for item in input_list:
                    if item in x_list:
                        x_list.remove(item)
                on_values = []
                off_values = []
                for b_x in x_list:
                    x = sum(b_x)
                    the_y = y_min + (y_max - y_min) / (1 + (x / k)**n)
                    if the_y > (y_max/2):
                        on_values += [the_y]
                    elif the_y < (y_min*2):
                        off_values += [the_y]
        dict_of_circuit[ele[1][0]]['ymin'] = max(off_values)
        dict_of_circuit[ele[1][0]]['ymax'] = min(on_values)
        score = min(on_values) / max(off_values)
    print(score)
    print(dict_of_circuit[ele[1][0]]['score'])


# ---------------------------------------------------------------------------#
# Run the functions that were made previously                  #
# ---------------------------------------------------------------------------#
parameters = create_parameters_array(dict_of_circuit)
circuit_forward_prop(parameters)

import requests
import os
import json
import numpy as np
from requests.auth import HTTPBasicAuth
from itertools import zip_longest

# The first step of this code is to develop a program that can connect to
# Cello.

username = 'gottbenn'
password = '123456789'
auth = HTTPBasicAuth(username, password)
case = 0
# I want to write a python tool that performs different post and get operations
# based on the user input of a certain value.
# This tool should help in writing the UI

# 1st case: A simple curl test:
if case == 1:
    url = 'http://cellocad.org:8080'
    req = requests.get(url, auth=auth)
    print(req.text)
elif case == 2:
    # 2nd case: get a netlist from the cello website.
    url = 'http://cellocad.org/netsynth'
    file = './resources/pycello/resources/AND.v'
    verilog_text = open(file, 'r').read()
    params = {'verilog_text': verilog_text}
    req = requests.post(url, auth=auth, params=params)
elif case == 3:
    # 3rd case: Design a circuit using Cello
    url = 'http://cellocad.org/submit'
    ID = username + '_Circuit'
    file = './resources/pycello/resources/AND.v'
    inputs = './resources/pycello/resources/Inputs.txt'
    outputs = './resources/pycello/resources/Outputs.txt'
    verilog_text = open(file, 'r').read()
    inputs_text = open(inputs, 'r').read()
    outputs_text = open(outputs, 'r').read()
    params = {'id': ID, 'verilog_text': verilog_text, 'input_promoter_data':
              inputs_text, 'output_gene_data': outputs_text}
    req = requests.post(url, auth=auth, params=params)
    print(req.text)
elif case == 4:
    # 4th case: Get list of completed jobs
    url = 'http://cellocad.org/results'
    req = requests.get(url, auth=auth)
    print(req.text)
elif case == 5:
    # 5th case: Get a list of result filenames from a job result
    ID = username + '_Circuit'
    url = 'http://cellocad.org/results/' + ID
    req = requests.get(url, auth=auth)
    print(req.text)
elif case == 6:
    # 6th case: Get the contents of a specified file
    ID = username + '_Circuit'
    filename = ID + '_A000' + '_logic' + '_circuit.txt'
    filename2 = ID + '_A000' + '_bionetlist.txt'
    filename3 = ID + '_inputs.txt'
    filename4 = ID + '_outputs.txt'
    url = 'http://cellocad.org/results/' + ID + '/' + filename4
    req = requests.get(url, auth=auth)
    new_file = open('out2.txt', 'w')
    print(req.text, file=new_file)
    new_file.close()

# Thoughts on what I need to do. I need to connect to Cello feed it a circuit,
# then from there have it design the circuit. Once we get what the promoters
# are for each of the circuits we then need to go into the UCF file and modify
# the values we want to for the circuit to create DNA Engineering.

# First step have cello give us what the promoters are for each circuit
with open('gottbenn.UCF.json') as initial_UCF:
    original_UCF = json.load(initial_UCF)

print(original_UCF[23:44])

# Lets get all the known promoters in the UCF file, this should make it easier
# to identify if one of these promoters is being used in the circuit.
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
# Next step is to look for the promoters that are used in this circuit.
# For this we will look at getting the contents of the _logic_circuit.txt file.
ID = username + '_Circuit'
filename = ID + '_A000' + '_logic' + '_circuit.txt'
url = 'http://cellocad.org/results/' + ID + '/' + filename
req = requests.get(url, auth=auth)
scores = open('scores.txt', 'w')
print(req.text, file=scores)
scores.close()

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
# get the set of all the gates in the circuit
# this guarantees I am not accidentally reproducing
# gates in the circuit.
# I need to grap the numerical IDs of each of the inputs and outputs.
# Note within the list_of_identities the first parameter of a sub_list is
# the lexical ID of the promoter. The second element is the numerical ID
# any element after the second is the input into that specific promoter/
# or any value that comes before the output. With the file format specified
# it is generally always guaranteed that the first sub_list is the output
# identity
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


# Now for convenience I want to make a dictionary that has
# all the information we need of the circuit and its elements.

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

ord_list_of_circ_el = sorted(list_of_circ_elements, key=lambda x: x[1])

# this little chunk of code is to add the y_min and y_max values
# to the input in our dictionary.
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

# we are going to do a little bit more preprocessing here in order to
# convert all the numbers in our dictionary to floats so we can use them
# in mathematical operations

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


# ----------- Eveything above this was essentially just preprocessing -
# ----------- Below this we are attempting to manipulate the circuit --
# ----------- parameters to see how that effects the ouptut score  ----
# we will try multiple methods to calculate what happens when we alter
# a promoter in a specific parameter to
    # first find the output in the dictionary
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

# this adds the IDs to the circuit list:
for key in dict_of_circuit.keys():
    for elem in circ_list:
        if key == elem[0]:
            element = (dict_of_circuit[key]['ID'], elem)
            circ_list[circ_list.index(elem)] = element

# Sort the circuit elements from greatest to least.
circ_list = sorted(circ_list, reverse=True, key=lambda x: x[0])

# now that I have the inputs the next thing to do is to calculate
# the score of the inputs given the equation. We want to do this
# for all the combinations of ymax and ymin. this will give us a list
# that contains all the possible y values of our output promoter in question.


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

# these lines of code convert the input_list which is a list of tuples
# to a regular list so it can be run in the combination function
# we have the list of tuples to get ride of any elements after the
# combinations output that represent an input being both high and
# low at the same time.

# Now I want to calculate the y_min, y_max of the elements
# based on the equation:
# y = ymin + (ymax - ymin)/(1.0 + (x/K)^n)

# circuit properties = [("gatename", ('K', value), ('ymin', value) ... ),(...)]
circuit_properties = [('pTet', ('ymin', 0.001), ('ymax', 4.4)),
                      ('A1_AmtR', ('ymin', 0.06), ('ymax', 3.8))]


# Converts the dict of circuit to a linear array of parameters
def create_parameters_array(dict_of_circuit):
    # This assumes that the dictionary is in the same order always
    # According to some random person on StackOverflow, the order is usually the same but not guaranteed so we may want to switch to using ordered dicts?
    # Or maybe consider changing it to a list of dictionaries b/c the order is guaranteed
    gates = [{gatename:values} for gatename,values in dict_of_circuit.items() if len(values) > 4] # Get only the gates that are not the initial inputs
    params = np.array([[gatevalues['n'], gatevalues['K'], gatevalues['ymax'], gatevalues['ymin']] for gate in gates for gatename, gatevalues in gate.items()]) # list of lists for each gate
    flat_params = params.flatten() # creates linear array
    return flat_params


def grouper(iterable, n, fillvalue=None): # From Python Recipes
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)

# Converts a linear array to [("gatename", ('K', value), ('ymin', value) ... ),(...)] form which can be used to update dictionary
# This only works if we assume that the dict_of_circuit order is always the same
def convert_parameter_array_to_tuples(params,dict_of_circuit):
    print(dict_of_circuit)
    gates = [gatename for gatename,values in dict_of_circuit.items() if len(values) > 4] # Name of gates that aren't the initial input
    params_per_gate = grouper(params,4) # Groups the linear array into tuples of size 4 ex: [1,2,3,4,5,6,7,8] --> (1,2,3,4), (5,6,7,8)
    dict_values = [(gatename,) + tuple(zip(['n', 'K', 'ymax', 'ymin'],gate_params)) for gatename, gate_params in zip(gates, params_per_gate)] # Combines gate names w gate parameters
    return dict_values

# The input needs to be the parameters of the circuit
# circuit_properties = the initial input to the circuit
def circuit_forward_prop(parameters, circuit_properties):
    global dict_of_circuit
    global circ_list

    parameter_list = convert_parameter_array_to_tuples(parameters,dict_of_circuit) + circuit_properties

    # update the dict_of_circuit
    for x in parameter_list:
        for y in x:
            if isinstance(y, tuple):
                print(dict_of_circuit[x[0]][y[0]], y[1])
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
                y_values = []
                for b_x in x_list:
                    x = sum(b_x)
                    y_values += [y_min + (y_max - y_min) / (1 + (x / k)**n)]
        dict_of_circuit[ele[1][0]]['ymin'] = min(y_values)
        dict_of_circuit[ele[1][0]]['ymax'] = max(y_values)
        score = max(y_values) / min(y_values)
    print(score)
    print(dict_of_circuit[ele[1][0]]['score'])

parameters = create_parameters_array(dict_of_circuit)
circuit_forward_prop(parameters, circuit_properties)


# I don't know yet how we are going to modify the UCF file to
# show different values.

for info in range(23, 44):
    for item in circuit_properties:
        if original_UCF[info]['gate_name'] == item[0]:
            params = original_UCF[info]['parameters']
            for x in range(0, len(params)):
                for y in item:
                    if original_UCF[info]['parameters'][x]['name'] == y[0]:
                        original_UCF[info]['parameters'][x]['value'] == y[1]

with open('new.UCF.json', 'w') as outfile:
    json.dump(original_UCF, outfile)

import requests
import os
import json
import numpy as np
from requests.auth import HTTPBasicAuth

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
    filename = ID+'_A000'+'_logic' + '_circuit.txt'
    filename2 = ID + '_A000'+'_bionetlist.txt'
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
gate_names = []
for info in original_UCF[23:44]:
    # save all the gate_names in an array.
    gate_names += [info['gate_name']]

# Next step is to look for the promoters that are used in this circuit.
# For this we will look at getting the contents of the _logic_circuit.txt file.
ID = username + '_Circuit'
filename = ID+'_A000'+'_logic' + '_circuit.txt'
url = 'http://cellocad.org/results/' + ID + '/' + filename
req = requests.get(url, auth=auth)
scores = open('scores.txt', 'w')
print(req.text, file=scores)
scores.close()

gates_in_circuit = []
table = []
count = 1
for line in open('scores.txt', 'r'):
    if ('Circuit_score' not in line) and (count != 0):
        table += [line]
        count += 1
    if 'Circuit_score' in line:
        circuit_score = line[15:25]
        count = 0
    for gates in gate_names:
        if 'Gate' in line:
            index = line.index('Gate')
            gates_in_circuit += [(gates, line[index+5: index+15])]

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

print(dict_of_circuit)

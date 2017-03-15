import requests
import os
from requests.auth import HTTPBasicAuth

username = os.environ.get('CELLOUSER')
password = os.environ.get('CELLOPASS')
auth = HTTPBasicAuth(username, password)

f = '/Users/melissagarcia/Documents/Spring2016/CSB/Homework/HW1/resources/pycello/resources/AND.v'

url = 'www.cellocad.org/netsynth'
verilog_text = open(f,'r').read()
params = {'verilog_text':verilog_text}

r = requests.post('http://www.cellocad.org/netsynth', params=params, auth=auth)
nf = open('out.txt','w')
print(r.text,file=nf)
nf.close()
import mutant_creator
import json_grammar
from fuzzingbook import Grammars
from fuzzingbook.Grammars import *

from fuzzingbook import GrammarFuzzer
from fuzzingbook.GrammarFuzzer import GrammarFuzzer

## this code stores inputs in a set, takes a function and generates mutants 
#(we split on value parser = ... statement so that the code is appended right above it and so that it calls the changed function) 
# - for every mutant, we take each of the stored inputs and raise errors if the output is not equal to that of the original parser
# or if res_mutated[0] doesnt print (is None/nothing to print). 
# Note that our mutant is created using ast.Return(None) not ast.Pass() which means instead of deleting statement and replacing it with Pass, we replace it with Return None
# We store the inputs that killed the mutants
import subprocess
import json

LAMBDA = lambda:0
cnt = 0
f = open("json_parser.py",'r')
f = f.read()
d_res = dict()

inp = GrammarFuzzer(JSON_GRAMMAR)
killer_inputs = set()
fuzzinp = []
for i in range(10):
    fuzzinp.append(inp.fuzz())
print(fuzzinp)
for fn in fns:
    if isinstance(fn[1], type(LAMBDA)) and fn[1].__name__ == LAMBDA.__name__: #check if fn is lambda fn, dont consider that
        continue
    print(fn[0])
    for mutant in MuFunctionAnalyzer(fn[1]): ## fn[0] is the function name. We need to pass the function, so take fn[1]
        cnt+=1
         
        new_f = f.split("value_parser = ")[0]+"\n"+mutant.src()+"\n" + "value_parser = " + f.split("value_parser = ")[1]
#         new_f = f+"\n"+mutant.src()
        #print(new_f)
        mutated_f = open('json_parser_mutated.py','w')
        mutated_f.write(new_f)
        mutated_f.close()
        for fi in fuzzinp:
            json_inp = json.dumps(fi)
            json_inp_file = open("json_inp.json","w")
            json_inp_file.write(json_inp)
            json_inp_file.close()
            out = subprocess.Popen([sys.executable,"json_parser_test.py"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            #out = subprocess.Popen(["json_parser_test.py", '"'+inp.fuzz()+'"'],shell=True,stdout=subprocess.PIPE)
            fuzzout, errors = out.communicate()
            d_res[new_f].append((fi,fuzzout.decode("utf-8"),errors))
            if errors:
                killer_inputs.add(fi)
                print("Mutant killed")
            #print(d_res[new_f])

print(killer_inputs)
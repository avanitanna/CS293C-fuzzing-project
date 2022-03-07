import subprocess
import sys
import json
from collections import defaultdict
import hashlib
import copy 
import matplotlib.pyplot as plt

sys.path.append("../")
import mutant_creator
import mutant_grammar_gen

from fuzzingbook.Grammars import *
from fuzzingbook.GrammarFuzzer import GrammarFuzzer
from fuzzingbook.ProbabilisticGrammarFuzzer import *

#get functions to mutate from parser to fuzz
from inspect import getmembers, isfunction
import json_parser

# for computing coverage
from fuzzingbook.Coverage import Coverage
import json_parser_mutated_0

#generate probabilistic grammar
#we use mutliple grammars to offset fixed directions caused by killing only particular kinds of mutants

mut_prob_grammar = copy.deepcopy(JSON_GRAMMAR)
random_prob_grammar = copy.deepcopy(JSON_GRAMMAR)

baseline_fuzz = GrammarFuzzer(JSON_GRAMMAR)
samples = []

for i in range(100):
    sample = baseline_fuzz.fuzz()
    if sample not in samples:
        samples.append(baseline_fuzz.fuzz())

 ## run a random input first to have the correct coverage value:
with Coverage() as cov_fuzz:
    try:
        json_parser_mutated_0.value_parser(baseline_fuzz.fuzz().strip())
    except:
        pass
mut_prob_grammar = mutant_grammar_gen.random_vector_gen(mut_prob_grammar, "sample", samples)
random_prob_grammar = mutant_grammar_gen.random_vector_gen(mut_prob_grammar, "sample", samples)


global_output_log = defaultdict(list)

tot_death = 0
tot = 0
max_coverage = 0
## save mutant_srcs - as we have an exhaustive list of mutants for every fuzzer iteration, it is more efficient to run it outside the fuzzer iterations 
mutant_srcs = []
mutant_pm_srcs = []

# directly generate mutant without the need to break json_parser into separate functions
for mutant in mutant_creator.MuFunctionAnalyzer(json_parser): 
    mutant_srcs.append(mutant.src())
    mutant_pm_srcs.append(len(mutant.pm.src.split('\n')))
    #print(mutant.diff())
    #print(difflib.unified_diff(mutant.pm.src.split('\\n'), mutant.src().split('\\n'),fromfile=mutant.pm.name,tofile=mutant.name, n=3))

mut_limit = int(sys.argv[3])
mutant_srcs = mutant_srcs[:mut_limit]
killed_list = set()
iter_death = 0

for j in range(int(sys.argv[1])): #limit iterations of fuzzer
    iter_cov = 0
    tot+=1 
    iter_output_log = defaultdict(list)
    inputs = set()

    mut_gen = ProbabilisticGrammarFuzzer(mut_prob_grammar,  max_nonterminals=5)
    random_gen = ProbabilisticGrammarFuzzer(random_prob_grammar,  max_nonterminals=5)

    inputs = set()
    
    inp_count=0
    while True:
        if len(inputs) == int(sys.argv[2]) or inp_count > int(sys.argv[2])*int(sys.argv[2]):
            break    
        inputs.add(random_gen.fuzz())
        inputs.add(mut_gen.fuzz())
        inp_count+=1


    killer_inputs = set()

    print("# inputs ", len(inputs))
   
    # reset for every iteration
    max_coverage = 0
    
    for fi in inputs:
        
        mutant_killed = 0
        inp_coverage = [0]

        json_inp = json.dumps(fi)
        json_inp_file = open("json_inp_0.json","w")
        json_inp_file.write(json_inp)
        json_inp_file.close()
        for i,m in enumerate(mutant_srcs):   
            
            if i in killed_list: #skip dead mutants
                continue

            mutated_prog = m
            mutated_file = open('json_parser_mutated_0.py','w')
            mutated_file.write(mutated_prog)
            mutated_file.close()

            with Coverage() as cov_fuzz:
                try:
                    json_parser_mutated_0.value_parser(fi.strip())
                except:
                    pass
            correct_cov = len(cov_fuzz.coverage())
            out = subprocess.Popen([sys.executable,"json_parser_test_0.py"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            fuzzout, errors = out.communicate()
            
            if errors:
                killer_inputs.add(fi)
                mutant_killed+=1
                killed_list.add(i)
                print("Mutant killed")
                
            inp_coverage.append(int(correct_cov))  
        
        iter_output_log[fi].append(mutant_killed)
        iter_output_log[fi].append(max(inp_coverage))        
        iter_death += iter_output_log[fi][0]
        iter_cov = max([iter_cov,iter_output_log[fi][1]])
        print("for input:"+fi+":coverage was:"+str(correct_cov)+":and mutants killed were:"+str(mutant_killed)+":out of:"+str(len(mutant_srcs) - len(killed_list)))

    print("baseline for mutant killing")
    print("Current stats:")
    print(iter_output_log)

    global_output_log[tot] = [mut_limit - iter_death, iter_cov]
    
    if len(killer_inputs) != 0:
        mut_prob_grammar = mutant_grammar_gen.modify_vec(mut_prob_grammar, "mined", list(killer_inputs)) 
    random_prob_grammar = mutant_grammar_gen.modify_vec(random_prob_grammar, "random")

print('global output log', global_output_log)
## store logs
with open('C:/Users/Avani/Data/Learning/UCSB_PREP/CS293C/CS293C-fuzzing-project/json-fuzzer/results/StmtReturnMutator/json_mutant_fuzzer/output_log_50-50-50.txt','w') as data: 
    data.write(str(global_output_log))

y_kill=[mut_limit]
y_kill += list(map(lambda x: global_output_log[x][0] ,global_output_log))
x_kill = range(len(y_kill))

y_cov = [0]
y_cov += list(map(lambda x: global_output_log[x][1] ,global_output_log))
x_cov = range(len(y_cov))

plt.plot(x_kill,y_kill,color='red', marker='o')
plt.title("Json Mutant fuzzer")
plt.xlabel("Number of total iterations")
plt.ylabel("Mutants Remaining")
#plt.xticks(nbins=10)
#plt.xticks(range(len(x_kill)+1))
plt.grid(True)
plt.savefig("C:/Users/Avani/Data/Learning/UCSB_PREP/CS293C/CS293C-fuzzing-project/json-fuzzer/results/StmtReturnMutator/json_mutant_fuzzer/mutant_50-50-50.png")
plt.clf()
#plt.show()

plt.plot(x_cov,y_cov,color='green', marker='o')
plt.title("Json Mutant fuzzer")
plt.xlabel("Number of total iterations")
plt.ylabel("Coverage")
#plt.xticks(nbins=10)
#plt.xticks(range(len(x_cov)+1))
plt.grid(True)
plt.savefig("C:/Users/Avani/Data/Learning/UCSB_PREP/CS293C/CS293C-fuzzing-project/json-fuzzer/results/StmtReturnMutator/json_mutant_fuzzer/cov_50-50-50.png")
plt.clf()
#plt.show()
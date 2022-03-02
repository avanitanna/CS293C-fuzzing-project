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
import json_parser_mutated

# threading
import threading 

killer_inputs = set()

#generate probabilistic grammar
#we use mutliple grammars to offset fixed directions caused by killing only particular kinds of mutants

mined_prob_grammar = copy.deepcopy(JSON_GRAMMAR)
random_prob_grammar = copy.deepcopy(JSON_GRAMMAR)

baseline_fuzz = GrammarFuzzer(JSON_GRAMMAR)
samples = []

for i in range(100):
    sample = baseline_fuzz.fuzz()
    if sample not in samples:
        samples.append(baseline_fuzz.fuzz())

mined_prob_grammar = mutant_grammar_gen.random_vector_gen(mined_prob_grammar, "sample", samples)
random_prob_grammar = mutant_grammar_gen.random_vector_gen(mined_prob_grammar, "sample", samples)


global_output_log = defaultdict(list)

tot_death = 0
tot = 0
## save mutant_srcs - as we have an exhaustive list of mutants for every fuzzer iteration, it is more efficient to run it outside the fuzzer iterations 
mutant_srcs = []
mutant_pm_srcs = []

# directly generate mutant without the need to break json_parser into separate functions
for mutant in mutant_creator.MuFunctionAnalyzer(json_parser): 
    mutant_srcs.append(mutant.src())
    mutant_pm_srcs.append(len(mutant.pm.src.split('\n')))

mut_limit = int(sys.argv[3])
mutant_srcs = mutant_srcs[:mut_limit]

for i in range(int(sys.argv[1])): #limit iterations of fuzzer
    iter_death = 0
    iter_tot = [0]
    iter_output_log = defaultdict(list)

    mined_gen = ProbabilisticGrammarFuzzer(mined_prob_grammar,  max_nonterminals=5)
    random_gen = ProbabilisticGrammarFuzzer(random_prob_grammar,  max_nonterminals=5)


    iter_mutant_log = defaultdict(set)
    iter_coverage_log = defaultdict(list)
    killer_inputs = set()
    inputs = set()
    killed_mutants = set()
    #generate inputs for fuzzer
    #TODO timeout if input generation takes too long
    for j in range(int(sys.argv[2])): #accept command line argument for number of inputs per grammar 
        inputs.add(random_gen.fuzz())
        inputs.add(mined_gen.fuzz())

    print("# inputs ", len(inputs))
    # reset for every iteration
    max_coverage = [1]
    num_mutants_killed = [0]
    def thread_function(index, mutant_srcs_subset):
        
        for i,m in enumerate(mutant_srcs_subset):   
            #mutant.src is mutated function, mutant.prm.src is original function        
            #Here we append mutated function to file before entry point function, thus overwriting the non mutated implementation
            #currently one mutation available (adding a return statement)
            mutated_prog = m
            mutated_file = open('json_parser_mutated_'+str(index)+'.py','w')
            mutated_file.write(mutated_prog)
            mutated_file.close()
            for fi in inputs:
                json_inp = json.dumps(fi)
                json_inp_file = open("json_inp_"+str(index)+".json","w")
                json_inp_file.write(json_inp)
                json_inp_file.close()
            
                out = subprocess.Popen([sys.executable,"json_parser_test_"+str(index)+".py"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                fuzzout, errors = out.communicate()
                fuzzout = fuzzout.decode("utf-8").split(":-")
                correct_cov=''
                correct_output=''
                if len(fuzzout) == 2:
                    correct_cov = fuzzout[1]
                    correct_output = fuzzout[0]      
                    max_coverage[0] = max(int(correct_cov),max_coverage[0])
                res = json_parser.value_parser(fi.strip())
                if correct_output != res[0]:
                    killer_inputs.add(fi)
                    killed_mutants.add(m)
                    num_mutants_killed[0]+=1
                    iter_mutant_log[fi].add(m)
                    print("Mutant killed")
                    break #break out of the input loop if a mutant is killed, another input is only interesting to us if it kills more mutants, otherwise it belongs to the same equivalence class
            #iter_coverage_log[fi].append(max_coverage[0])    
        
    threads = list()
    start = 0
    for index in range(3):
        print("create and start thread %d.", index)
        x = threading.Thread(target=thread_function, args=(index,mutant_srcs[start:start+len(mutant_srcs)//3]))
        start+=len(mutant_srcs)//3
        threads.append(x)
        x.start()

    for index, thread in enumerate(threads):
        print("before joining thread %d.", index)
        thread.join()
        print("thread %d done", index)
        
    global_output_log[i] = [mut_limit - num_mutants_killed[0], max_coverage[0]]
    #TODO add logging to collect results
    #TODO add coverage information for results
    print("################## Round"+str(i)+"stats ###############")
    print("killer inputs\n", killer_inputs)
    print("inputs\n", inputs) 
    print("Number of mutants killed in iteration:",len(killed_mutants), "out of", str(len(mutant_srcs)))
    #print("Score per iteration (number of mutants killed in the iteration divided by the max coverage found in that iteration):",round((len(iter_output_log.keys())/iter_tot)/max_coverage,2)) 
    #print("Number of mutants killed total:",len(global_output_log.keys()), "out of", tot)
    #change inputs based on killer inputs
    print("##############################")
    if len(killer_inputs) != 0:
        mined_prob_grammar = mutant_grammar_gen.modify_vec(mined_prob_grammar, "mined", list(killer_inputs)) 
    random_prob_grammar = mutant_grammar_gen.modify_vec(random_prob_grammar, "random")

print(global_output_log)
y_kill=[mut_limit]
y_kill += list(map(lambda x: global_output_log[x][0] ,global_output_log))
x_kill = range(len(y_kill))

y_cov = [0]
y_cov += list(map(lambda x: global_output_log[x][1] ,global_output_log))
x_cov = range(len(y_cov))

plt.plot(x_kill,y_kill,color='red', marker='o')
plt.title("Json mutant guided fuzzer")
plt.xlabel("Number of total iterations")
plt.ylabel("Mutants Remaining")
plt.xticks(range(len(x_kill)+1))
plt.grid(True)
#plt.savefig("mut_based_killed.png")
#plt.clf()
plt.show()

plt.plot(x_cov,y_cov,color='green', marker='o')
plt.title("Json mutant guided fuzzer")
plt.xlabel("Number of total iterations")
plt.ylabel("Coverage")
plt.xticks(range(len(x_cov)+1))
plt.grid(True)
# plt.savefig("mut_based_cov.png")
# plt.clf()
plt.show()
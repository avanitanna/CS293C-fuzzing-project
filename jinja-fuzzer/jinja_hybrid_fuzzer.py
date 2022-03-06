import sys
import time
import docker
import subprocess
from collections import defaultdict
import copy
from inspect import getmembers, isfunction
import os
import matplotlib.pyplot as plt

sys.path.append("../")

import mutant_creator
import mutant_grammar_gen
from jinja_grammar import JINJA_GRAMMAR

from fuzzingbook.Grammars import *
from fuzzingbook.GrammarFuzzer import GrammarFuzzer
from fuzzingbook.ProbabilisticGrammarFuzzer import *

#functions to generate mutants from
from jinja_orig.jinja2 import Template as environment_mutate


client = docker.from_env()
runner = client.containers.run("fuzzer-runner", working_dir = "/app/jinja-fuzzer",
command = "/bin/bash", tty=True, 
detach = True, auto_remove = True, volumes={os.path.dirname(os.getcwd()): {'bind': '/app', 'mode': 'rw'}} )

def test_env(sample):

    runner.exec_run("pip -qqq install -e ./jinja_mutate")
    f=open("template_file","w")
    f.write(sample)
    f.close()
    r = runner.exec_run("python3 jinja_tester.py")
    # print(r.output)
    return r.output.decode("utf-8")

jinja_path = "jinja_mutate/jinja2/environment.py"

jinja_to_fuzz = open(jinja_path)

jinja_seed = jinja_to_fuzz.read()

hybrid_prob_grammar = copy.deepcopy(JINJA_GRAMMAR)
cov_prob_grammar = copy.deepcopy(JINJA_GRAMMAR)

baseline_fuzz = GrammarFuzzer(JINJA_GRAMMAR, max_nonterminals=5)
samples = []

for i in range(10):
    sample = baseline_fuzz.fuzz()
    if sample not in samples:
        samples.append(baseline_fuzz.fuzz())

hybrid_prob_grammar = mutant_grammar_gen.random_vector_gen(hybrid_prob_grammar, "sample", samples)
cov_prob_grammar = mutant_grammar_gen.random_vector_gen(cov_prob_grammar, "sample", samples)

global_output_log = defaultdict(list)

max_coverage = 0
LAMBDA = lambda:0
tot_death = 0
tot = 0

## save mutant_srcs - as we have an exhaustive list of mutants for every fuzzer iteration, it is more efficient to run it outside the fuzzer iterations 
mutant_srcs = []
mutant_pm_srcs = []

for mutant in mutant_creator.MuFunctionAnalyzer(environment_mutate): ## fn[0] is the function name. We need to pass the function, so take fn[1]
    mutant_srcs.append(mutant.src())
    mutant_pm_srcs.append(len(mutant.pm.src.split('\n')))        

mut_limit = int(sys.argv[3])
mutant_srcs = mutant_srcs[:mut_limit]
killed_list = set()
iter_death = 0

for i in range(int(sys.argv[1])): #limit iterations of fuzzer
    iter_cov = 0
    iter_output_log = defaultdict(list)
    tot+=1
    inputs = set()

    print("inside fuzzing loop")
    hybrid_gen = ProbabilisticGrammarFuzzer(hybrid_prob_grammar,  max_nonterminals=5)
    cov_gen = ProbabilisticGrammarFuzzer(cov_prob_grammar,  max_nonterminals=5)

    #for i in range(int(sys.argv[2])): #accept command line argument for number of inputs per grammar
        # print(inputs)
    inp_count=0
    while True:
        if len(inputs) == int(sys.argv[2]) or inp_count > int(sys.argv[2])*int(sys.argv[2]):
            break    
        inputs.add(cov_gen.fuzz())
        inputs.add(hybrid_gen.fuzz())
        inp_count+=1

    killer_inputs = set()
    print("# inputs ", len(inputs))
    # reset for every iteration
    max_coverage = 0

    for jinja_inp in inputs:
        #for each input calculate score (mutants killed/ coverage)
        #see how score improves per iteration of generation of inputs
        #if the trend in coverage and mutants killed ratio is increasing mutant guided fuzzing works
        #if it isn't increasing or tapering off, it isn't working

        mutant_killed = 0 #per input generation
        inp_coverage=[0] 

        for i,m in enumerate(mutant_srcs):   
            #mutant.src is mutated function, mutant.prm.src is original function        
            #Here we append mutated function to file before entry point function, thus overwriting the non mutated implementation
            #currently one mutation available (adding a return statement)

            if i in killed_list: #skip dead mutants
                continue

            mutated_prog = m
            mutated_file = open(jinja_path,'w')
            mutated_file.write(mutated_prog)
            mutated_file.close()
            start_time = time.time()
            out = subprocess.Popen([sys.executable, "jinja_tester.py",jinja_inp],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            fuzzout, errors = out.communicate()
            fuzzout = fuzzout.decode("utf-8").split(":-")
            correct_cov=''
            correct_output=''
            if len(fuzzout) == 2:
                correct_cov = fuzzout[1]
                correct_output = fuzzout[0]            
            print(jinja_inp)
            output_str = test_env(jinja_inp)
            print(output_str)
            print(fuzzout)
            print("time taken:",time.time()-start_time)
            test_output=''
            testout = output_str.split(":-")
            print("testout:",testout)
            test_cover = 1 #min coverage 1 to avoid divide by zero error
            # inp_coverage.append(1)
            if len(testout) == 2:
                test_output = testout[0]
                test_cover = int(testout[1])
            if fuzzout[0] == output_str == "killed":
                print("REAL ERROR FOUND!")

            if correct_output != test_output:
                killer_inputs.add(jinja_inp)
                mutant_killed+=1
                killed_list.add(i)
                print("killed list:",killed_list,"Mutant killed!")
            inp_coverage.append(test_cover)

        iter_output_log[jinja_inp].append(mutant_killed)
        iter_output_log[jinja_inp].append(max(inp_coverage))        
        iter_death += iter_output_log[jinja_inp][0]
        iter_cov = max([iter_cov,iter_output_log[jinja_inp][1]])
        print("for input:"+jinja_inp+":coverage was:"+str(test_cover)+":and mutants killed were:"+str(mutant_killed)+":out of:"+str(len(mutant_srcs) - len(killed_list)))

    print("baseline for mutant killing")
    print("Current stats:")
    print(iter_output_log)
    #get top k values where k is 25%. 
    top_k = sorted(iter_output_log.items(), key = lambda item: item[1][1])
    global_output_log[tot] = [mut_limit - iter_death, iter_cov]
    top_global = sorted(global_output_log.items(), key = lambda item: item[1][1])[0]
    if len(killer_inputs) != 0:
        hybrid_prob_grammar = mutant_grammar_gen.modify_vec(hybrid_prob_grammar, "mined", list(killer_inputs)) 
    samples = []
    for k,v in top_k:
        if top_global[1][1] < v[1]:
            samples.append(k)
    if len(samples) < len(iter_output_log)//4:
        #random changes if not enough inputs that increase coverage
        cov_prob_grammar = mutant_grammar_gen.modify_vec(cov_prob_grammar, "random")
    else:
        cov_prob_grammar = mutant_grammar_gen.modify_vec(cov_prob_grammar, "mined", samples)
    

print(global_output_log)

y_kill=[mut_limit]
y_kill += list(map(lambda x: global_output_log[x][0] ,global_output_log))
x_kill = range(len(y_kill))

y_cov = [0]
y_cov += list(map(lambda x: global_output_log[x][1] ,global_output_log))
x_cov = range(len(y_cov))

plt.plot(x_kill,y_kill,color='red', marker='o')
plt.title("Speed of update of inputs via hybrid")
plt.xlabel("Number of total iterations")
plt.ylabel("Mutants Remaining")
plt.xticks(range(len(x_kill)+1))
plt.grid(True)
plt.savefig("hybrid_based_killed.png")
plt.clf()

plt.plot(x_cov,y_cov,color='green', marker='o')
plt.title("Speed of update of inputs via hybrid")
plt.xlabel("Number of total iterations")
plt.ylabel("Coverage")
plt.xticks(range(len(x_cov)+1))
plt.grid(True)
plt.savefig("hybrid_based_cov.png")
plt.clf()

runner.stop()
    #TODO add logging to collect results
    #TODO add coverage information for results
    #parser flow 
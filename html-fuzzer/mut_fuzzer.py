import sys
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
from html_grammar import HTML_GRAMMAR

from fuzzingbook.Grammars import *
from fuzzingbook.GrammarFuzzer import GrammarFuzzer
from fuzzingbook.ProbabilisticGrammarFuzzer import *

#functions to generate mutants from
from html5lib import html5parser #main parser entry point filename html5lib-python-master/html5parser.py
from html5lib.treebuilders import etree #parser tree generations html5lib-python-master/treebuilders/etree.py
from html5lib import _tokenizer #parser token generation html5lib-python-master/_tokenizer.py

client = docker.from_env()
runner = client.containers.run("fuzzer-runner", working_dir = "/app/html-fuzzer",
command = "/bin/bash", tty=True, 
detach = True, auto_remove = True, volumes={os.path.dirname(os.getcwd()): {'bind': '/app', 'mode': 'rw'}} )

def test_env(sample):
    #start container only once
    #recompile code with pip, but don't keep recreating containers
    
    # client = docker.from_env()
    # runner = client.containers.run("fuzzer-runner", working_dir = "/app/html-fuzzer",
    # command = ["/bin/bash","-c", "pip -qqq install -e ./html5lib-python-mutate && python3 html_tester.py "+"'"+sample+"'"], 
    # detach = True, auto_remove = True, volumes={os.path.dirname(os.getcwd()): {'bind': '/app', 'mode': 'rw'}} )
    # runner.start()
    runner.exec_run("pip -qqq install -e ./html5lib-python-mutate")
    r = runner.exec_run("python3 html_tester.py "+"'"+sample+"'")
    print(r.output)
    return r.output.decode("utf-8")
    output_str = ''

    # for line in runner.logs(stream=True):
    #     print("stuck")
    #     output_str += line.decode("utf-8")
    # #log_string = runner.logs()
    # return output_str
# print(htmlparser_fns)
# print(htmltree_fns)
# print(htmltokenizer_fns)
htmlparser_path = "html5lib-python-mutate/html5lib/html5parser.py"
htmltree_path = "html5lib-python-mutate/html5lib/treebuilders/etree.py"
htmltokenizer_path = "html5lib-python-mutate/html5lib/_tokenizer.py"

htmlparser_to_fuzz = open(htmlparser_path)
htmltree_to_fuzz = open(htmltree_path)
htmltokenizer_to_fuzz = open(htmltokenizer_path)

htmlparser_seed = htmlparser_to_fuzz.read()
htmltree_seed = htmltree_to_fuzz.read()
htmltokenizer_seed = htmltokenizer_to_fuzz.read()

hybrid_prob_grammar = copy.deepcopy(HTML_GRAMMAR)
random_prob_grammar = copy.deepcopy(HTML_GRAMMAR)

baseline_fuzz = GrammarFuzzer(HTML_GRAMMAR, max_nonterminals=5)
samples = []

for i in range(10):
    sample = baseline_fuzz.fuzz()
    if sample not in samples:
        samples.append(baseline_fuzz.fuzz())

hybrid_prob_grammar = mutant_grammar_gen.random_vector_gen(hybrid_prob_grammar, "sample", samples)
random_prob_grammar = mutant_grammar_gen.random_vector_gen(random_prob_grammar, "sample", samples)

global_output_log = defaultdict(list)

max_coverage = 0
LAMBDA = lambda:0
tot_death = 0
tot = 0

## save mutant_srcs - as we have an exhaustive list of mutants for every fuzzer iteration, it is more efficient to run it outside the fuzzer iterations 
mutant_srcs = []
mutant_pm_srcs = []

for mutant in mutant_creator.MuFunctionAnalyzer(etree): ## fn[0] is the function name. We need to pass the function, so take fn[1]
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
    random_gen = ProbabilisticGrammarFuzzer(random_prob_grammar,  max_nonterminals=5)

    #for i in range(int(sys.argv[2])): #accept command line argument for number of inputs per grammar
        # print(inputs)
    inp_count=0
    while True:
        if len(inputs) == int(sys.argv[2]) or inp_count > int(sys.argv[2])*int(sys.argv[2]):
            break    
        inputs.add(random_gen.fuzz())
        inputs.add(hybrid_gen.fuzz())
        inp_count+=1


    killer_inputs = set()
    print("# inputs ", len(inputs))
    # reset for every iteration
    max_coverage = 0

    for html_inp in inputs:
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
            mutated_file = open(htmltree_path,'w')
            mutated_file.write(mutated_prog)
            mutated_file.close()
            
            out = subprocess.Popen([sys.executable, "html_tester.py",html_inp],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            fuzzout, errors = out.communicate()
            fuzzout = fuzzout.decode("utf-8").split(":-")
            correct_cov=''
            correct_output=''
            if len(fuzzout) == 2:
                correct_cov = fuzzout[1]
                correct_output = fuzzout[0]            
            print(html_inp)
            output_str = test_env(html_inp)
            print(output_str)
            print(fuzzout)

            test_output=''
            testout = output_str.split(":-")
            print("testout:",testout)
            test_cover = 1 #min coverage 1 to avoid divide by zero error
            # inp_coverage.append(1)
            if len(testout) == 2:
                test_output = testout[0]
                test_cover = int(testout[1])

            if correct_output != test_output:
                killer_inputs.add(html_inp)
                mutant_killed+=1
                killed_list.add(i)
                print("killed list:",killed_list,"Mutant killed!")
            inp_coverage.append(test_cover)

        iter_output_log[html_inp].append(mutant_killed)
        iter_output_log[html_inp].append(max(inp_coverage))        
        iter_death += iter_output_log[html_inp][0]
        iter_cov = max([iter_cov,iter_output_log[html_inp][1]])
        print("for input:"+html_inp+":coverage was:"+str(test_cover)+":and mutants killed were:"+str(mutant_killed)+":out of:"+str(len(mutant_srcs) - len(killed_list)))

    print("baseline for mutant killing")
    print("Current stats:")
    print(iter_output_log)

    if len(killer_inputs) != 0:
        hybrid_prob_grammar = mutant_grammar_gen.modify_vec(hybrid_prob_grammar, "mined", list(killer_inputs)) 
    random_prob_grammar = mutant_grammar_gen.modify_vec(random_prob_grammar, "random")
    

print(global_output_log)

y_kill=[mut_limit]
y_kill += list(map(lambda x: global_output_log[x][0] ,global_output_log))
x_kill = range(len(y_kill))

y_cov = [0]
y_cov += list(map(lambda x: global_output_log[x][1] ,global_output_log))
x_cov = range(len(y_cov))

plt.plot(x_kill,y_kill,color='red', marker='o')
plt.title("Speed of update of inputs via randomness")
plt.xlabel("Number of total iterations")
plt.ylabel("Mutants Remaining")
plt.xticks(range(len(x_kill)+1))
plt.grid(True)
plt.savefig("mut_based_killed.png")
plt.clf()

plt.plot(x_cov,y_cov,color='green', marker='o')
plt.title("Speed of update of inputs via randomness")
plt.xlabel("Number of total iterations")
plt.ylabel("Coverage")
plt.xticks(range(len(x_cov)+1))
plt.grid(True)
plt.savefig("mut_based_cov.png")
plt.clf()

runner.stop()
    #TODO add logging to collect results
    #TODO add coverage information for results
    #parser flow 
    #html5parser => etree => tokenizer => inputstream 
#json parser fuzzer
#usage instructions
# python3 json_mutant_fuzzer.py <number of iterations to kill mutants> <number of inputs per grammar>

import mutant_creator
import mutant_grammar_gen

from fuzzingbook.Grammars import *
from fuzzingbook.GrammarFuzzer import GrammarFuzzer
from fuzzingbook.ProbabilisticGrammarFuzzer import *

import subprocess
import sys
import json
from collections import defaultdict
import hashlib
import copy 

#get functions to mutate from parser to fuzz
from inspect import getmembers, isfunction
import json_parser

# for computing coverage
from fuzzingbook.Coverage import Coverage
import json_parser_mutated

fns = getmembers(json_parser, isfunction)
print(fns)

parser_to_fuzz = open("json_parser.py")
mutant_seed = parser_to_fuzz.read()
killer_inputs = set()
# inp_gen = ProbabilisticGrammarFuzzer(JSON_GRAMMAR)

#generate probabilistic grammar
#we use mutliple grammars to offset fixed directions caused by killing only particular kinds of mutants
 
uniform_prob_grammar = copy.deepcopy(JSON_GRAMMAR)
dumb_prob_grammar = copy.deepcopy(JSON_GRAMMAR)
mined_prob_grammar = copy.deepcopy(JSON_GRAMMAR)

baseline_fuzz = GrammarFuzzer(JSON_GRAMMAR)
samples = []

for i in range(100):
    sample = baseline_fuzz.fuzz()
    if sample not in samples:
        samples.append(baseline_fuzz.fuzz())

uniform_prob_grammar = mutant_grammar_gen.random_vector_gen(uniform_prob_grammar,"uniform")
dumb_prob_grammar = mutant_grammar_gen.random_vector_gen(dumb_prob_grammar,"dumb")
mined_prob_grammar = mutant_grammar_gen.random_vector_gen(mined_prob_grammar, "sample", samples)

global_output_log = defaultdict(list)

max_coverage = 0
LAMBDA = lambda:0
tot_death = 0
tot = 0

## save mutant_srcs - as we have an exhaustive list of mutants for every fuzzer iteration, it is more efficient to run it outside the fuzzer iterations 
mutant_srcs = []
mutant_pm_srcs = []
for fn in fns:
    if isinstance(fn[1], type(LAMBDA)) and fn[1].__name__ == LAMBDA.__name__: #check if fn is lambda fn, dont consider that
        continue
    for mutant in mutant_creator.MuFunctionAnalyzer(fn[1]): ## fn[0] is the function name. We need to pass the function, so take fn[1]
        mutant_srcs.append(mutant.src())
        mutant_pm_srcs.append(len(mutant.pm.src.split('\n')))
        
for i in range(int(sys.argv[1])): #limit iterations of fuzzer
    iter_death = 0
    iter_tot = 0
    iter_output_log = defaultdict(list)

    uniform_gen = ProbabilisticGrammarFuzzer(uniform_prob_grammar, max_nonterminals=5)
    dumb_gen = ProbabilisticGrammarFuzzer(dumb_prob_grammar,  max_nonterminals=5)
    mined_gen = ProbabilisticGrammarFuzzer(mined_prob_grammar,  max_nonterminals=5)

    inputs = set()
    # print(uniform_prob_grammar)
    # print(dumb_prob_grammar)
    # print(mined_prob_grammar)
    #generate inputs for fuzzer
    #TODO timeout if input generation takes too long
    for i in range(int(sys.argv[2])): #accept command line argument for number of inputs per grammar
        print(inputs)
        inputs.add(uniform_gen.fuzz())
        inputs.add(dumb_gen.fuzz())
        inputs.add(mined_gen.fuzz())

    print("# inputs ", len(inputs))
    # reset for every iteration
    max_coverage = 0
    for i,m in enumerate(mutant_srcs):   
        #mutant.src is mutated function, mutant.prm.src is original function        
        #Here we append mutated function to file before entry point function, thus overwriting the non mutated implementation
        #currently one mutation available (adding a return statement)
        mutated_prog = mutant_seed.split("value_parser = ")[0]+"\n"+m+"\n" + "value_parser = " + mutant_seed.split("value_parser = ")[1]
        mutated_file = open('json_parser_mutated.py','w')
        mutated_file.write(mutated_prog)
        mutated_file.close()
        non_blank_count_lines = 0
        
        with open('json_parser_mutated.py') as f:
            for line in f:
                if line.strip():
                    non_blank_count_lines += 1
        #tot += 1 #TODO 
        iter_tot += 1
        # we need to subtract the lines in the original function to avoid duplicate counting
        #print("non blank lines",non_blank_count_lines - len(mutant.pm.src.split('\n')))
        non_blank_count_lines -= mutant_pm_srcs[i]
        for fi in inputs:
            json_inp = json.dumps(fi)
            json_inp_file = open("json_inp.json","w")
            json_inp_file.write(json_inp)
            json_inp_file.close()
            with Coverage() as cov_fuzz:
                try:
                    json_parser_mutated.value_parser(fi.strip())
                except:
                    pass
            #print("Coverage ", cov_fuzz.coverage(), len(cov_fuzz.coverage()))
            max_coverage = max(round(len(cov_fuzz.coverage())/non_blank_count_lines,2),max_coverage)
            out = subprocess.Popen([sys.executable,"json_parser_test.py"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            fuzzout, errors = out.communicate()
            iter_output_log[hashlib.sha1(mutated_prog.encode()).hexdigest()].append((fi,fuzzout.decode("utf-8"),errors))
            global_output_log[hashlib.sha1(mutated_prog.encode()).hexdigest()].append((fi,fuzzout.decode("utf-8"),errors))
            
            if errors:
                killer_inputs.add(fi)
                print("Mutant killed")
                break #break out of the input loop if a mutant is killed, another input is only interesting to us if it kills more mutants, otherwise it belongs to the same equivalence class
    #TODO add logging to collect results
    #TODO add coverage information for results
    print("killer inputs\n", killer_inputs)
    print("inputs\n", inputs) 
    print("Number of mutants killed in iteration:",len(iter_output_log.keys()), "out of", iter_tot)
    print("Score per iteration (number of mutants killed in the iteration divided by the max coverage found in that iteration):",round((len(iter_output_log.keys())/iter_tot)/max_coverage,2)) 
    #print("Number of mutants killed total:",len(global_output_log.keys()), "out of", tot)
    #change inputs based on killer inputs
    dumb_prob_grammar = mutant_grammar_gen.modify_vec(dumb_prob_grammar, "random")
    uniform_prob_grammar = mutant_grammar_gen.modify_vec(uniform_prob_grammar, "random")
    mined_prob_grammar = mutant_grammar_gen.modify_vec(mined_prob_grammar, "mined", list(killer_inputs))

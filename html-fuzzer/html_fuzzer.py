import sys
import docker
import subprocess
from collections import defaultdict
import copy
from inspect import getmembers, isfunction
import os

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

# htmlparser_fns = getmembers(HTMLParser, isfunction)
# htmltree_fns = getmembers(etree, isfunction)
# htmltokenizer_fns = getmembers(_tokenizer, isfunction)
def test_env(sample):
    #start container only once
    #recompile code with pip, but don't keep recreating containers
    
    client = docker.from_env()
    runner = client.containers.run("fuzzer-runner", working_dir = "/app/html-fuzzer",
    command = ["/bin/bash","-c", "pip -qqq install -e ./html5lib-python-master && python3 html_tester.py "+"'"+sample+"'"], 
    detach = True, auto_remove = True, volumes={os.path.dirname(os.getcwd()): {'bind': '/app', 'mode': 'rw'}} )
    output_str = ''
    for line in runner.logs(stream=True):
        output_str += line.decode("utf-8")
    #log_string = runner.logs()
    return output_str
# print(htmlparser_fns)
# print(htmltree_fns)
# print(htmltokenizer_fns)
htmlparser_path = "html5lib-python-master/html5lib/html5parser.py"
htmltree_path = "html5lib-python-master/html5lib/treebuilders/etree.py"
htmltokenizer_path = "html5lib-python-master/html5lib/_tokenizer.py"

htmlparser_to_fuzz = open(htmlparser_path)
htmltree_to_fuzz = open(htmltree_path)
htmltokenizer_to_fuzz = open(htmltokenizer_path)

htmlparser_seed = htmlparser_to_fuzz.read()
htmltree_seed = htmltree_to_fuzz.read()
htmltokenizer_seed = htmltokenizer_to_fuzz.read()


# inp_gen = ProbabilisticGrammarFuzzer(JSON_GRAMMAR)

#generate probabilistic grammar
#we use mutliple grammars to offset fixed directions caused by killing only particular kinds of mutants
 
uniform_prob_grammar = copy.deepcopy(HTML_GRAMMAR)
dumb_prob_grammar = copy.deepcopy(HTML_GRAMMAR)
mined_prob_grammar = copy.deepcopy(HTML_GRAMMAR)

baseline_fuzz = GrammarFuzzer(HTML_GRAMMAR, max_nonterminals=5)
samples = []

for i in range(10):
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
# print(inspect.getsource(HTMLParser))

# for fn in htmlparser_fns:
#     print(fn[1].__name__)
#     if (isinstance(fn[1], type(LAMBDA)) and fn[1].__name__ == LAMBDA.__name__): #check if fn is lambda fn or init, dont consider that
#         continue
for mutant in mutant_creator.MuFunctionAnalyzer(etree): ## fn[0] is the function name. We need to pass the function, so take fn[1]
    mutant_srcs.append(mutant.src())
    mutant_pm_srcs.append(len(mutant.pm.src.split('\n')))        


# mutated_prog = htmlparser_seed.split(signature)[0]
# print(mutated_prog)
# mutated_file = open('json_parser_mutated.py','w')
# mutated_file.write(mutated_prog)
# mutated_file.close()

# for fn in htmltree_fns:
#     if isinstance(fn[1], type(LAMBDA)) and fn[1].__name__ == LAMBDA.__name__: #check if fn is lambda fn, dont consider that
#         continue
#     for mutant in mutant_creator.MuFunctionAnalyzer(fn[1]): ## fn[0] is the function name. We need to pass the function, so take fn[1]
#         mutant_srcs.append(mutant.src())
#         mutant_pm_srcs.append(len(mutant.pm.src.split('\n')))

# for fn in htmltokenizer_fns:
#     if isinstance(fn[1], type(LAMBDA)) and fn[1].__name__ == LAMBDA.__name__: #check if fn is lambda fn, dont consider that
#         continue
#     for mutant in mutant_creator.MuFunctionAnalyzer(fn[1]): ## fn[0] is the function name. We need to pass the function, so take fn[1]
#         mutant_srcs.append(mutant.src())
#         mutant_pm_srcs.append(len(mutant.pm.src.split('\n')))


mutant_srcs = mutant_srcs[:50]

for i in range(int(sys.argv[1])): #limit iterations of fuzzer
    iter_death = 0
    iter_tot = 0
    iter_output_log = defaultdict(list)

    uniform_gen = ProbabilisticGrammarFuzzer(uniform_prob_grammar, max_nonterminals=5)
    dumb_gen = ProbabilisticGrammarFuzzer(dumb_prob_grammar,  max_nonterminals=5)
    mined_gen = ProbabilisticGrammarFuzzer(mined_prob_grammar,  max_nonterminals=5)

    inputs = set()
    dumbinputs = set()
    uniforminputs = set()
    print("inside fuzzing loop")
    # print(uniform_prob_grammar)
    # print(dumb_prob_grammar)
    # print(mined_prob_grammar)
    #generate inputs for fuzzer
    #TODO timeout if input generation takes too long
    for i in range(int(sys.argv[2])): #accept command line argument for number of inputs per grammar
        # print(inputs)
        inputs.add(uniform_gen.fuzz())
        dumbinputs.add(dumb_gen.fuzz())
        inputs.add(mined_gen.fuzz())
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
        inp_coverage=[] 
        killed_list = set()

        for i,m in enumerate(mutant_srcs):   
            #mutant.src is mutated function, mutant.prm.src is original function        
            #Here we append mutated function to file before entry point function, thus overwriting the non mutated implementation
            #currently one mutation available (adding a return statement)
            if i == 5:
                break
            mutated_prog = m
            mutated_file = open(htmltree_path,'w')
            mutated_file.write(mutated_prog)
            mutated_file.close()
            
            iter_tot += 1
            out = subprocess.Popen([sys.executable, "html_tester.py",html_inp],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            fuzzout, errors = out.communicate()
            fuzzout = fuzzout.decode("utf-8").split(":-")
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
            inp_coverage.append(1)
            if len(testout) == 2:
                test_output = testout[0]
                test_cover = int(testout[1])

            if correct_output != test_output:
                killer_inputs.add(html_inp)
                inp_coverage.append(test_cover)
                mutant_killed+=1
                killed_list.add(i)
                print("killed list:",killed_list,"Mutant killed!")
        
        iter_output_log[html_inp].append(mutant_killed/max(inp_coverage))
        print("for input:"+html_inp+":coverage was:"+str(test_cover)+":and mutants killed were:"+str(mutant_killed)+":out of:"+str(len(mutant_srcs)))
        
        #delete dead mutants
        for index in killed_list:
            del mutant_srcs[index]

    dumb_prob_grammar = mutant_grammar_gen.modify_vec(dumb_prob_grammar, "random")
    uniform_prob_grammar = mutant_grammar_gen.modify_vec(uniform_prob_grammar, "random")
    if len(killer_inputs) != 0: #don't change grammar if no killer inputs
        mined_prob_grammar = mutant_grammar_gen.modify_vec(mined_prob_grammar, "mined", list(killer_inputs))
    print("recalibrated grammars for mutant killing")
    print("Current stats:")
    print(iter_output_log)

    #TODO add logging to collect results
    #TODO add coverage information for results
    #parser flow 
    #html5parser => etree => tokenizer => inputstream 
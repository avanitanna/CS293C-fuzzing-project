import json
import sys
import threading
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
from html_grammar import HTML_GRAMMAR
import logging

from fuzzingbook.Grammars import *
from fuzzingbook.GrammarFuzzer import GrammarFuzzer
from fuzzingbook.ProbabilisticGrammarFuzzer import *

#functions to generate mutants from
from html5lib import html5parser #main parser entry point filename html5lib-python-master/html5parser.py
from html5lib.treebuilders import etree #parser tree generations html5lib-python-master/treebuilders/etree.py
from html5lib import _tokenizer #parser token generation html5lib-python-master/_tokenizer.py

#globals
format = "%(asctime)s: %(levelname)s: %(funcName)s: %(message)s"
logging.basicConfig(filename='html-fuzzer-cov-'+str(sys.argv[1])+'-'+str(sys.argv[2])+'-'+str(sys.argv[3])+'.log', 
filemode='w',format=format, level=logging.INFO, datefmt="%H:%M:%S")

client = docker.from_env()

ds = threading.Semaphore()

iter_output_log = defaultdict(list)

def update_ds(inp, cov, incr):
    global iter_output_log
    cov=int(cov.rstrip())
    ds.acquire()
    if inp not in iter_output_log.keys():
        iter_output_log[inp] = [incr, cov]
    else:
        iter_output_log[inp] = [iter_output_log[inp][0]+incr,max([iter_output_log[inp][1],cov])]
    ds.release()

def create_container():
    runner = client.containers.run("fuzzer-runner", working_dir = "/app/html-fuzzer",
    command = "/bin/bash", tty=True, 
    detach = True, auto_remove = True, volumes={os.path.dirname(os.getcwd()): {'bind': '/app', 'mode': 'rw'}} )
    return runner

def install_mutant(runner, mutant, mutant_path):
    f=open(mutant_path,"w")
    f.write(mutant)
    f.close()
    runner.exec_run("cp -r ./html5lib-python-mutate /")
    runner.exec_run("pip -qqq install -e /html5lib-python-mutate")

def test_env(runner,samples,ind):
    #start container only once
    #recompile code with pip, but don't keep recreating containers
    for sample in samples:
        r = runner.exec_run("python3 html_tester.py "+"'"+sample+"'")
        mut_out = r.output.decode("utf-8")
        out = subprocess.Popen([sys.executable, "html_tester.py",sample],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        org_out, errors = out.communicate()
        mut_out = mut_out.split(":-")
        org_out = org_out.decode("utf-8").split(":-")
        logging.info("for original code input:"+sample+":original code output:"+str(org_out[0]))
        logging.info("For mutated code input:"+sample+":mutated code output:"+str(mut_out[0]))
        if len(org_out) == 2:
            if len(mut_out) == 2:
                if org_out[0] != mut_out[0]:
                    killed_list.add(ind)
                    killer_inputs.add(sample)
                    logging.info("Mutant killed with"+sample+"! Current mutant killed list:"+str(killed_list))
                    update_ds(sample,mut_out[1],1)
                    break
                else:
                    update_ds(sample,mut_out[1],0)
            elif "invalid" in mut_out[0]:
                    killed_list.add(ind)
                    killer_inputs.add(sample)
                    logging.info("Mutant killed with"+sample+"! Current mutant killed list:"+str(killed_list))
                    update_ds(sample,mut_out[1],1)
                    break
        else:
            logging.log("Input:"+sample+":Found a real bug!")
htmltree_path = "html5lib-python-mutate/html5lib/treebuilders/etree.py"
htmltree_to_fuzz = open(htmltree_path)
htmltree_seed = htmltree_to_fuzz.read()



baseline_fuzz = GrammarFuzzer(HTML_GRAMMAR, max_nonterminals=5)
samples = []
for i in range(10):
    sample = baseline_fuzz.fuzz()
    if sample not in samples:
        samples.append(baseline_fuzz.fuzz())

cov_prob_grammar = copy.deepcopy(HTML_GRAMMAR)
cov_prob_grammar = mutant_grammar_gen.random_vector_gen(cov_prob_grammar, "sample", samples)
# random_prob_grammar = copy.deepcopy(HTML_GRAMMAR)
# random_prob_grammar = mutant_grammar_gen.random_vector_gen(random_prob_grammar, "sample", samples)

global_output_log = defaultdict(list)

max_coverage = 0
LAMBDA = lambda:0
tot_death = 0
tot = 0

## save mutant_srcs - as we have an exhaustive list of mutants for every fuzzer iteration, it is more efficient to run it outside the fuzzer iterations 
mutant_srcs = []
mutant_pm_srcs = []
mut_limit = int(sys.argv[3])


strategy = sys.argv[5]
if strategy == "mixed":
    del_mut = []
    ret_mut = []
    ds_mut = []
    if_mut = []

    for mutant in mutant_creator.MuFunctionAnalyzer(etree, strategy="return"): ## fn[0] is the function name. We need to pass the function, so take fn[1]
        ret_mut.append(mutant.src())

    for mutant in mutant_creator.MuFunctionAnalyzer(etree, strategy="condition"): ## fn[0] is the function name. We need to pass the function, so take fn[1]
        if_mut.append(mutant.src())

    for mutant in mutant_creator.MuFunctionAnalyzer(etree, strategy="ds"): ## fn[0] is the function name. We need to pass the function, so take fn[1]
        ds_mut.append(mutant.src())

    for mutant in mutant_creator.MuFunctionAnalyzer(etree): ## fn[0] is the function name. We need to pass the function, so take fn[1]
        del_mut.append(mutant.src())
    
    min_len = min([len(if_mut), len(ret_mut), len(ds_mut), len(del_mut)])

    for i in range(mut_limit):
        ret_rand = random.randint(0,len(ret_mut)-1)
        del_rand = random.randint(0,len(del_mut)-1)
        if_rand = random.randint(0,len(if_mut)-1)
        ds_rand = random.randint(0,len(ds_mut)-1)

        if ret_mut[ret_rand] not in mutant_srcs:
            mutant_srcs.append(ret_mut[ret_rand])

        if del_mut[del_rand] not in mutant_srcs:
            mutant_srcs.append(del_mut[del_rand])

        if if_mut[if_rand] not in mutant_srcs:
            mutant_srcs.append(if_mut[if_rand])

        if ds_mut[ds_rand] not in mutant_srcs:
            mutant_srcs.append(ds_mut[ds_rand])


else:
    for mutant in mutant_creator.MuFunctionAnalyzer(etree, strategy=strategy): ## fn[0] is the function name. We need to pass the function, so take fn[1]
        mutant_srcs.append(mutant.src())

if mut_limit > len(mutant_srcs):
    mut_limit = len(mutant_srcs)    
    print("Given argument too large for possible mutants, changing to", mut_limit)
mutant_srcs = mutant_srcs[:mut_limit]
killed_list = set()
iter_death = 0
scale_factor = int(sys.argv[4])

if scale_factor > mut_limit:
    print("INVALID SCALE FACTOR CAN'T BE GREATER THAN MUTATION LIMIT")
    exit()

runners=[]
#create docker containers
if len(runners) == 0:
    for i in range(scale_factor):
        runners.append(create_container())

for i in range(int(sys.argv[1])): #limit iterations of fuzzer
    iter_output_log = defaultdict(list)
    iter_cov = 0
    tot+=1
    inputs = set()
    inp_count=0
    cov_gen = ProbabilisticGrammarFuzzer(cov_prob_grammar,  max_nonterminals=5)
    # rand_gen = ProbabilisticGrammarFuzzer(random_prob_grammar,  max_nonterminals=5)

    while True:
        if len(inputs) >= int(sys.argv[2]) or inp_count > int(sys.argv[2])*int(sys.argv[2]):
            break    
        inputs.add(cov_gen.fuzz())
        # inputs.add(rand_gen.fuzz())
        inp_count+=1

    start = time.time()
    killer_inputs = set()
    logging.info("for iteration:"+str(tot)+":number of inputs:"+str(len(inputs)))
    # reset for every iteration
    max_coverage = 0
    ind=0
    while ind < len(mutant_srcs):
        if ind not in killed_list:
            threads = [0]*scale_factor
            runner_ind = 0
            while runner_ind < scale_factor:
                if ind not in killed_list:
                    if ind < len(mutant_srcs):
                        #install mutant
                        install_mutant(runners[runner_ind], mutant_srcs[ind], htmltree_path)
                        #start thread
                        threads[runner_ind]=threading.Thread(target=test_env, args=(runners[runner_ind], inputs, ind,), daemon=True)
                        threads[runner_ind].start()
                    else:
                        break
                ind+=1
                runner_ind+=1
                    
            #wait for threads to finish
            for x in threads:
                if x!=0:
                    x.join()
        else:
            ind+=1
    logging.info("iteration log:"+json.dumps(iter_output_log))
    print("iteration:"+str(tot)+" completed in "+str(time.time()-start))
    if len(killed_list) == mut_limit and len(iter_output_log)==0:
        print("all mutants died before specified iterations completetion")
        break
    iter_cov = max(list(map(lambda x: iter_output_log[x][1], iter_output_log)))
    global_output_log[tot] = [mut_limit -  len(killed_list) , iter_cov]
    #get top k coverage for inputs
    top_k = sorted(iter_output_log.items(), key = lambda item: item[1][1])
    top_global = sorted(global_output_log.items(), key = lambda item: item[1][1])[0]
    new_inputs = []
    for k,v in top_k:
        if top_global[1][1] < v[1]:
            new_inputs.append(k)
    if len(new_inputs) < len(iter_output_log)//4:
        cov_prob_grammar = mutant_grammar_gen.modify_vec(cov_prob_grammar, "mined", samples)
    else:
        #random changes if enough inputs increase coverage
        cov_prob_grammar = mutant_grammar_gen.modify_vec(cov_prob_grammar, "random")

logging.info("global iteration stats:"+json.dumps(global_output_log))

y_kill=[mut_limit]
y_kill += list(map(lambda x: global_output_log[x][0] ,global_output_log))
x_kill = range(len(y_kill))

y_cov = [0]
y_cov += list(map(lambda x: global_output_log[x][1] ,global_output_log))
x_cov = range(len(y_cov))

plt.figure(figsize=(10,10))
plt.plot(x_kill,y_kill,color='red', marker='o')
plt.title("HTML Cov Guided Fuzzer")
plt.xlabel("Number of total iterations")
plt.ylabel("Mutants Remaining")
plt.xticks(range(len(x_kill)+1))
plt.yticks(range(len(mutant_srcs)+1))
plt.grid(True)
plt.savefig(strategy+"/html_cov/mutant_"+str(sys.argv[1])+"_"+str(sys.argv[2])+"_"+str(sys.argv[3])+".png")
plt.clf()


plt.plot(x_cov,y_cov,color='green', marker='o')
plt.title("HTML Cov Guided Fuzzer")
plt.xlabel("Number of total iterations")
plt.ylabel("Coverage")
plt.xticks(range(len(x_cov)+1))
plt.grid(True)
plt.savefig(strategy+"/html_cov/cov_"+str(sys.argv[1])+"_"+str(sys.argv[2])+"_"+str(sys.argv[3])+".png")
plt.clf()

print("safe to kill process only cleaning up containers now")
#clean up docker containers
for runner in runners:
    runner.stop()
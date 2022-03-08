from fuzzingbook.Grammars import *
from fuzzingbook.GrammarFuzzer import GrammarFuzzer
from fuzzingbook.ProbabilisticGrammarFuzzer import *
# from fuzzingbook.Fuzzer import Fuzzer
# from fuzzingbook.GrammarFuzzer import GrammarFuzzer, all_terminals, display_tree, DerivationTree
# from fuzzingbook.Grammars import is_valid_grammar, EXPR_GRAMMAR, START_SYMBOL, crange
# from fuzzingbook.Grammars import opts, exp_string, exp_opt, set_opts
# from fuzzingbook.Grammars import Grammar, Expansion
# from typing import List, Dict, Set, Optional, cast, Any, Tuple

import importlib
import sys
import numpy as np
import random

def mined_prob_gen(sample_inputs, grammar_module):
    probabilistic_grammar_miner = ProbabilisticGrammarMiner(
    EarleyParser(grammar_module))
    probabilistic_cgi_grammar = probabilistic_grammar_miner.mine_probabilistic_grammar(sample_inputs)
    return probabilistic_cgi_grammar

def uniform_prob_gen(vec_len):
    prob_vec = np.random.random(vec_len)
    prob_vec /= prob_vec.sum()
    return list(prob_vec)

def dumb_prob_gen(vec_len):
    #returns a probability vector which sums up to 1
    #intentionally meant to be non uniform
    prob_vector = []
    prob = 0
    zero_count = 0
    while len(prob_vector) != vec_len:
        if len(prob_vector) == 0 and vec_len != 1:
            rand_prob = round(random.random(),2)
            prob_vector.append(rand_prob)
        elif vec_len == 1:
            prob_vector.append(1)
        elif len(prob_vector)+1 == vec_len:
            prob_vector.append(round(1-sum(prob_vector),2))
        else:
            rand_prob = round(random.uniform(0, 1 - sum(prob_vector)),2)
            prob_vector.append(rand_prob) 
            if rand_prob == 0.0:
                zero_count+=1
    #randomly flip vector
    if zero_count < random.randint(0,len(prob_vector)):
        # print("flipped")
        prob_vector.reverse()
    if round(sum(prob_vector)) != 1:
        print(prob_vector, "invalid\n")

    return prob_vector

def random_vector_gen(grammar_module, prob_type, samples=None):
    #returns probability grammar
    if prob_type == "uniform":
        for vec in grammar_module.keys():
            prob_vec = uniform_prob_gen(len(grammar_module[vec]))
            for term in range(0,len(prob_vec)):
                set_prob(grammar_module, vec, grammar_module[vec][term],prob_vec[term])
        return grammar_module
    
    elif prob_type == "dumb":
        for vec in grammar_module.keys():
            prob_vec = dumb_prob_gen(len(grammar_module[vec]))
            for term in range(0,len(prob_vec)):
                set_prob(grammar_module, vec, grammar_module[vec][term],prob_vec[term])
        return grammar_module

    elif prob_type == "sample" and samples:
        return mined_prob_gen(samples, grammar_module)

def mutate_vector_gen(prob_vector1,  mutation_type, pos=None):
    #mutate the probability vector of a known mutant killer
    #mutation types:
    # shuffle - swap random positions in the vector, ignores pos
    # plus - increases position (pos) in vector by random amount (decrements the rest)
    # minus - decreases position (pos) in vector by random amount (increments the rest)
    # reverse - reverse vector, ignores pos

    if mutation_type=="swap":
        random.shuffle(prob_vector1)
        return prob_vector1

    elif mutation_type=="plus" and ( pos >=0 and pos < len(prob_vector1) ):
        #value to increment by must be < smallest probability (prevent negative probability)
        #value to increment by must be < 1-greatest probabilty (prevent >1 probability)
        min_prob = min([1-max(prob_vector1),min(prob_vector1)])
        inc = random.uniform(0.0,min_prob)
        prob_vector1[pos] += inc
        if pos != 0:
            prob_vector1[random.choice(list(range(0,pos)))] -= inc
        else:
            prob_vector1[random.choice(list(range(pos,len(prob_vector1))))] -= inc
        # for i in range(0,len(prob_vector1)):
        #     if i == pos:
        #         prob_vector1[i] += inc
        #     else:
        #         prob_vector1[i] -= inc
        return prob_vector1
    
    elif mutation_type=="minus" and ( pos >=0 and pos < len(prob_vector1) ):
        #value to decrement by must be < smallest probability (prevent negative probability)
        #value to decrement by must be < 1-smallest probabilty (prevent >1 probability)
        # print(min(prob_vector1))
        min_prob = min([1-min(prob_vector1),min(prob_vector1)])
        inc = random.uniform(0,min_prob)
        prob_vector1[pos] -= inc
        if pos != 0:
            prob_vector1[random.choice(list(range(0,pos)))] += inc
        else:
            prob_vector1[random.choice(list(range(pos,len(prob_vector1))))] += inc
        # for i in range(0,len(prob_vector1)):
        #     if i == pos:
        #         prob_vector1[i] -= inc
        #     else:
        #         prob_vector1[i] += inc
        return prob_vector1

    elif mutation_type=="reverse":
        prob_vector1.reverse()
        return prob_vector1

def modify_vec(grammar_module, mod_type, samples=None):
    pos = 0
    if mod_type == "random":
        for vec in grammar_module.keys():
            random_mod = random.choice(['swap','reverse','plus','minus'])
            if random_mod == "plus" or random_mod == "minus":
                pos = random.choice(list(range(0,len(grammar_module[vec]))))
            prob_vec = list(exp_probabilities(grammar_module[vec]).values())
            if len(prob_vec) <=1 :
                continue
            prob_vec = mutate_vector_gen(prob_vec, random_mod, pos)
            for term in range(0,len(prob_vec)):
                set_prob(grammar_module, vec, grammar_module[vec][term],prob_vec[term])
        return grammar_module
    elif mod_type == "mined" and samples:
        return mined_prob_gen(samples, grammar_module)

if __name__=="__main__":
    # from json_grammar import JSON_GRAMMAR
    # assert is_valid_grammar(JSON_GRAMMAR, supported_opts={'prob'})
    # for i in JSON_GRAMMAR.keys():
        # vec_len = len(JSON_GRAMMAR[i])
        # prob_vec = verify_prob(vec_len)
        # for prob in prob_vec:


    # f = GrammarFuzzer(JSON_GRAMMAR)
    # a = f.fuzz()
    # print(a)
    # for i in JSON_GRAMMAR.keys():
    #     prob_vec = prob_gen(len(JSON_GRAMMAR[i]))
    #     # print(JSON_GRAMMAR[i], prob_vec)
    #     for term in range(0,len(prob_vec)):
    #         set_prob(JSON_GRAMMAR, i, JSON_GRAMMAR[i][term],prob_vec[term])
    # print(JSON_GRAMMAR)
    # g = ProbabilisticGrammarFuzzer(JSON_GRAMMAR)
    # b = g.fuzz()
    # print(b)
    import json

    example1 = open("json_examples/example1.json")
    example2 = open("json_examples/example2.json")
    example3 = open("json_examples/example3.json")
    example4 = open("json_examples/example4.json")
    example5 = open("json_examples/example5.json")

    samples = [json.dumps(json.load(example1))]#, json.load(example2), json.load(example3), json.load(example4), json.load(example5)]

    example1.close()
    example2.close()
    example3.close()
    example4.close()
    example5.close()
    # tokens = set(JSON_GRAMMAR.keys())
    mined_prob_grammar = copy.deepcopy(JSON_GRAMMAR)
    # print(EXPR_GRAMMAR)
    # print(JSON_GRAMMAR)
    samples = [' { } ']
    mined_prob_grammar = random_vector_gen(mined_prob_grammar, "sample", samples)
    print(mined_prob_grammar)



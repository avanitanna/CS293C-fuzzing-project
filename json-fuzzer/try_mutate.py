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


mutant_srcs = []
mutant_pm_srcs = []

# directly generate mutant without the need to break json_parser into separate functions
for mutant in mutant_creator.MuFunctionAnalyzer(json_parser): 
    mutant_srcs.append(mutant.src())
    mutant_pm_srcs.append(len(mutant.pm.src.split('\n')))

for i,m in enumerate(mutant_srcs): 
    mutated_prog = m
    mutated_file = open('json_parser_mutated_try.py','w')
    mutated_file.write(mutated_prog)
    mutated_file.close()
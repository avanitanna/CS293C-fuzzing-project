import sys
sys.path.append("../")

import mutant_creator
import mutant_grammar_gen
import html_grammar
# from fuzzingbook import Grammars
from fuzzingbook.Grammars import *

from fuzzingbook import GrammarFuzzer
from fuzzingbook.GrammarFuzzer import GrammarFuzzer
from fuzzingbook.Parser import EarleyParser, Parser

XML_GRAMMAR = html_grammar.HTML_GRAMMAR

baseline_fuzz = GrammarFuzzer(XML_GRAMMAR, max_nonterminals=7)
samples = []

for i in range(10):
    sample = baseline_fuzz.fuzz()
    if sample not in samples:
        samples.append(baseline_fuzz.fuzz())

print(samples)
import html5lib
parser = html5lib.HTMLParser(strict=True)
for i in samples:
    print(i)
    parser.parse(i)

from fuzzingbook.GrammarFuzzer import GrammarFuzzer
from fuzzingbook.ProbabilisticGrammarFuzzer import *
# print(mutant_grammar_gen.mined_prob_gen(samples, XML_GRAMMAR))
probabilistic_grammar_miner = ProbabilisticGrammarMiner(EarleyParser(XML_GRAMMAR)) #tokens=XML_TOKENS))
print("fin parsing")
probabilistic_cgi_grammar = probabilistic_grammar_miner.mine_probabilistic_grammar(samples)
print("fin mining")
print(probabilistic_cgi_grammar)
# a='<!DOCTYPE html><meta charset="utf-8"><title>CSS Backgrounds and Borders Reference</title><link rel="author" title="Intel" href="http://www.intel.com"><body></body>'
# for a in samples:
#     parser = EarleyParser(XML_GRAMMAR)
#     print(parser.parse(a))
        # print(tree)
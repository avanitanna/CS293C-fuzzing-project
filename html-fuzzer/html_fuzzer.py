import sys
sys.path.append("../")

import mutant_creator
from fuzzingbook import Grammars
from fuzzingbook.Grammars import *

from fuzzingbook import GrammarFuzzer
from fuzzingbook.GrammarFuzzer import GrammarFuzzer
from fuzzingbook.Parser import EarleyParser, Parser

XML_TOKENS: Set[str] = {"<id>", "<text>"}

XML_GRAMMAR: Grammar = {
    "<start>": ["<!DOCTYPE html><xml-tree>"],
    "<xml-tree>": ["<text>",
                   "<xml-open-tag><xml-tree><xml-close-tag>",
                   "<xml-openclose-tag>",
                   "<xml-tree><xml-tree>"],
    "<xml-open-tag>":      ["<<id>>", "<<id> <xml-attribute>>"],
    "<xml-openclose-tag>": ["<<id>/>", "<<id> <xml-attribute>/>"],
    "<xml-close-tag>":     ["</<id>>"],
    "<xml-attribute>":     ["<id>=<id>", "<xml-attribute> <xml-attribute>"],
    "<id>":                ["<letter_keywords>", "<id><letter_keywords>","<keywords>"],
    "<text>":              ["<text><letter_space>", "<letter_space>", "<keywords><letter_space><text>>", "<letter>"],
    "<letter>":            srange(string.ascii_letters + string.digits +
                                  "\"" + "'" + "."),
    "<letter_space>":      srange(string.ascii_letters + string.digits +
                                  "\"" + "'" + " " + "\t"),
    "<keywords>" : ["body","script","style","div"],
    "<letter_keywords>": ["p","b","i","a","u","br"]
}

baseline_fuzz = GrammarFuzzer(XML_GRAMMAR)
samples = []

for i in range(100):
    sample = baseline_fuzz.fuzz()
    if sample not in samples:
        samples.append(baseline_fuzz.fuzz())

print(samples)
import html5lib
parser = html5lib.HTMLParser()
for i in samples:
    print(i)
    parser.parse(i)

# a='<!DOCTYPE html><meta charset="utf-8"><title>CSS Backgrounds and Borders Reference</title><link rel="author" title="Intel" href="http://www.intel.com"><body></body>'
for a in samples:
    parser = EarleyParser(XML_GRAMMAR, tokens=XML_TOKENS)
    for tree in parser.parse(a):
        print(tree)
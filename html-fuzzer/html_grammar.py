from fuzzingbook import Grammars
from fuzzingbook.Grammars import *

HTML_EBNF_GRAMMAR: Grammar = {
    "<start>": ["<json>"],

    "<json>": ["<element>"],

    "<element>": ["<ws><value><ws>"],

    "<value>": ["<object>", "<array>", "<string>", "<number>",
                "true", "false", "null", "'; DROP TABLE STUDENTS"],

    "<object>": ["{<ws>}", "{<members>}"],

    "<members>": ["<member>(,<members>)*"],

    "<member>": ["<ws><string><ws>:<element>"],

    "<array>": ["[<ws>]", "[<elements>]"],

    "<elements>": ["<element>(,<elements>)*"],

    "<element>": ["<ws><value><ws>"],

    "<string>": ['"' + "<characters>" + '"'],
    
    "<characters>": ["<character>*"],

    "<character>": srange(CHARACTERS_WITHOUT_QUOTE),

    "<number>": ["<int><frac><exp>"],

    "<int>": ["<digit>", "<onenine><digits>", "-<digits>", "-<onenine><digits>"],

    "<digits>": ["<digit>+"],

    "<digit>": ['0', "<onenine>"],

    "<onenine>": crange('1', '9'),

    "<frac>": ["", ".<digits>"],

    "<exp>": ["", "E<sign><digits>", "e<sign><digits>"],

    "<sign>": ["", '+', '-'],

    # "<ws>": srange(string.whitespace)

    "<ws>": [" "]
}

assert is_valid_grammar(JSON_EBNF_GRAMMAR)

HTML_GRAMMAR = convert_ebnf_grammar(HTML_EBNF_GRAMMAR)
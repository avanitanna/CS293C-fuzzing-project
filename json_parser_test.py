import json_parser_mutated
import sys
import pprint

#i = sys.argv[1] 
f = open("json_inp.json")
content = f.read()
#print(i)
res = json_parser_mutated.value_parser(content.strip())
try:
    pprint.pprint(res[0])
except TypeError:
    print("Error!")

#print(res[0])
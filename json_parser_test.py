import json_parser_mutated
import json_parser
import sys
import pprint

#i = sys.argv[1] 
f = open("json_inp.json")
content = f.read()
#print(i)
res_mutated = json_parser_mutated.value_parser(content.strip())
res = json_parser.value_parser(content.strip())
try:
    assert res[0] == res_mutated[0]
    pprint.pprint(res_mutated[0])
       
except Exception as e:
   raise Exception("Error!")

#print(res[0])
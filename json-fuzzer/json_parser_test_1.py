# import json_parser_mutated_1
import json_parser
import sys
sys.path.append("../")

f = open("json_inp_1.json")
content = f.read()
try:
    import json_parser_mutated_1
    res_mutated = json_parser_mutated_1.value_parser(content.strip())
    res = json_parser.value_parser(content.strip())
    assert res[0] == res_mutated[0]
    print(res_mutated[0])
except Exception as e:
    raise Exception("Error!")

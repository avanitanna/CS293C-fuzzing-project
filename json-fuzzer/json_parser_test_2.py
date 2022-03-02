import json_parser_mutated_2
import json_parser
import sys
sys.path.append("../")

from fuzzingbook.Coverage import Coverage

def test_function(content):
    with Coverage() as cov_fuzz:
        try:
            res_mutated = json_parser_mutated_2.value_parser(content.strip())
        except:
            pass
    cov = len(cov_fuzz.coverage())
    print(res_mutated[0]+":-"+str(cov))

if __name__=="__main__":
    f = open("json_inp_2.json")
    content = f.read()
    try:
        test_function(content)
    except Exception as e:
        print("input invalid!")
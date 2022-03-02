import json_parser_mutated_1
import json_parser
import sys
sys.path.append("../")

from fuzzingbook.Coverage import Coverage

def test_function(content):
    with Coverage() as cov_fuzz:
        try:
            res_mutated = json_parser_mutated_1.value_parser(content.strip())
        except:
            pass
    cov = len(cov_fuzz.coverage())
    print(res_mutated[0]+":-"+str(cov))

if __name__=="__main__":
    f = open("json_inp_1.json")
    content = f.read()
    try:
        test_function(content)
    except Exception as e:
        print("input invalid!")
# import json_parser_mutated_1
# import json_parser
# import sys
# sys.path.append("../")

# from fuzzingbook.Coverage import Coverage
# #i = sys.argv[1] 
# f = open("json_inp_1.json")
# content = f.read()
# #print(i)
# with Coverage() as cov_fuzz:
#     try:
#         res_mutated = json_parser_mutated_1.value_parser(content.strip())
#     except:
#         pass
# cov = 1
# if cov_fuzz.coverage():
#     cov = len(cov_fuzz.coverage())

# res = json_parser.value_parser(content.strip())
# try:
#     assert res[0] == res_mutated[0]
       
# except Exception as e:
#    raise Exception("Error!")
# print(res_mutated[0]+":-"+str(cov))
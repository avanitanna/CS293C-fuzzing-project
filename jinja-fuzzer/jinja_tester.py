import random
import sys
sys.path.append("../")
from fuzzingbook.Coverage import Coverage

f=open("template_file")
temp=f.read()
rand_int = random.randint(0,50)
try:
    import jinja2
    with Coverage() as cov_fuzz:
        try:
            op = jinja2.Template(temp).render(values=list(range(rand_int)))  
        except:
            pass
    cov = cov_fuzz.coverage()
    cov_len = len(cov)
    print(op+":-"+str(cov_len))
except Exception as e:
    print("killed")
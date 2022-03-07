import html5lib
import sys
sys.path.append("../")

from fuzzingbook.Coverage import Coverage
# def testing_coverage(sample):
#     parser = html5lib.HTMLParser(strict=True)
#     element = parser.parse(sample)
#     return element

def test_function(sample, ind):
    element = None
    with Coverage() as cov_fuzz:
        try:
            parser = html5lib.HTMLParser()
            element = parser.parse(sample)
        except:
            pass
    cov = cov_fuzz.coverage()
    walker = html5lib.getTreeWalker("etree")
    stream = walker(element)
    s = html5lib.serializer.HTMLSerializer()
    output = s.serialize(stream)
    ex_str=''
    for i in output:
        ex_str+=i
    if i == 1:
        print(ex_str+":-"+str(len(cov)))

if __name__=="__main__":
    sample = sys.argv[1]
    for i in range(2):
        try:
            test_function(sample, i)
        except Exception as e:
            print("input invalid!")
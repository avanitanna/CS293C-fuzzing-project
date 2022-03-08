#fuzzer implementation
#inspired by work from fuzzingbook

import ast
import inspect
import difflib
class Mutant:
    def __init__(self, pm, location, strategy, log=False):
        self.pm = pm
        self.i = location
        self.strategy = strategy
        self.name = "%s_%s" % (self.pm.name, self.i)
        self._src = None
        self.tests = []
        self.detected = False
        self.log = log
  
    def __enter__(self):
        # pass
        if self.log:
            print('->\t%s' % self.name)
        c = compile(self.src(), '<mutant>', 'exec')
        eval(c, globals())

    def generate_mutant(self, location):
        mutant_ast = self.pm.mutator_object(
            location,strategy=self.strategy).visit(ast.parse(self.pm.src))  # copy
        return ast.unparse(mutant_ast)

    def src(self):
        if self._src is None:
            self._src = self.generate_mutant(self.i)
        return self._src
    
    def diff(self):
        return '\n'.join(difflib.unified_diff(self.pm.src.split('\n'),
                                              self.src().split('\n'),
                                              fromfile='original',
                                              tofile='mutant',
                                              n=3))

    def __exit__(self, exc_type, exc_value, traceback):
        pass

class PMIterator:
    def __init__(self, pm):
        self.pm = pm
        self.idx = 0
  
    def __next__(self):
        i = self.idx
        if i >= self.pm.nmutations:
            self.pm.finish()
            raise StopIteration()
        self.idx += 1
        mutant = Mutant(self.pm, self.idx, strategy=self.pm.strategy, log=self.pm.log)
        self.pm.register(mutant)
        return mutant

class MuFunctionAnalyzer:
    def __init__(self, fn, strategy = None, log=False):
        self.fn = fn
        self.name = fn.__name__
        src = inspect.getsource(fn)
        self.ast = ast.parse(src)
        self.src = ast.unparse(self.ast)  # normalize
        self.strategy = strategy
        self.mutator = self.mutator_object(strategy=strategy)
        # print(self.mutator)
        self.nmutations = self.get_mutation_count()
        # print(self.nmutations)
        self.un_detected = set()
        self.mutants = []
        self.log = log

    def mutator_object(self, locations=None, strategy=None):
        if strategy == "condition":
            return ConditionMutator(locations)
        elif strategy == "ds":
            return DSMutator(locations)
        elif strategy == "return":
            return StmtReturnMutator(locations)
        else:
            return StmtDeletionMutator(locations)

    def register(self, m):
        self.mutants.append(m)

    def get_mutation_count(self):
        self.mutator.visit(self.ast)
        return self.mutator.count

    def __iter__(self):
        return PMIterator(self)

    def finish(self):
        self.un_detected = {mutant for mutant in self.mutants if not mutant.detected}

    def score(self):
        return (self.nmutations - len(self.un_detected)) / self.nmutations

class Mutator(ast.NodeTransformer):
    def __init__(self, mutate_location=-1):
        self.count = 0
        self.mutate_location = mutate_location

    def mutable_visit(self, node, flag=None):
        self.count += 1  # statements start at line no 1
        if self.count == self.mutate_location:
            return self.mutation_visit(node, flag)
        return self.generic_visit(node)


class StmtReturnMutator(Mutator):
    def visit_Return(self, node): return self.mutable_visit(node)
    def visit_Pass(self, node): return self.mutable_visit(node)
    def visit_Break(self, node): return self.mutable_visit(node)
    def visit_Continue(self, node): return self.mutable_visit(node)

    def mutation_visit(self, node, flag=None): 
        obj=None
        obj = ast.Return(None)
        return obj

class StmtDeletionMutator(Mutator):
    def visit_Return(self, node): return self.mutable_visit(node)
    def visit_Delete(self, node): return self.mutable_visit(node)

    def visit_Assign(self, node): return self.mutable_visit(node) #r=0
    def visit_AnnAssign(self, node): return self.mutable_visit(node) #??
    def visit_AugAssign(self, node): return self.mutable_visit(node) #r+=1

    def visit_Raise(self, node): return self.mutable_visit(node)
    def visit_Assert(self, node): return self.mutable_visit(node)

    def visit_Global(self, node): return self.mutable_visit(node)
    def visit_Nonlocal(self, node): return self.mutable_visit(node)

    def visit_Expr(self, node): return self.mutable_visit(node) #a+b
    # def visit_If(self, node):
    #     if (type(node.test) == type(ast.Name()) or type(node.test) == type(ast.Compare()) 
    #     or type(node.test) == type(ast.UnaryOp())):
    #         # obj = ast.parse("not "+node.test.id)
    #         return self.mutable_visit(node, flag="add") #changes if a to if not a, and if expr to if not expr

    #     print(type(node.test) == type(ast.Name()))
    #     # node.test.ops = [ast.Invert()]
    #     # print(node.test.ops[0])
    #     return self.mutable_visit(node)

    def visit_Pass(self, node): return self.mutable_visit(node)
    def visit_Break(self, node): return self.mutable_visit(node)
    def visit_Continue(self, node): return self.mutable_visit(node)

    def mutation_visit(self, node, flag=None): 
        obj=None
        obj = ast.Pass()
        # print("using wrong variation")
        #print(type(node.test) == type(ast.Name()))
        # node.test.ops = [ast.Invert()]
        # print(node.test.ops[0])
        return obj #return ast.Pass() 

class ConditionMutator(Mutator):

    def visit_If(self, node):
        if (type(node.test) == type(ast.Name()) or type(node.test) == type(ast.Compare()) 
        or type(node.test) == type(ast.UnaryOp())):
            # obj = ast.parse("not "+node.test.id)
            return self.mutable_visit(node, flag="add") #changes if a to if not a, and if expr to if not expr

        # print(type(node.test) == type(ast.Name()))
        # node.test.ops = [ast.Invert()]
        # print(node.test.ops[0])
        return self.mutable_visit(node)

    def mutation_visit(self, node, flag=None): 
        obj=None
        if flag == "add":
            # print(ast.dump(node))
            node.test = ast.UnaryOp(op=ast.Not(), operand=node.test)# ast.parse("not "+node.test.id)
            obj = node
            # print("using right variation")
            # print(ast.dump(node))
            # print(ast.unparse(node))
        else:
            obj = ast.Return(None)
        #print(type(node.test) == type(ast.Name()))
        # node.test.ops = [ast.Invert()]
        # print(node.test.ops[0])
        return obj #return ast.Pass() 

class DSMutator(Mutator):

    def visit_Assign(self, node):
        # print(ast.dump(node))
        if type(node.value) == type(ast.List()):
            # print(node.value.elts)
            return self.mutable_visit(node,flag="reverse")
        elif type(node.value) == type(ast.Dict()):
            return self.mutable_visit(node, flag="mod")


        # return self.mutable_visit(node,flag=None)
    
    # def visit_Dict(self, node):
    #     # print(ast.dump(node))
    #     return self.mutable_visit(node,flag="convert")

    def mutation_visit(self, node, flag=None): 
        obj=None
        if flag == "reverse":
            # print(ast.dump(node))
            node.value.elts.reverse()
            obj = node
            # print(obj.value.elts)
            # print("using right variation")
            # print(ast.dump(node))
            # print(ast.unparse(node))
        elif flag == "mod":
            node.value.keys.reverse()
            obj=node
        else:
            obj = ast.Return(None)
        #print(type(node.test) == type(ast.Name()))
        # node.test.ops = [ast.Invert()]
        # print(node.test.ops[0])
        return obj #return ast.Pass()

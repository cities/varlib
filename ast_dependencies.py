dep_graph = {}
defs = {}

import yaml
import ast
import pandas as pd
from pprint import pprint

with open(r'variables.yml') as file:
    # The FullLoader parameter handles the conversion from YAML
    # scalar values to Python the dictionary format
    variables = yaml.load(file, Loader=yaml.FullLoader)

    #print(variables)

ops = [
    'aggregate',
    'disaggregate',
]    



class Analyzer(ast.NodeVisitor):
    def __init__(self):
        self.deps = []
        self.crosswalk = {"deps":[]}
        self.funcs = []

    def visit_Assign(self, node):
        lhs, = node.targets
        rhs = node.value
        self.generic_visit(rhs)

    def visit_Attribute(self, node):
        dataset = node.value.id
        if node.attr == "aggregate":
            #self.deps += [f"{node.value.id}.{node.value.id}_id"]
            self.crosswalk["tgt_id"] = f"{dataset}_id"
        elif node.attr == "disaggregate":
            #self.deps += [f"{node.value.id}.{node.value.id}_id"]
            self.crosswalk["src_ds"] = f"{dataset}"
        else:
            self.deps += [f"{dataset}.{node.attr}"]
            if "tgt_id" in self.crosswalk:
                self.crosswalk["deps"] += [f"{dataset}.{self.crosswalk['tgt_id']}"]
            elif "src_ds" in self.crosswalk:
                self.crosswalk["deps"] += [f"{self.crosswalk['src_ds']}.{dataset}_id"]
                
    def visit_Call(self, node):
        #if type(node.func) is ast.Name:
        #    self.generic_visit(node.args)
        #if type(node.func) is ast.Attribute:
        #    self.deps += [f"{node.func.value.id}.{node.func.value.id}_id"]
        self.funcs += [node.func]
        [self.visit(arg) for arg in node.args]
        [self.visit(kwarg) for kwarg in node.keywords]
    
    def visit_Name(self, node):
        if hasattr(node, "attr"):
            self.deps += [f"{node.id}.{node.attr}"]
        else:
            self.deps += [node.id]
    
    def report(self):
        pprint(self.deps)

   
# how can I know a ast.Name is a DataFrame column?
for df_name, var_exprs in variables.items():
    for expr in var_exprs:
        #print(expr)
        module = ast.parse(expr)
        stmt = module.body[0]
        lhs, = stmt.targets
        rhs = stmt.value
        analyzer = Analyzer()
        analyzer.visit(stmt)
        #analyzer.report()
        dep_graph[f"{df_name}.{lhs.id}"] = [f"{dep}" if "." in dep 
                                              else f"{df_name}.{dep}" 
                                            for dep in analyzer.deps + 
                                               analyzer.crosswalk.get("deps")
                                           ]
        defs[f"{df_name}.{lhs.id}"] = expr #rhs

        
# tests
def compare_dict(dict1, dict2):
    for x1 in dict1.keys():
        z = dict1.get(x1) == dict2.get(x1)
        if not z:
            print('key', x1)
            print('Actual', dict1.get(x1), '\nExpected', dict2.get(x1))
            print('-----\n')
            
expected_graph = {'household.nadults': ['household.hhsize', 'household.nchildren'],
 'household.cars_per_adults': ['household.cars', 'household.nadults'],
 'household.cars_per_adults_gt1': ['household.cars_per_adults'],
 'household.sqrt_hhsize': ['household.hhsize'],
 'household.nchildren': ['person.is_child', 'person.household_id'],
 'person.is_child': ['person.age'],
 'person.nadults': ['household.nadults', 'person.household_id'],
 'person.is_girl': ['person.is_child', 'person.sex']
                 }

compare_dict(dep_graph, expected_graph)

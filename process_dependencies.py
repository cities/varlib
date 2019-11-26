dep_graph = {}

import yaml
import pandas as pd

with open(r'variables.yml') as file:
    # The FullLoader parameter handles the conversion from YAML
    # scalar values to Python the dictionary format
    variables = yaml.load(file, Loader=yaml.FullLoader)

    #print(variables)

ops = [
    'aggregate',
    'disaggregate',
]    
    
# how can I know a ast.Name is a DataFrame column?
import ast
for df_name, var_exprs in variables.items():
    for expr in var_exprs:
        module = ast.parse(expr)
        stmt = module.body[0]
        if not isinstance(stmt, ast.Assign):
            # need to assign auto-generated name?
            continue
        lhs, = stmt.targets
        rhs = stmt.value
        #print(lhs, rhs)
        rhs_names = set([node.id for node in ast.walk(rhs)
                         if type(node) is ast.Name])
        #remove function calls (may want to keep tracking them)
        func_names = set([node.func.id for node in ast.walk(rhs)
                         if type(node) is ast.Call and 
                              type(node.func) is ast.Name])
        #handle pd DataFrame methods
        method_names = set([node.func.attr for node in ast.walk(rhs)
                            if type(node) is ast.Call and 
                              type(node.func) is ast.Attribute])
        if type(rhs) is ast.Call and type(rhs.func) is ast.Attribute:
            var_names = [f"{rhs.func.value.id}.{rhs.func.value.id}_id"]
            var_names += [f"{arg.value.id}.{arg.attr}" for arg in rhs.args]
        else:
            var_names = [name if "." in name else f"{df_name}.{name}" 
                         for name in rhs_names - func_names]
        dep_graph[f"{df_name}.{lhs.id}"] = var_names
        #print(names)


import pandas as pd
import numpy as np
from pandas.core.computation.expr import Expr
from pandas.core.computation.scope import Scope

code = "sqrt_nch = sqrt(nchildren + 1)"
env = Scope(1, local_dict={"hhsize":3, "nchildren":2}, target="c")
aa = Expr(code, env=env)

data = {'person_id': [1, 2, 3, 4],
        'household_id': [1, 1, 2, 3],
        'age':[2, 26, 19, 18]} 
# Create DataFrame 
person = pd.DataFrame(data) 

person = person.assign(is_child=lambda x: (x["age"]<18).astype(int))
#pd.eval("is_child=np.where(person.age<18, 1, 0)", target=person)
#person.eval("is_child=np.where(age<18, 1, 0)", inplace=True, np=np)

data = {'household_id': [1, 2, 3]} 
# Create DataFrame 
household = pd.DataFrame(data).set_index("household_id")

def nchildren(household, person):
    res = person.groupby("household_id").agg({"is_child":"sum"}).rename(columns={"is_child":"nchildren"})
    return household.join(res)["nchildren"].values

local_dict={"person":person_df, "np":np}
code = 'nchildren = person.groupby("household_id").agg(np.sum)'
env = Scope(1, local_dict=local_dict, target="c")
#pd.eval(code, local_dict=local_dict, target="c")
#aa = Expr(code, env=env)
        
# tests
def compare_dict(dict1, dict2):
    for x1 in dict1.keys():
        z = dict1.get(x1) == dict2.get(x1)
        if not z:
            print('key', x1)
            print('Actual', dict1.get(x1), '\nExpected', dict2.get(x1))
            print('-----\n')
            
expected_graph = {'household.nadults': ['household.hhsize', 'household.nchildren'],
 'household.cars_per_adults': ['household.nadults', 'household.cars'],
 'household.cars_per_adults_gt1': ['household.cars_per_adults'],
 'household.sqrt_hhsize': ['household.hhsize'],
 'household.nchildren': ['household.household_id', 'person.is_child'],
 'person.is_child': ['person.age']
                 }

compare_dict(dep_graph, expected_graph)

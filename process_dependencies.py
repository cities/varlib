dep_graph = {}

import yaml

with open(r'variables.yml') as file:
    # The FullLoader parameter handles the conversion from YAML
    # scalar values to Python the dictionary format
    variables = yaml.load(file, Loader=yaml.FullLoader)

    #print(variables)

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
                     if type(node) is ast.Call and type(node.func) is ast.Name])
        #handle pd DataFrame methods
        
        rhs_names = [name if "." in name else f"{df_name}.{name}" 
                     for name in rhs_names - func_names]    
        dep_graph[f"{df_name}.{lhs.id}"] = rhs_names
        #print(names)


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
 'household.nchildren': ['person.household_id', 'person.is_child'],
 'person.is_child': ['person.age']
                 }

compare_dict(dep_graph, expected_graph)

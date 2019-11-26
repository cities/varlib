      
import pandas as pd
import numpy as np
from pandas.core.computation.expr import Expr
from pandas.core.computation.scope import Scope

code = "sqrt_nch = sqrt(nchildren + 1)"
#env = Scope(1, local_dict={"hhsize":3, "nchildren":2}, target="c")
#aa = Expr(code, env=env)

pp_data = {'person_id': [1, 2, 3, 4],
           'household_id': [1, 1, 2, 2],
           'age':[2,   26,  39, 10],
           'sex':['F', 'F', 'M', 'M']}
# Create DataFrame 
person = pd.DataFrame(pp_data)
household = pd.DataFrame(hh_data).set_index("person_id")
person.name = "person"

#person = person.assign(is_child=lambda x: (x["age"]<18).astype(int))
#pd.eval("is_child=np.where(person.age<18, 1, 0)", target=person)
#person.eval("is_child=np.where(age<18, 1, 0)", inplace=True, np=np)


hh_data = {'household_id': [1, 2, 3]} 
# Create DataFrame 
household = pd.DataFrame(hh_data).set_index("household_id")
household.name = "household"

from ast_dependencies import *
import networkx as nx
import itertools

G = nx.DiGraph()
for k, v in dep_graph.items():
    G.add_node(k)
    G.add_nodes_from(v)
    edges = itertools.zip_longest(v, [k], fillvalue=k)
    G.add_edges_from(edges)
    
def compute(full_vname):
    assert G.has_node(full_vname)
    df_name, vname= full_vname.split(".")
    df = globals()[df_name]
    for dep_full_vname in G.predecessors(full_vname):
        dep_df_name, dep_vname = dep_full_vname.split(".")
        if dep_vname not in globals()[dep_df_name].columns:
            compute(dep_full_vname)
    var_def = defs[full_vname]
    #var_def = f"{vname} = {var_def}"
    df.eval(var_def, inplace=True)

#compute("person.is_child")
compute("person.is_girl")
assert 'is_child' in person.columns
assert 'is_girl' in person.columns

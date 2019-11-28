import yaml
import ast
import itertools
import networkx as nx
import pandas as pd
from pprint import pprint

_methods = [
    'astype'
]

class DepAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.deps = []
        self.crosswalk = {"deps":[]}
        self.funcs = []
        self.is_method = None

    def visit_Assign(self, node):
        lhs, = node.targets
        rhs = node.value
        self.visit(rhs)

    def visit_Attribute(self, node):
        print(ast.dump(node))
        dataset = None
        #import ipdb; ipdb.set_trace()
        #maybe a dataset name
        if type(node.value) is ast.Name:
            # node is an attribute, not a method
            if node.attr not in _methods:
                dataset = node.value.id
            else:
                self.deps +=[node.value.id]
        else:
            self.visit(node.value)
        if node.attr == "aggregate":
            #self.deps += [f"{node.value.id}.{node.value.id}_id"]
            self.crosswalk["tgt_ds"] = f"{dataset}"
        elif node.attr == "disaggregate":
            #self.deps += [f"{node.value.id}.{node.value.id}_id"]
            self.crosswalk["src_ds"] = f"{dataset}"
        elif dataset is not None:
            self.deps += [f"{dataset}.{node.attr}"]
            if "tgt_ds" in self.crosswalk:
                self.crosswalk["deps"] += [f"{dataset}.{self.crosswalk['tgt_ds']}_id"]
            elif "src_ds" in self.crosswalk:
                self.crosswalk["deps"] += [f"{self.crosswalk['src_ds']}.{dataset}_id"]

    def visit_Call(self, node):
        #print(ast.dump(node))
        #if type(node.func) is ast.Name:
        #    self.generic_visit(node.args)
        if type(node.func) is ast.Attribute:
            self.is_method = True
        #    self.deps += [f"{node.func.value.id}.{node.func.value.id}_id"]
        if type(node.func) is ast.Attribute:
            self.visit(node.func)
        else:
            self.funcs += [node.func]
        [self.visit(arg) for arg in node.args]
        [self.visit(kwarg) for kwarg in node.keywords]

    def visit_Name(self, node):
        print(ast.dump(node))
        if hasattr(node, "attr"):
            self.deps += [f"{node.id}.{node.attr}"]
        else:
            self.deps += [node.id]

    def report(self):
        pprint(self.deps)

def build_graph(vardef_yml, verbose=False):
    dep_dict = {}
    #def_dict = {}

    with open(vardef_yml) as file:
        # The FullLoader parameter handles the conversion from YAML
        # scalar values to Python the dictionary format
        variables = yaml.load(file, Loader=yaml.FullLoader)

        #print(variables)

    # how can I know a ast.Name is a DataFrame column?
    for df_name, var_exprs in variables.items():
        for expr in var_exprs:
            #print(expr)
            module = ast.parse(expr)
            stmt = module.body[0]
            lhs, = stmt.targets
            rhs = stmt.value
            analyzer = DepAnalyzer()
            analyzer.visit(stmt)
            #analyzer.report()
            dep_dict[f"{df_name}.{lhs.id}"] = [[f"{dep}" if "." in dep
                                                  else f"{df_name}.{dep}"
                                                for dep in analyzer.deps +
                                                  analyzer.crosswalk.get("deps")
                                                ],
                                               expr, # original var definition
                                               None] # hash placeholder
            #def_dict[f"{df_name}.{lhs.id}"] = expr #rhs

    dep_graph = nx.DiGraph()
    for k, v in dep_dict.items():
        k_dep, k_expr, k_hash = v
        if not dep_graph.has_node(k):
            dep_graph.add_node(k, expr=k_expr, hash=k_hash)
        else:
            dep_graph.nodes[k]['expr'] = k_expr
            dep_graph.nodes[k]['hash'] = k_hash
        dep_graph.add_nodes_from(k_dep)
        edges = itertools.zip_longest(k_dep, [k], fillvalue=k)
        dep_graph.add_edges_from(edges)

    if verbose:
        pprint(dep_dict)

    #return def_dict, dep_dict, dep_graph
    return dep_graph

def compute(full_vname, dep_graph, resolvers, recompute=False):
    assert dep_graph.has_node(full_vname)
    df_name, vname= full_vname.split(".")
    df = resolvers[df_name]
    for dep_full_vname in dep_graph.predecessors(full_vname):
        dep_df_name, dep_vname = dep_full_vname.split(".")
        if dep_vname not in resolvers[dep_df_name].columns:
            compute(dep_full_vname, dep_graph, resolvers)
    var_def = dep_graph.nodes[full_vname]['expr']
    #var_def = f"{vname} = {var_def}"
    df.eval(var_def, inplace=True)


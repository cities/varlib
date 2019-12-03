import yaml
import ast
import itertools
import networkx as nx
import pandas as pd
from pprint import pprint
import xxhash
import astor

class ExprTransformer(ast.NodeTransformer):
    def __init__(self):
        self.is_method = {}
        self.exprs = []
        self.hash_gen = xxhash.xxh64()

    def transform_stmt(self, stmt):
        stmt_txfm = self.visit(stmt)
        stmt_retn = self.exprs + [astor.to_source(stmt_txfm)]
        return stmt_retn

    def visit_Call(self, node):
        if type(node.func) is ast.Attribute:
            self.is_method = {node.func: True}
        return self.generic_visit(node)
        #[self.visit(arg) for arg in node.args]
        #[self.visit(kwarg) for kwarg in node.keywords]
        #return node

    def visit_Attribute(self, node):
        #print(ast.dump(node))
        if type(node.value) is not ast.Name and self.is_method.get(node, False):
            print(astor.dump_tree(node))
            node_expr = astor.to_source(node.value)
            self.hash_gen.update(node_expr)
            expr_hash = f'_var{self.hash_gen.hexdigest()}'
            self.hash_gen.reset()
            self.exprs += [f'{expr_hash}={node_expr}']
            attr_name = ast.Name(id=f'{expr_hash}', ctx=ast.Load())
            newnode = ast.Attribute(value=attr_name, attr=node.attr)
            ast.copy_location(newnode, node)
            ast.fix_missing_locations(newnode)
            print(astor.dump_tree(newnode))
            return newnode
        return node

class DepAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.deps = []
        self.funcs = []
        self.crosswalk = {}
        self.is_method = {}
        self.is_func = {}

    def visit_Assign(self, node):
        lhs, = node.targets
        rhs = node.value
        print(ast.dump(rhs))
        #print(astor.dump_tree(rhs))
        self.visit(rhs)

    def visit_Attribute(self, node):
        #print(ast.dump(node))
        dataset = None
        #maybe a dataset name
        if type(node.value) is ast.Name:
            # node is an attribute
            if not self.is_method.get(node, False):
            #if node.attr not in _methods:
                dataset = node.value.id
                self.deps += [f"{dataset}.{node.attr}"]
            elif node.attr not in ['aggregate', 'disaggregate']:
                # aggregate and disaggregate is method, but
                # no need to add dependency here
                self.deps +=[node.value.id]
        else:
            self.visit(node.value)
        if node.attr == "aggregate":
            dataset = node.value.id
            #self.deps += [f"{node.value.id}.{node.value.id}_id"]
            self.crosswalk["tgt_ds"] = f"{dataset}"
        elif node.attr == "disaggregate":
            dataset = node.value.id
            #self.deps += [f"{node.value.id}.{node.value.id}_id"]
            self.crosswalk["src_ds"] = f"{dataset}"
        elif self.crosswalk:
            if "tgt_ds" in self.crosswalk:
                self.deps += [f"{dataset}.{self.crosswalk['tgt_ds']}_id"]
            elif "src_ds" in self.crosswalk:
                self.deps += [f"{self.crosswalk['src_ds']}.{dataset}_id"]


    def visit_Call(self, node):
        #print(ast.dump(node))
        #if type(node.func) is ast.Name:
        #    self.generic_visit(node.args)
        #if type(node.func) is ast.Attribute:
        #    self.deps += [f"{node.func.value.id}.{node.func.value.id}_id"]
        if type(node.func) is ast.Attribute:
            self.is_method[node.func] = True
            #self.visit(node.func)
        else:
            self.is_func[node.func] = True
        self.generic_visit(node)
        #[self.visit(arg) for arg in node.args + node.keywords]
        #[self.visit(kwarg) for kwarg in node.keywords]

    def visit_Name(self, node):
        #print(ast.dump(node))
        if hasattr(node, "attr"):
            self.deps += [f"{node.id}.{node.attr}"]
        elif not self.is_func.get(node, False):
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
            transformer = ExprTransformer()
            stmts = transformer.transform_stmt(stmt)
            deps = [f"{dep}" if "." in dep else f"{df_name}.{dep}"
                                for dep in analyzer.deps]
            dep_dict[f"{df_name}.{lhs.id}"] = [deps,
                                               stmts, # original var definition
                                               None]  # hash placeholder
            #def_dict[f"{df_name}.{lhs.id}"] = expr #rhs

    dep_graph = nx.DiGraph()
    for k, v in dep_dict.items():
        k_dep, k_expr, k_hash = v
        if not dep_graph.has_node(k):
            dep_graph.add_node(k, exprs=k_expr, hash=k_hash)
        else:
            dep_graph.nodes[k]['exprs'] = k_expr
            dep_graph.nodes[k]['hash'] = k_hash
        dep_graph.add_nodes_from(k_dep)
        edges = itertools.zip_longest(k_dep, [k], fillvalue=k)
        dep_graph.add_edges_from(edges)

    if verbose:
        pprint(dep_dict)

    #return def_dict, dep_dict, dep_graph
    return dep_graph



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

    def visit_Arg(self, node):
        print(astor.dump_tree(node))
        return node

class ExprQualifier(ast.NodeTransformer):
    def __init__(self, dataset_name=None):
        self.dataset_name = dataset_name
        self.is_qualified_name = {}
        self.is_method = {}
        self.is_func = {}
        self.deps = []
        self.crosswalk = {}

    def transform_stmt(self, stmt, verbose=False):
        if verbose:
            print('=> Before transforming ---')
            print(astor.to_source(stmt))
        stmt_txfm = self.visit(stmt)
        stmt_retn = astor.to_source(stmt_txfm)
        if verbose:
            print('=> After transforming ---')
            print(stmt_retn)
        return stmt_retn

    def visit_Call(self, node):
        if type(node.func) is ast.Attribute:
            self.is_method[node.func] = True
            self.is_method[node.func.value] = True
        else:
            self.is_func[node.func] = True

        func_name = node.func.id if type(node.func) is ast.Name else \
            node.func.attr
        if func_name in ['aggregate', 'disaggregate']:
            tgt_ds = self.dataset_name
            self.crosswalk['target_ds'] = tgt_ds
            self.crosswalk["func"] = func_name
            #self.deps += [f'{self.dataset_name}.{node.id}']
            self.generic_visit(node)

            src_ds = self.crosswalk['source_ds']
            # insert target_ds = 'dataset_name' into list of arguments
            #keyword_val = ast.Constant(value=self.dataset_name, kind=None)
            kw_tgt_ds_val = ast.Constant(value=tgt_ds, kind=None)
            kw_tgt_ds = ast.keyword(arg='target_ds', value=kw_tgt_ds_val)
            kw_src_ds_val = ast.Constant(value=src_ds, kind=None)
            kw_src_ds = ast.keyword(arg='source_ds', value=kw_src_ds_val)
            #simpleeval doesn't provide access to resolvers
            kw_resolvers_val = ast.Name(id='resolvers')
            kw_resolvers = ast.keyword(arg='resolvers', value=kw_resolvers_val)
            keywords = node.keywords + [kw_tgt_ds, kw_src_ds, kw_resolvers]
            newnode = ast.Call(node.func, args=node.args, keywords=keywords)
            #dataset_name = ast.Name(id=f'{self.dataset_name}', ctx=node.ctx)
            #newnode = ast.Attribute(value=dataset_name, attr=node.id, ctx=node.ctx)
            ast.copy_location(newnode, node)
            ast.fix_missing_locations(newnode)
            #print(astor.dump_tree(newnode))
            return newnode

        return self.generic_visit(node)

    def visit_Attribute(self, node):
        #import ipdb; ipdb.set_trace()
        #if type(node.value) is ast.Name and not self.is_method.get(node, False):
        if type(node.value) is ast.Name:
            #e.g. disaggregate(household.nadults)
            child_node = node.value
            if not self.is_method.get(node, False):
                self.deps += [f'{child_node.id}.{node.attr}']
                self.is_qualified_name[child_node] = True
                # find the source dataset and adds required id to deps
                #import ipdb; ipdb.set_trace()
                if 'target_ds' in self.crosswalk:
                    func = self.crosswalk["func"]
                    tgt_ds = self.crosswalk['target_ds']
                    src_ds = child_node.id
                    self.crosswalk['source_ds'] = src_ds
                    self.deps += [f'{src_ds}.{tgt_ds}_id'] if func == 'aggregate' else \
                        [f'{tgt_ds}.{src_ds}_id']
            elif child_node.id in ['np']:
                #- is_girl = np.logical_and(is_child, sex == 'F')
                self.is_func[node.value] = True
        elif hasattr(node.value, 'value'):
            #e.g. person.is_child.astype('int')
            grandchild_node = node.value.value
            self.is_qualified_name[grandchild_node] = True
        #elif hasattr(node.value, 'id') and node.value.id in ['np']:
        #    # module_name.func_name
        #    self.is_func[node.value] = True
        return self.generic_visit(node)

    def visit_Name(self, node):
        #print(ast.dump(node))
        #if hasattr(node, "attr"):
        if self.is_qualified_name.get(node, False): # or self.is_method.get(node, False):
            return node
        elif not self.is_func.get(node, False):
            self.deps += [f'{self.dataset_name}.{node.id}']
            dataset_name = ast.Name(id=f'{self.dataset_name}', ctx=node.ctx)
            newnode = ast.Attribute(value=dataset_name, attr=node.id, ctx=node.ctx)
            ast.copy_location(newnode, node)
            ast.fix_missing_locations(newnode)
            #print(astor.dump_tree(newnode))
            return newnode
        return node

class DepAnalyzer(ast.NodeVisitor):
    def __init__(self, dataset_name=None):
        self.dataset_name = dataset_name
        self.deps = []
        self.funcs = []
        self.crosswalk = {}
        self.is_method = {}
        self.is_func = {}

    def visit_Assign(self, node):
        lhs, = node.targets
        rhs = node.value
        #print(ast.dump(rhs))
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
            dep = node.id
            #if "." not in dep:
            #    dep = f"{self.dataset_name}.{dep}"
            self.deps += [dep]

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
            #lhs, = stmt.targets
            #rhs = stmt.value
            #analyzer = DepAnalyzer(dataset_name=df_name)
            #analyzer.visit(stmt)
            #analyzer.report()
            transformer = ExprQualifier(dataset_name=df_name)
            stmt = transformer.transform_stmt(stmt)
            deps = transformer.deps
            #deps = [f"{dep}" if "." in dep else f"{df_name}.{dep}"
            #                    for dep in analyzer.deps]
            dep_dict[f"{deps[0]}"] = [set(deps[1:]),
                                      stmt,  # fully qualified var definition
                                      None]  # hash placeholder
            #import ipdb; ipdb.set_trace()
            pass
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



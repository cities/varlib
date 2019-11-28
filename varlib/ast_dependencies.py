import yaml
import ast
import pandas as pd
from pprint import pprint

class DepAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.deps = []
        self.crosswalk = {"deps":[]}
        self.funcs = []

    def visit_Assign(self, node):
        lhs, = node.targets
        rhs = node.value
        self.generic_visit(rhs)

    def visit_Attribute(self, node):
        print(ast.dump(node))
        dataset = None
        if type(node.value) is ast.Name:
            dataset = node.value.id
        else:
            self.visit(node.value)
        if node.attr == "aggregate":
            #self.deps += [f"{node.value.id}.{node.value.id}_id"]
            self.crosswalk["tgt_id"] = f"{dataset}_id"
        elif node.attr == "disaggregate":
            #self.deps += [f"{node.value.id}.{node.value.id}_id"]
            self.crosswalk["src_ds"] = f"{dataset}"
        elif dataset is not None:
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

def analyze_dependency(vardef_yml):
    dep_dict = {}
    def_dict = {}

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
            dep_dict[f"{df_name}.{lhs.id}"] = [f"{dep}" if "." in dep
                                                  else f"{df_name}.{dep}"
                                                for dep in analyzer.deps +
                                                   analyzer.crosswalk.get("deps")
                                               ]
            def_dict[f"{df_name}.{lhs.id}"] = expr #rhs
    return dep_dict, def_dict



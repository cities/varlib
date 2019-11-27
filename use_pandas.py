from yaml import load, dump
variables = load("variables.yml")

#TODO
#- [ ] parse variable definitions to find dependency graph between variables
#- [ ] auto insert its dependencies when a variable is evalualted
#- [ ] handle version of dependencies, only re-compute when a variable is stale
#- [ ]

import pandas as pd

class DataFrame(pd.DataFrame):
    def __init__(self, args, kwargs):
        super(self).__init__(args, **kwargs)

    def aggregate(self, attr, func="sum", resolver=None):
        df1_id = f"{self.name}_id"
        df2_name, vname = attr.split(".")
        df2 = resolver["df2_name"]
        res = df2.group_by(df1_id).agg({vname:func})
        return self.join(res[vname]).values

    def disaggregate(self, attr, resolver=None):
        df1_id = f"{self.name}_id"
        df2_name, vname = attr.split(".")
        df2 = resolver["df2_name"]
        return self.join(df2[vname]).values
    



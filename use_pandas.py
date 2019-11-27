from yaml import load, dump
variables = load("variables.yml")

import pandas as pd

def aggregate(attr, tgt_df, func="sum", resolvers=None):
    df1_id = f"{tgt_df.name}_id"
    df2_name, vname = attr.split(".")
    df2 = resolvers["df2_name"]
    res = df2.group_by(df1_id).agg({vname:func})
    return tgt_df.join(res[vname]).values

def disaggregate(attr, tgt_df, resolvers=None):
    df1_id = f"{tgt_df.name}_id"
    df2_name, vname = attr.split(".")
    df2 = resolvers["df2_name"]
    return tgt_df.join(df2[vname]).values

class DataFrame(pd.DataFrame):
    def __init__(self, args, kwargs):
        super(self).__init__(args, **kwargs)

    def aggregate(self, attr, func="sum", tgt_df = "", resolvers=None):
        df1_id = f"{self.name}_id"
        df2_name, vname = attr.split(".")
        df2 = resolver["df2_name"]
        res = df2.group_by(df1_id).agg({vname:func})
        return self.join(res[vname]).values

    def disaggregate(self, attr, tgt_df = "", resolvers=None):
        df1_id = f"{self.name}_id"
        df2_name, vname = attr.split(".")
        df2 = resolver["df2_name"]
        return self.join(df2[vname]).values
    



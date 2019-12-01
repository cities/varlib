import logging
import xxhash
import time

logging_indent_spaces_per_level = 2 * ' '

def log_function_entry_and_exit(decorated_function):
    """
    Function decorator logging entry + exit and parameters of functions.
    Entry and exit as logging.info, parameters as logging.DEBUG.
    https://stackoverflow.com/a/39643469/688693
    """
    from functools import wraps

    @wraps(decorated_function)
    def wrapper(*dec_fn_args, **dec_fn_kwargs):
        # Log function entry
        func_name = decorated_function.__name__
        log = logging.getLogger(func_name)

        # get function params (args and kwargs)
        arg_names = decorated_function.__code__.co_varnames
        params = dict(
            args=dict(zip(arg_names, dec_fn_args)),
            kwargs=dec_fn_kwargs)

        vname = params['args']["full_vname"]
        level = params['kwargs'].get('level', 0)
        if type(vname) is not list:
            indent = logging_indent_spaces_per_level * level
            log.info(f'{indent}Computing {vname} started ...')
            t0 = time.time()
            #log.debug(
            #    "\t" + ', '.join([
            #        '{}={}'.format(str(k), repr(v)) for k, v in params.items()]))
            # Execute wrapped (decorated) function:
            out = decorated_function(*dec_fn_args, **dec_fn_kwargs)
            time_lapsed = time.time() - t0
            log.info(f'{indent}Computing {vname} done in {time_lapsed:.2f}s.')
        else:
            out = decorated_function(*dec_fn_args, **dec_fn_kwargs)

        return out
    return wrapper

@log_function_entry_and_exit
def compute(full_vname, dep_graph, resolvers, recompute=False, level=0):
    if type(full_vname) is list:
        [compute(a_vname, dep_graph, resolvers, recompute=recompute, level=0)
                 for a_vname in full_vname]
        return

    assert dep_graph.has_node(full_vname), f"{full_vname} not in dep_graph"
    df_name, vname= full_vname.split(".")
    df = resolvers[df_name]
    deps_up_to_date = True
    xxh64_hash = xxhash.xxh64()
    for dep_full_vname in dep_graph.predecessors(full_vname):
        dep_df_name, dep_vname = dep_full_vname.split(".")
        #if dep_vname not in resolvers[dep_df_name].columns:
        compute(dep_full_vname, dep_graph, resolvers, level=level+1)
        xxh64_hash.update(resolvers[dep_df_name][dep_vname].values)
        current_hash = xxh64_hash.intdigest()
        xxh64_hash.reset()
        dep_hash = dep_graph.nodes[dep_full_vname].get("hash", "")
        if dep_hash != current_hash:
            deps_up_to_date = False
            dep_graph.nodes[dep_full_vname]["hash"] = current_hash

    vname_exists = vname in df.columns
    log = logging.getLogger('compute')
    indent = logging_indent_spaces_per_level * (level + 1)
    if not vname_exists or not deps_up_to_date or recompute:
        var_def = dep_graph.nodes[full_vname]['expr']
        #var_def = f"{vname} = {var_def}"
        df.eval(var_def, inplace=True)
        reason = 'new variable' * (not vname_exists) or \
                 'forced recomputing' * recompute or \
                 'dependency updated' * (not deps_up_to_date)
        log.info(f'{indent}Computing {full_vname} ({reason})')
    else:
        log.info(f'{indent}Computing {full_vname} skipped')

    return

#import sys
#sys.path = ["/home/lmwang/py3env/lib/python3.8/site-packages"] + sys.path
#
#from importlib import reload
#import pandas as pd
#import numpy as np
#from pandas.core.computation.expr import Expr
#from pandas.core.computation.scope import Scope
#
#code = "sqrt_nch = sqrt(nchildren + 1)"
##env = Scope(1, local_dict={"hhsize":3, "nchildren":2}, target="c")
##aa = Expr(code, env=env)
#
#pp_data = {'person_id': [1, 2, 3, 4],
#           'household_id': [1, 1, 2, 2],
#           'age':[2,   26,  39, 10],
#           'sex':['F', 'F', 'M', 'M']}
## Create DataFrame
#person = pd.DataFrame(pp_data).set_index("person_id")
#person.name = "person"
#
##person = person.assign(is_child=lambda x: (x["age"]<18).astype(int))
##pd.eval("is_child=np.where(person.age<18, 1, 0)", target=person)
##person.eval("is_child=np.where(age<18, 1, 0)", inplace=True, np=np)
#
#
#hh_data = {'household_id': [1, 2, 3]}
## Create DataFrame
#household = pd.DataFrame(hh_data).set_index("household_id")
#household.name = "household"
#
#one = 1
#from pandas import to_numeric
#np.ndarray.astype
#
#person.eval("(age)**2")
#person.eval("sqrt(age<18)")
#person.eval("@to_numeric(age<18)")
#
#person.eval("(age).astype('int')", engine="python")
#pd.eval("(person.age).astype('int')")
#
#person.eval("@(age)")

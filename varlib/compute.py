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
def compute(full_vname, dep_graph, resolvers, *args,
            functions={}, recompute=False, level=0,
            **kwargs):
    if type(full_vname) is list:
        [compute(a_vname, dep_graph, resolvers, *args,
                 functions=functions, recompute=recompute, level=0,
                 **kwargs)
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
        compute(dep_full_vname, dep_graph, resolvers, *args,
                functions=functions, level=level+1,
                #recompute=recompute,
                # when forced to recompute should we force recomputing its
                # dependencies?
                **kwargs)
        xxh64_hash.update(resolvers[dep_df_name][dep_vname].values)
        current_hash = xxh64_hash.intdigest()
        xxh64_hash.reset()
        dep_hash = dep_graph.nodes[dep_full_vname].get("hash", None)
        if dep_hash != current_hash:
            deps_up_to_date = False
            dep_graph.nodes[dep_full_vname]["hash"] = current_hash

    vname_exists = vname in df.columns
    log = logging.getLogger('compute')
    indent = logging_indent_spaces_per_level * (level + 1)
    if not vname_exists or not deps_up_to_date or recompute:
        var_def = dep_graph.nodes[full_vname].get('expr', '')
        assert var_def != '', f'The variable definition for {full_vname} cannot be found.'
        #var_def = f"{vname} = {var_def}"
        #df.eval(var_def, *args, inplace=True, **kwargs)
        eval_assign(var_def, resolvers=resolvers, functions=functions,
                    inplace=True)
        reason = 'new variable' * (not vname_exists) or \
                 'forced recomputing' * recompute or \
                 'dependency updated' * (not deps_up_to_date)
        log.info(f'{indent}Computing {full_vname} ({reason})')
    else:
        log.info(f'{indent}Computing {full_vname} skipped')

    return

def eval_assign(expr, target_ds=None, target_col=None, resolvers={}, functions={},
         inplace=True):
    import ast
    import astor
    from simpleeval import SimpleEval
    s = SimpleEval()
    s.names.update(resolvers)
    s.functions.update(functions)
    #import ipdb; ipdb.set_trace()
    ret = s.eval(expr)
    if inplace:
        if target_ds is None or target_col is None:
            expr_mod = ast.parse(expr).body[0]
            assert type(expr_mod) is ast.Assign
            src_target = astor.to_source(expr_mod.targets[0]).strip()
            target_ds, target_col = src_target.split(".")
        #import ipdb; ipdb.set_trace()
        resolvers[target_ds][target_col] = ret.values
        return resolvers[target_ds]
    else:
        return ret

def aggregate(expr, target_ds, source_ds, func="sum", resolvers={}):
    #import ipdb; ipdb.set_trace()
    tgt_df = resolvers[target_ds]
    tgt_df_id = f"{target_ds}_id"
    #src_ds, vname = expr.split(".")
    src_df = resolvers[source_ds]
    vname = expr.name
    assert all(src_df[vname] == expr)
    #src_df['_temp_vname'] = expr
    res = src_df.groupby(tgt_df_id).agg({vname: func})
    return res.loc[tgt_df.index, vname]

def disaggregate(expr, target_ds, source_ds, resolvers={}):
    tgt_df = resolvers[target_ds]
    #src_ds, vname = expr.split(".")
    src_df = resolvers[source_ds]
    vname = expr.name
    assert all(src_df[vname] == expr)
    src_df_id = f"{source_ds}_id"
    return src_df.loc[tgt_df[src_df_id], vname]


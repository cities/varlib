from varlib.parse import build_graph
from varlib.compute import compute, aggregate, disaggregate
import pandas as pd
import numpy as np

# tests
def compare_dict(dict1, dict2, verbose=True):
    for x1 in dict1.keys():
        z = set(dict1.get(x1)) == set(dict2.get(x1))
        if not z and verbose:
            print('key', x1)
            print('Actual', dict1.get(x1), '\nExpected', dict2.get(x1))
            print('-----\n')
        assert z


#compare_dict(resulted_dict, expected_dict)
def test_parse_deps():
    expected_dict = {
        'household.hhsize': ['person.household_id'],
        'household.nadults': ['household.hhsize', 'household.nchildren'],
        'household.cars_per_adults': ['household.cars', 'household.nadults'],
        'household.cars_per_adults_gt1': ['household.cars_per_adults'],
        'household.sqrt_hhsize': ['household.hhsize'],
        'household.nchildren': ['person.is_child_int', 'person.household_id'],
        'person.person_id': ['person.household_id', 'person.member_id'],
        'person.log1p_age': ['person.age'],
        'person.is_child': ['person.age'],
        'person.is_child_int': ['person.age'],
        'person.hh_nadults': ['household.nadults', 'person.household_id'],
        'person.is_girl': ['person.is_child', 'person.sex'],
        'zone.nadults': ['household.nadults', 'household.zone_id']
        }

    dep_graph = build_graph("example/variables.yml")
    resulted_dict = dict([(v, list(dep_graph.predecessors(v)))
                            for v in expected_dict.keys()])
    compare_dict(resulted_dict, expected_dict, verbose=True)

def prep_resolvers():
    # Create DataFrame
    pp_data = {'member_id': [1, 2, 3, 4],
            'household_id': [1, 1, 2, 2],
            'age':[2,   26,  39, 10],
            'sex':['F', 'F', 'M', 'M']}
    person = pd.DataFrame(pp_data)
    person.name = "person"

    hh_data = {'household_id': [1, 2],
               'cars': [1, 2],
               'zone_id': [1, 2]}
    household = pd.DataFrame(hh_data).set_index("household_id")
    household.name = "household"

    zn_data = {'zone_id': [1, 2]}
    zone = pd.DataFrame(zn_data).set_index("zone_id")
    zone.name = "zone"
    resolvers = {"person": person,
                 "household": household,
                 "zone": zone}
    resolvers['resolvers'] = resolvers
    return resolvers

dep_graph = build_graph("example/variables.yml")
def test_compute_simple_vars():
    resolvers = prep_resolvers()
    functions = {'logical_and': np.logical_and, 'log': np.log}
    person = resolvers["person"]
    compute("person.is_girl", dep_graph, resolvers=resolvers, functions=functions)
    assert 'is_girl' in person.columns
    assert np.all(person['is_girl'].values ==
                  np.array([True, False, False, False]))
    assert 'is_child' in person.columns
    assert np.all(person['is_child'].values ==
                  np.array([True, False, False, True]))
    compute("person.log1p_age", dep_graph, resolvers=resolvers, functions=functions)
    assert 'log1p_age' in person.columns
    assert np.allclose(person['log1p_age'].values,
                       np.array([1.09861229, 3.29583687, 3.68887945, 2.39789527]))
    compute("person.person_id", dep_graph, resolvers=resolvers, engine='python')

def test_compute_lazy_recompute():
    resolvers = prep_resolvers()
    functions = {'logical_and': np.logical_and}
    person = resolvers["person"]
    compute("person.is_girl", dep_graph, resolvers=resolvers, functions=functions)
    assert 'is_girl' in person.columns
    col1 = person['is_girl']
    compute("person.is_girl", dep_graph, resolvers=resolvers, functions=functions)
    assert id(person['is_girl']) == id(col1), "lazy recompute not enabled"
    compute("person.is_girl", dep_graph, resolvers=resolvers, functions=functions,
            recompute=True)
    assert id(person['is_girl']) != id(col1), "force recompute failed"
    col2 = person['is_girl']
    person['age'] += 10
    compute("person.is_girl", dep_graph, resolvers=resolvers, functions=functions)
    assert id(person['is_girl']) != id(col2), "failed to recompute when deps change"

def test_compute_type_conversion():
    resolvers = prep_resolvers()
    person = resolvers["person"]
    compute("person.is_child_int", dep_graph, resolvers=resolvers)
    compute("person.is_child_int2", dep_graph, resolvers=resolvers)
    compute("person.is_child", dep_graph, resolvers=resolvers)
    assert {'is_child', 'is_child_int', 'is_child_int2'}.issubset(person.columns)
    assert np.all(person['is_child_int'].values == (person['is_child'].values).astype(int))
    assert np.all(person['is_child_int'].values == person['is_child_int2'])

def test_compute_dep_other():
    resolvers = prep_resolvers()
    #resolvers['resolvers'] = resolvers
    functions = {'logical_and': np.logical_and,
                'aggregate': aggregate,
                'disaggregate': disaggregate}

    person = resolvers["person"]
    household = resolvers["household"]
    compute("household.cars_per_adults_gt1", dep_graph, resolvers=resolvers,
            functions=functions)
    assert 'is_child_int' in person.columns
    assert {'nchildren', 'nadults', 'cars_per_adults'}.issubset(household.columns)
    assert all(household['cars_per_adults_gt1'].values == np.array([False, True]))

def test_compute_dep_others():
    resolvers = prep_resolvers()
    person = resolvers["person"]
    household = resolvers["household"]
    zone = resolvers["zone"]
    #resolvers['resolvers'] = resolvers
    functions = {'logical_and': np.logical_and,
                'aggregate': aggregate,
                'disaggregate': disaggregate}

    compute("zone.nadults", dep_graph, resolvers=resolvers, functions=functions)
    assert 'is_child_int' in person.columns
    assert {'nchildren', 'nadults'}.issubset(household.columns)
    assert 'nadults' in zone.columns
    assert all(zone['nadults'].values == np.array([1, 1]))

def test_compute_round_trip():
    resolvers = prep_resolvers()
    person = resolvers["person"]
    household = resolvers["household"]
    resolvers['resolvers'] = resolvers
    functions = {'logical_and': np.logical_and,
                'aggregate': aggregate,
                'disaggregate': disaggregate}

    compute("person.hh_nadults", dep_graph, resolvers=resolvers, functions=functions)
    assert {'is_child_int', 'hh_nadults'}.issubset(person.columns)
    assert {'nchildren', 'nadults'}.issubset(household.columns)
    assert all(person['hh_nadults'].values == np.array([1, 1, 1, 1]))


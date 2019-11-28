from varlib.parse import build_graph, compute
import pandas as pd

# tests
def compare_dict(dict1, dict2, verbose=True):
    for x1 in dict1.keys():
        z = dict1.get(x1) == dict2.get(x1)
        assert z
        if not z and verbose:
            print('key', x1)
            print('Actual', dict1.get(x1), '\nExpected', dict2.get(x1))
            print('-----\n')


#compare_dict(resulted_dict, expected_dict)
def test_parse_deps():
    expected_dict = {'household.nadults': ['household.hhsize', 'household.nchildren'],
        'household.cars_per_adults': ['household.cars', 'household.nadults'],
        'household.cars_per_adults_gt1': ['household.cars_per_adults'],
        'household.sqrt_hhsize': ['household.hhsize'],
        'household.nchildren': ['person.is_child', 'person.household_id'],
        'person.is_child': ['person.age'],
        'person.is_child_int': ['person.age'],
        'person.nadults': ['household.nadults', 'person.household_id'],
        'person.is_girl': ['person.is_child', 'person.sex']
        }

    dep_graph = build_graph("example/variables.yml")
    resulted_dict = dict([(v, list(dep_graph.predecessors(v)))
                        for v in expected_dict.keys()])
    compare_dict(expected_dict, resulted_dict, verbose=False)

def test_compute():
    dep_graph = build_graph("example/variables.yml")

    pp_data = {'person_id': [1, 2, 3, 4],
            'household_id': [1, 1, 2, 2],
            'age':[2,   26,  39, 10],
            'sex':['F', 'F', 'M', 'M']}
    # Create DataFrame
    person = pd.DataFrame(pp_data).set_index("person_id")
    person.name = "person"

    compute("person.is_girl", dep_graph, resolvers={"person":person})
    assert 'is_girl' in person.columns
    assert 'is_child' in person.columns

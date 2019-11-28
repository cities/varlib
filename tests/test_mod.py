import varlib

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

    resulted_dict, _ = varlib.analyze_dependency("example/variables.yml")
    compare_dict(expected_dict, resulted_dict, verbose=False)


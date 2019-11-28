import sys
sys.path = ["/home/lmwang/py3env/lib/python3.8/site-packages"] + sys.path

from importlib import reload
import pandas as pd
import numpy as np
from pandas.core.computation.expr import Expr
from pandas.core.computation.scope import Scope

code = "sqrt_nch = sqrt(nchildren + 1)"
#env = Scope(1, local_dict={"hhsize":3, "nchildren":2}, target="c")
#aa = Expr(code, env=env)

pp_data = {'person_id': [1, 2, 3, 4],
           'household_id': [1, 1, 2, 2],
           'age':[2,   26,  39, 10],
           'sex':['F', 'F', 'M', 'M']}
# Create DataFrame
person = pd.DataFrame(pp_data).set_index("person_id")
person.name = "person"

#person = person.assign(is_child=lambda x: (x["age"]<18).astype(int))
#pd.eval("is_child=np.where(person.age<18, 1, 0)", target=person)
#person.eval("is_child=np.where(age<18, 1, 0)", inplace=True, np=np)


hh_data = {'household_id': [1, 2, 3]}
# Create DataFrame
household = pd.DataFrame(hh_data).set_index("household_id")
household.name = "household"

one = 1
from pandas import to_numeric
np.ndarray.astype

person.eval("(age)**2")
person.eval("sqrt(age<18)")
person.eval("@to_numeric(age<18)")

person.eval("(age).astype('int')", engine="python")
pd.eval("(person.age).astype('int')")

person.eval("@(age)")

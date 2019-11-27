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

one = 1
from pandas import to_numeric

#import ipdb
#ipdb.set_trace()
person.eval("(age)**2")
person.eval("(age).astype('int')", engine="python")
person.eval("sqrt(age<18)")
person.eval("@to_numeric(age<18)")
person.eval("(age<18).astype('int')")
pd.eval("(person.age).astype('int')")

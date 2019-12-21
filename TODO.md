# TODO
- [x] parse variable definitions to find dependency graph for variables
- [x] recursively compute its dependencies before a variable is evalualted (computed)
- [x] refactor varlib into a python package
- [x] automate tests
- [x] handle version of dependencies, only re-compute when a variable is stale
   - insert hash digest as 'version' attr in the dep graph for a variable is computed
   - insert hash digest of dependencies variables into the dependency graph at computing if a column of the name of the variable exists and its version attr in dep graph is not set
   - re-compute a variable only when 'version' attr for predecessors is not set or differ from current value of hash digest
- [x] a simpler yet safe parser for parsing common expressions to be evaluated, e.g.
   * person.eval("@to_numeric(age<18)")
   * person.eval("(age<18).astype('int')")
   * pd.eval("(person.age).astype('int')")
   - [ ] find references of data frame columns in an expression and replace them with Series from the resolvers
   - [ ] does this approach disable the numexpr engine?
   - [ ] how much advantage does the numexpr engine provide?
- [ ] are there other common patterns of variable definitions that need to support?
- [ ] is there a need to specify dataset relationship? If yes, what is the most sensible way to do so?
- [ ] get feedback from Paul and team
- [ ] a variable checker that verifies variable definitions
- [ ] cache dep_graph on disk
- [x] if a predecessor doesn't have predecessor, don't call compute on it
   e.g. person.is_child, if age is up-to-date, don't need to call compute(age), since age doesn't have any predecessor (primary attributes in opus)
- [ ] parallel computation of variables, zmq?

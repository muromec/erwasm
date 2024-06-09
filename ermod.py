class Module:
  def __init__(self, name, export_funcs, functions):
    self.name = name
    self.functions = functions
    self.export_funcs = export_funcs

  def find_function(self, start_label):
    for func in self.functions:
      if func.start_label == start_label:
        return func
    raise ValueError(f'No function found {start_label}')

class Func:
  def __init__(self, name, arity, start_label):
    self.name = name
    self.arity = arity
    self.start_label = start_label
    self.statements = []


def make_module(parse_beam):
  module_name = None
  export_funcs = None
  current_func = None
  functions = []
  for sentence in parse_beam:
    typ = sentence[0]
    if typ == 'module':
      [name] = sentence[1]
      module_name = name
    if typ == 'exports':
      [func_list] = sentence[1]
      export_funcs = [
         (func[0], int(func[1][0]))
         for func in func_list
      ]
    if typ == 'function':
      [name, arity, start_label] = sentence[1]
      current_func = Func(name, int(arity), int(start_label))
      functions.append(current_func)
    elif current_func:
      current_func.statements.append(sentence)

  return Module(module_name, export_funcs, functions)

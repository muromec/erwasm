import os

MODULE = '''(module
   ;; module name: {name}
   {imports}
   (memory 1)
   (export "memory" (memory 0))
   {data}
   {body}
)'''

FUNC = '''
(func ${name}_{arity} {params} {result}
{body}
)
'''
FUNC_EXPORT = '''
(export "{name}/{arity}" (func ${name}_{arity}))
'''

FUNC_IMPORT = '''
(import "{mod}" "{fn}" (func ${mod}_{fn}_{arity} {params} (result i32 i32)))
'''

LITERAL = '''
  (data (i32.const {offset0}) "{llen}")
  (data (i32.const {offset1}) "{lval}")
'''

def pad(n):
  if len(n) == 1:
    return '0' + n
  return n

def make_len(n):
  len0 = n & 0xFF
  len1 = (n >> 8) & 0xFF
  len2 = (n >> 16) & 0xFF
  len3 = (n >> 24) & 0xFF

  len0s = pad(hex(len0)[2:])
  len1s = pad(hex(len1)[2:])
  len2s = pad(hex(len2)[2:])
  len3s = pad(hex(len3)[2:])

  return f'\\{len3s}\\{len2s}\\{len1s}\\{len0s}'

def make_result_n(n):
  if n == 0:
    return ''

  ret = 'i32 ' * n
  return f'(result {ret})'

def make_params_n(n):
  if n == 0:
    return ''

  ret = 'i32 ' * n
  return f'(param {ret})'

def make_in_params_n(n):
  idx = 0
  ret = ''
  while idx < n:
    ret += f'(param $in_{idx} i32) '
    idx += 1
  return ret

def produce_wasm(module):
  body = ''
  data = ''
  imports = []

  literalidx = 0
  for func in module.functions:
    for statement in func.statements:
      styp = statement[0]
      sbody = statement[1]

      if styp == 'move':
        [(styp, [sval]), (dtyp, [dval])] = sbody
        if styp == 'literal':
          data += LITERAL.format(
            offset0 = literalidx,
            offset1 = literalidx + 4,
            llen = make_len(len(sval)),
            lval = sval,
          )
          literalidx += 4
          literalidx += len(sval)

      if styp == 'call_ext':
        [ext_mod, ext_fn, ext_fn_arity] = statement[1][1][1]
        import_line = FUNC_IMPORT.format(
          mod=ext_mod, fn=ext_fn,
          arity=int(ext_fn_arity),
          params = make_params_n(int(ext_fn_arity) * 2),
        )
        if import_line not in imports:
          imports.append(import_line)

  literalidx = 0
  for func in module.functions:
    max_arity = max(int(func.arity), 1)
    max_yregs = 0
    if (func.name, func.arity) in module.export_funcs:
      body += FUNC_EXPORT.format(name=func.name, arity=func.arity)

    localvars = '\n'
    b = '\n'

    stack = 0
    arg = int(func.arity)
    reg = (arg * 2) - 1
    while arg > 0:
      b += f'local.get $in_{reg}\n'
      b += f'local.set $var_xreg_{arg - 1}_val\n'
      reg -= 1

      b += f'local.get $in_{reg}\n'
      b += f'local.set $var_xreg_{arg - 1}_tag\n'
      reg -= 1

      arg -= 1

    for statement in func.statements:
      styp = statement[0]
      sbody = statement[1]
      if styp == 'allocate':
        [yreg, xreg] = sbody
        max_yregs = max(max_yregs, int(yreg))
        max_arity = max(max_arity, int(xreg))
      if styp == 'trim':
        [nremove, nleft] = sbody
        nremove = int(nremove)
        nleft = int(nleft)
        for yreg in range(0, nleft):
          b += f'local.get $var_yreg_{yreg + nremove}_tag\n'
          b += f'local.set $var_yreg_{yreg}_tag\n'
          b += f'local.get $var_yreg_{yreg + nremove}_val\n'
          b += f'local.set $var_yreg_{yreg}_val\n'

      if styp == 'move':
        [(styp, [sval]), (dtyp, [dval])] = sbody
        if styp == 'integer':
          b += f'(local.set $var_{dtyp}reg_{dval}_tag (i32.const 0))\n'
          b += f'(local.set $var_{dtyp}reg_{dval}_val (i32.const {sval}))\n'
        elif styp == 'literal':
          b += f'(local.set $var_{dtyp}reg_{dval}_tag (i32.const 10))\n'
          b += f'(local.set $var_{dtyp}reg_{dval}_val (i32.const {literalidx}))\n'
          literalidx += 4
          literalidx += len(sval)
        elif styp == 'x' or styp == 'y':
          b += f'local.get $var_{styp}reg_{sval}_tag\n'
          b += f'local.set $var_{dtyp}reg_{dval}_tag\n'
          b += f'local.get $var_{styp}reg_{sval}_val\n'
          b += f'local.set $var_{dtyp}reg_{dval}_val\n'

        if styp == 'x':
          max_arity = max(max_arity, int(sval) + 1)
        if dtyp == 'x':
          max_arity = max(max_arity, int(dval) + 1)

        else:
          continue

      if styp == 'call_ext':
        [ext_mod, ext_fn, ext_fn_arity] = statement[1][1][1]
        max_arity = max(max_arity, int(ext_fn_arity))

        for xreg in range(0, int(ext_fn_arity)):
          b += f'local.get $var_xreg_{xreg}_tag\n'
          b += f'local.get $var_xreg_{xreg}_val\n'

        b += f'call ${ext_mod}_{ext_fn}_{ext_fn_arity}\n'
        b += f'local.set $var_xreg_0_val\n'
        b += f'local.set $var_xreg_0_tag\n'

        assert stack >= 0, f"Stack shold grow {stack}"

      if styp == 'call_only':
        [arity, (_f, [findex])] = sbody
        arity = int(arity)
        findex = int(findex)
        into_func = module.find_function(findex)

        for xreg in range(0, arity):
          b += f'local.get $var_xreg_{xreg}_tag\n'
          b += f'local.get $var_xreg_{xreg}_val\n'

        b += f'call ${into_func.name}_{into_func.arity}\n'
        b += f'local.set $var_xreg_0_val\n'
        b += f'local.set $var_xreg_0_tag\n'

        max_arity = max(max_arity, arity)

      if styp == 'gc_bif':
        [op, _fall, arity, [arg0, arg1], ret] = sbody
        (arg0t, [arg0v]) = arg0
        (arg1t, [arg1v]) = arg1
        (retT, [retV]) = ret

        if arg0t == 'x' or arg0t == 'y':
          b += f'local.get $var_{arg0t}reg_{arg0v}_val\n'
        if arg1t == 'x' or arg1t == 'y':
          b += f'local.get $var_{arg1t}reg_{arg1v}_val\n'

        if op == "'+'":
          b += 'i32.add\n'

        if retT == 'x' or retT == 'y':
          b += f'local.set $var_{retT}reg_{retV}_val\n'
          b += f'(local.set $var_{retT}reg_{retV}_tag (i32.const 0))\n'
    while stack > 0:
      stack -= 1
      b += 'drop\n'

    b += f'local.get $var_xreg_0_tag\n'
    b += f'local.get $var_xreg_0_val\n'
    stack = 2

    for xreg in range(0, max_arity):
      localvars += f'(local $var_xreg_{xreg}_tag i32)\n'
      localvars += f'(local $var_xreg_{xreg}_val i32)\n'

    for yreg in range(0, max_yregs):
      localvars += f'(local $var_yreg_{yreg}_tag i32)\n'
      localvars += f'(local $var_yreg_{yreg}_val i32)\n'

    body += FUNC.format(
      name=func.name,
      arity=func.arity,
      params=make_in_params_n(int(func.arity) * 2),
      result=make_result_n(stack),
      body=localvars + b
    )

  return MODULE.format(name=module.name, imports="\n".join(imports), data=data, body=body)

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

def parse_list_sentence_helper(text, State):
  ret = []
  state = None
  while State.idx < len(text):
    symbol = text[State.idx]
    State.idx += 1
    if symbol == ']':
      break
    elif state == None and symbol == '{':
      child_sentence = parse_sentence_helper(text, State)
      ret.append(child_sentence)
    elif state == None and symbol in ['[', '"']:
      assert False, 'cant be!'

  return ret


def clean_v(value):
  if value[0] == '"' and value[-1] == '"':
    value = value[1:-1]
  return value

def parse_sentence_helper(text, State):
  state = 'name'
  ret = []
  sentence = None
  name = ''
  children = []
  arg_name = ''

  while State.idx < len(text):
    symbol = text[State.idx]
    State.idx += 1
    if symbol == '}':
      break
    elif state == 'name' and symbol not in [' ', ',']:
      name += symbol
    elif state == 'name':
      state = None
    elif state == None and symbol in [' ', ',']:
      pass
    elif state == None and symbol == '[':
      child_sentence = parse_list_sentence_helper(text, State)
      children.append(child_sentence)
    elif state == None and symbol == '{':
      child_sentence = parse_sentence_helper(text, State)
      children.append(child_sentence)
    elif state == None:
      state = 'arg_name'
      arg_name = symbol
    elif state == 'arg_name' and symbol in [' ', ',']:
      children.append(clean_v(arg_name))
      state = None
      arg_name = None
    elif state == 'arg_name':
      arg_name += symbol
    
  if arg_name:
    children.append(clean_v(arg_name))

  return name, children

def parse_sentence(text):
  class State:
   idx = 1

  return parse_sentence_helper(text, State)

def parse_beam(text):
  state = None
  ret = []
  sentence = None
  for symbol in text:
    if state == None and symbol == '{':
      state = 'inside'
      sentence = symbol
    elif state == 'inside' and symbol == '.':
      state = None
      ret.append(sentence)
      sentence = None
    elif state == 'inside' and symbol == '"':
      state = 'inside_literal'
      sentence += symbol
    elif state == 'inside_literal' and symbol == '"':
      state = 'inside'
      sentence += symbol
    elif state == 'inside' or state == 'inside_literal':
      sentence += symbol

  return ret


def main(fname):
  print('compile f', fname)
  input_file = fname
  output_file = fname.replace('.erl', '.S')
  output_wat_file = fname.replace('.erl', '.wat')
  output_wasm_file = fname.replace('.erl', '.wasm')

  try:
    os.remove(output_file)
  except FileNotFoundError:
    pass
  os.system('erlc -S ' + fname)
  with open(output_file, 'r') as beam_text_f:
    beam_text = beam_text_f.read()
    sentences =  parse_beam(beam_text)
    mod = make_module(map(parse_sentence, sentences))
    wat_text = produce_wasm(mod)
    with open(output_wat_file, 'w') as wat_text_f:
      wat_text_f.write(wat_text)

  os.system('wat2wasm ' + output_wat_file)
  os.system('node run.js ' + output_wasm_file)


if __name__ == '__main__':
  import sys
  main(*sys.argv[1:])

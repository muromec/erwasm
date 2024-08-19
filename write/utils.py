from erparse import Atom
from write.literals import add_literal, GLOBAL_CONST, pack_reg_value

FUNC_IMPORT = '''
(import "{mod}" "{fn}_{arity}" (func ${mod}_{fn}_{arity} {params} (result i32)))
'''

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

def add_import(ctx, ext_mod, ext_fn, ext_fn_arity):
  import_line = FUNC_IMPORT.format(
    mod=ext_mod, fn=ext_fn,
    arity=int(ext_fn_arity),
    params = make_params_n(int(ext_fn_arity)),
  )
  if import_line not in ctx.imports:
    ctx.imports.append(import_line)

def ignore_call(ext_mod, ext_fn):
  if ext_mod == 'erlang' and ext_fn == 'get_module_info':
    return True


def pop(ctx, typ, num):
  assert typ in ['x', 'y']

  if typ == 'x':
    ctx.max_xregs = max(ctx.max_xregs, num + 1)
  if typ == 'y':
    ctx.max_yregs = max(ctx.max_yregs, num, + 1)

  return f'local.set $var_{typ}reg_{num}_val\n'

def push(ctx, typ, num):
  assert typ in ['x', 'y']

  if typ == 'x':
    ctx.max_xregs = max(ctx.max_xregs, num + 1)
  if typ == 'y':
    ctx.max_yregs = max(ctx.max_yregs, num, + 1)

  return f'local.get $var_{typ}reg_{num}_val\n'

def move(ctx, styp, snum, dtyp, dnum):
  b = push(ctx, styp, snum)
  b += pop(ctx, dtyp, dnum)
  return b

def populate_stack_with(ctx, value):
  if value == 'nil':
    return '(i32.const 0x3b)\n'

  if isinstance(value, int):
    value = ['integer', [value]]

  if value[0] == 'tr':
    value = value[1][0]

  if value[0] == 'literal' and value[1] == []:
    value= (value[0], [[]])

  [typ, [val]] = value
  b = ''
  if typ == 'integer':
    pval = pack_reg_value(ctx, int(val))
    b += f'(i32.const {pval})\n'
  elif typ == 'atom':
    # print('v', val)
    (atom_name, _atom_id) = ctx.register_atom(str(val))
    b += f'(global.get $__unique_atom__{str(atom_name)}) ;; atom {val}\n'
  elif typ == 'literal':
    (_offset, literal_name) = add_literal(ctx, val)
    b += f'(global.get ${literal_name})\n'
  elif typ == 'x' or typ == 'y':
    b += push(ctx, typ, int(val))
  else:
    assert False, 'not implemented {typ}'.format(typ=typ)

  return b

def populate_with(ctx, dtyp, dnum, value):
  b = populate_stack_with(ctx, value)
  b += f'(local.set $var_{dtyp}reg_{dnum}_val)\n'
  return b

def arg(value):
  [typ, [num]] = value
  assert typ in ('x', 'y')
  return typ, int(num)


def get_atoms(ctx):
  b = ';; atoms table\n'
  for (key, value) in ctx.atoms.items():
    b += GLOBAL_CONST.format(name=f'__unique_atom__{key}', value=value)

  return b

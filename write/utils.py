from codecs import decode
from erparse import Atom

FUNC_IMPORT = '''
(import "{mod}" "{fn}_{arity}" (func ${mod}_{fn}_{arity} {params} (result i32)))
'''

LITERAL = '''
  (data (i32.const {offset}) "{value}")
'''
GLOBAL_CONST = '''
  (global ${name} i32 (i32.const {value}))
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

def pad(n):
  if len(n) == 1:
    return '0' + n
  return n


def escape_bin(byte_list):
  ret = ''
  for b_value in byte_list:
    b_value_s = pad(hex(b_value)[2:])
    ret += f'\\{b_value_s}'

  return ret

def make_word(n):
  len3 = n & 0xFF
  len2 = (n >> 8) & 0xFF
  len1 = (n >> 16) & 0xFF
  len0 = (n >> 24) & 0xFF
  return [len3, len2, len1, len0]


def fix_string(value):
  return  decode(value, 'unicode-escape')

def pack_reg_value(ctx, value):
  if isinstance(value, Atom):
    (_atom_name, atom_id) = ctx.register_atom(str(value))
    return (atom_id << 6 | 0xB)

  if isinstance(value, int):
    return (value << 4 | 0xF)

  assert False, ('unknown typ', value, type(value))

def fix_tuple(value):
  if len(value) == 2 and isinstance(value[1], list):
    value = (value[0],) + tuple(value[1])
  value = tuple((
    fix_tuple(item) if isinstance(item, tuple) else item
    for item in value
  ))
  return value

def pack_literal(ctx, value, base_offset):
  if isinstance(value, Atom) or isinstance(value, int):
    return make_word(pack_reg_value(ctx, value))

  if isinstance(value, str):
    value = list(map(ord, fix_string(value)))

  if isinstance(value, list):
    value = [
      pack_literal(ctx, item, base_offset)
      for item in value
    ]
    ret = []
    for s_value in value:
      s_len = len(s_value) + 4
      ret += make_word(s_len << 2 | 1)
      ret += s_value

    ret += make_word(0x3b)
    ret += make_word(0)

    return ret

  if isinstance(value, tuple):
    value = fix_tuple(value)
    ret = make_word(len(value) << 6)
    for s_value in value:
      ret += make_word(pack_reg_value(ctx, s_value))

    return ret

  assert False, f'cant pack as constant value {value}'

def add_literal(ctx, sval):
  packed_value = pack_literal(ctx, sval, base_offset = ctx.literalidx)
  ctx.data += LITERAL.format(
    offset = ctx.literalidx,
    value = escape_bin(packed_value),
  )
  name = f'__{ctx.literalidx}__literal_ptr_raw'
  ctx.data += GLOBAL_CONST.format(
    name = name,
    value = ctx.literalidx,
  )
  name = f'__{ctx.literalidx}__literal_ptr_e'
  ctx.data += GLOBAL_CONST.format(
    name = name,
    value = (ctx.literalidx << 2) | 2,
  )

  ret = ctx.literalidx + 0
  ctx.literalidx += len(packed_value)
  return name

def push(ctx, typ, num):
  assert typ in ['x', 'y']

  if typ == 'x':
    ctx.max_xregs = max(ctx.max_xregs, num + 1)
  if typ == 'y':
    ctx.max_yregs = max(ctx.max_yregs, num, + 1)

  return f'local.get $var_{typ}reg_{num}_val\n'

def pop(ctx, typ, num):
  assert typ in ['x', 'y']

  if typ == 'x':
    ctx.max_xregs = max(ctx.max_xregs, num + 1)
  if typ == 'y':
    ctx.max_yregs = max(ctx.max_yregs, num, + 1)

  return f'local.set $var_{typ}reg_{num}_val\n'


def move(ctx, styp, snum, dtyp, dnum):
  b = push(ctx, styp, snum)
  b += pop(ctx, dryp, dnum)
  return b

def populate_stack_with(ctx, value):
  if value == 'nil':
    return '(i32.const 0x3b)\n'

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
    # pval = pack_reg_value(ctx, Atom(val))
    b += f'(global.get $__unique_atom__{str(atom_name)}) ;; atom {val}\n'
  elif typ == 'literal':
    literal_name = add_literal(ctx, val)
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

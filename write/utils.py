from codecs import decode

FUNC_IMPORT = '''
(import "{mod}" "{fn}" (func ${mod}_{fn}_{arity} {params} (result i32)))
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

def pad(n):
  if len(n) == 1:
    return '0' + n
  return n

def make_len(n):
  len3 = n & 0xFF
  len2 = (n >> 8) & 0xFF
  len1 = (n >> 16) & 0xFF
  len0 = (n >> 24) & 0xFF

  len0s = pad(hex(len0)[2:])
  len1s = pad(hex(len1)[2:])
  len2s = pad(hex(len2)[2:])
  len3s = pad(hex(len3)[2:])

  ret = f'\\{len3s}\\{len2s}\\{len1s}\\{len0s}'
  return ret

def fix_string(value):
  return  decode(value, 'unicode-escape')

def pack_literal(value):
  if isinstance(value, int):
    return (make_len(value), 0)

  if isinstance(value, str):
    value = list(map(ord, fix_string(value)))

  if isinstance(value, list):
    # print('pack literal', repr(value))
    assert all(map(lambda v: isinstance(v, int), value)), 'Only list of ints'
    ret = ''
    for int_value in value:
      ret += make_len(8 << 2 | 1)
      ret += make_len(int_value << 4 | 0xF)

    ret += make_len(0x3b)
    ret += make_len(0)

    return ret

  assert False, f'cant pack as constant value {value}'

def add_literal(ctx, sval):
  packed_value = pack_literal(sval)
  ctx.data += LITERAL.format(
    offset = ctx.literalidx,
    value = packed_value,
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
  push(ctx, styp, snum)
  pop(ctx, dryp, dnum)

def populate_stack_with(ctx, value):
  if value[0] == 'tr':
    value = value[1][0]
  [typ, [val]] = value
  b = ''
  if typ == 'integer':
    val = (int(val) << 4 | 0xF)
    b += f'(i32.const {val})\n'
  elif typ == 'literal':
    literal_name = add_literal(ctx, val)
    b += f'(global.get ${literal_name})\n'
  elif typ == 'atom':
    b += f'(i32.const 0)\n' # TODO: implement atoms
  elif typ == 'x' or typ == 'y':
    b += push(ctx, typ, int(val))
  else:
    assert False, 'not implemented {typ}'.format(typ=typ)

  return b

def populate_with(ctx, dtyp, dnum, value):
  b = populate_stack_with(ctx, value)
  b += f'(local.set $var_{dtyp}reg_{dnum}_val)\n'
  return b

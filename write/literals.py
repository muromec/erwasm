from codecs import decode
from erparse import Atom

GLOBAL_CONST = '''
  (global ${name} i32 (i32.const {value}))
'''

LITERAL = '''
  (data (i32.const {offset}) "{value}")
'''

# bin pack utils
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

def add_literal(ctx, sval):
  packed_value = pack_literal(ctx, sval)
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
  ctx.data += f';; erlang value {repr(sval)}, {type(sval)} \n'

  offset = ctx.literalidx + 0
  ctx.literalidx += len(packed_value)
  return (offset, name)

def make_word(n):
  len3 = n & 0xFF
  len2 = (n >> 8) & 0xFF
  len1 = (n >> 16) & 0xFF
  len0 = (n >> 24) & 0xFF
  return [len3, len2, len1, len0]

def fix_string(value):
  return decode(value, 'unicode-escape')

def pack_reg_value(ctx, value):
  if isinstance(value, Atom):
    (_atom_name, atom_id) = ctx.register_atom(str(value))
    return (atom_id << 6 | 0xB)

  if isinstance(value, int):
    return (value << 4 | 0xF)

  # This is technically UTF-32
  if isinstance(value, str):
    value = list(map(ord, fix_string(value)))

  if isinstance(value, (list, tuple, bytes)):
    (offset, _name) = add_literal(ctx, value)
    return (offset << 2 | 2)

  assert False, ('unknown typ', value, type(value))

def fix_tuple(value):
  if len(value) == 2 and isinstance(value[1], list):
    value = (value[0],) + tuple(value[1])
  value = tuple((
    fix_tuple(item) if isinstance(item, tuple) else item
    for item in value
  ))
  return value

def pack_literal(ctx, value):
  if isinstance(value, Atom) or isinstance(value, int):
    return make_word(pack_reg_value(ctx, value))

  if isinstance(value, str):
    value = list(map(ord, fix_string(value)))

  if isinstance(value, list):
    ret = []
    packed_items = [
      make_word(pack_reg_value(ctx, s_value))
      for s_value in value
    ]
    base_offset = ctx.literalidx
    for p_item in packed_items:
      base_offset += 8 # 4 bytes header + 4 bytes reg value
      ret += make_word(base_offset << 2 | 1)
      ret += p_item

    ret += make_word(0x3b)
    ret += make_word(0)

    return ret

  if isinstance(value, tuple):
    value = fix_tuple(value)
    ret = make_word(len(value) << 6)
    for s_value in value:
      ret += make_word(pack_reg_value(ctx, s_value))

    return ret

  if isinstance(value, bytes):
    ret = make_word(0x24)
    ret += make_word(len(value) << 3)
    ret += list(value)
    return ret

  assert False, f'cant pack as constant value {value}'


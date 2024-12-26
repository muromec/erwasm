import struct
import zlib
from ermod import Module, Func
from nodes import Atom

def consume_tuple(data, offset):
  ret = tuple()
  tuple_len = data[offset]
  offset += 1
  while tuple_len > 0:
    (part, offset) = consume_value(data, offset)
    ret += (part,)
    tuple_len -= 1

  return (ret, offset)


def consume_small_int(data, offset):
  value = data[offset]
  return (value, offset + 1)

def consume_int(data, offset):
  (value,) = struct.unpack_from('>i', data, offset = offset)
  return (value, offset + 4)

def consume_bin(data, offset):
  (blen,) = struct.unpack_from('>i', data, offset = offset)
  offset += 4
  value = data[offset : offset + blen]
  return (value, offset + blen)

def consume_short_bin(data, offset):
  (blen,) = struct.unpack_from('B', data, offset = offset)
  offset += 1
  value = data[offset : offset + blen]
  return (value, offset + blen)


def consume_atom(data, offset):
  (value, offset) = consume_short_bin(data, offset)
  value = value.decode('utf8')
  return (value, offset)

consumers = {
  0x68: consume_tuple,
  0x61: consume_small_int,
  0x62: consume_int,
  0x6d: consume_bin,
  0x77: consume_atom,
}

def consume_value(data, offset):
  tag = data[offset]
  offset += 1
  consumer = consumers.get(tag)
  if consumer:
    return consumer(data, offset)

  assert False, f"Unknown tag {hex(tag)} (decimal {tag})"

def parse_literals(data):
  ret = []

  (count,) = struct.unpack_from('>I', data)
  offset = 4
  while count:
    (plen, header) = struct.unpack_from('>IB', data, offset = 4)
    offset += 5

    if header != 131:
      raise ValueError('ETF header must be 131')

    part = data[offset : offset + plen]

    (value, offset) = consume_value(data, offset)
    count -= 1
    ret.append(value)

  # for idx, literal in enumerate(ret):
  #  print('literal', idx, literal)

  return ret

def parse_beam_chunks(data):
  dlen = len(data)
  offset = 0
  (header, flen, beam) = struct.unpack_from('>4sI4s', data, offset=offset)
  if header != b'FOR1' or beam != b'BEAM':
    raise ValueError('File is not am uncompressed beam file.')

  if flen != (dlen - 8):
    raise ValueError(f'Wrong file length {flen} != {dlen}')

  acc = {}
  offset = 12
  while offset < dlen:
    if data[offset] == 0: 
      offset += 1
      continue

    (header, flen) = struct.unpack_from('>4sI', data, offset=offset)
    chunk_data = data[offset+8 : offset + 8 + flen]
    offset += (flen + 8)

    acc[header.decode()]  = chunk_data

  if 'LitT' in acc:
    acc['LitT'] = zlib.decompress(acc['LitT'][4:])

  return acc

def parse_atoms(data):
  (count,) = struct.unpack_from('>I', data)
  offset = 4
  ret = ()
  while count > 0:
    (alen,) = struct.unpack_from('>B', data, offset = offset)
    offset += 1
    atom = data[offset : offset + alen].decode('utf8')
    offset += alen
    count -= 1
    ret += (Atom(atom),)

  return ret


def parse_imports(data, atoms):
  (count,) = struct.unpack_from('>I', data)
  offset = 4
  ret = ()
  while count > 0:
    (mod, fn, arity) = struct.unpack_from('>III', data, offset = offset)
    mod = atoms[mod - 1]
    fn = atoms[fn - 1]
    offset += 12
    count -= 1

    ret += ((mod, fn, arity),)

  return ret

def parse_exports(data, atoms):
  (count,) = struct.unpack_from('>I', data)
  offset = 4
  ret = ()
  while count > 0:
    (fn, arity, start) = struct.unpack_from('>III', data, offset = offset)
    fn = atoms[fn - 1]
    offset += 12
    count -= 1

    ret += ((fn, arity, start),)

  return ret


op_tab = {
  0x01: ('label', 1),
  0x02: ('func_info', 3),
  0x03: ('end', 0),
  0x04: ('call', 2),
  0x05: ('call_last', 3),
  0x06: ('call_only', 2),
  0x07: ('call_ext', 2),
  0x08: ('call_ext_last', 3),
  0x0b: ('bif2', 5),
  0x0a: ('bif1', 4),
  0x0c: ('allocate', 2),
  0x0d: ('allocate_heap', 3),
  0x10: ('test_heap', 2),
  0x12: ('deallocate', 1),
  0x13: ('return', 0),
  0x27: ('is_lt', 3),
  0x2b: ('is_eq_exact', 3),
  0x28: ('is_ge', 3),
  0x30: ('is_atom', 2),
  0x32: ('is_reference', 2),
  0x35: ('is_binary', 2),
  0x3b: ('select_val', 3),
  0x40: ('move', 2),
  0x4e: ('call_ext_only', 2),
  0x4a: ('case_end', 1), # this raises error
  0x6c: ('raise', 2),
  0x6e: ('bs_bits_to_bytes', 3),
  0x72: ('is_boolean', 2),
  0x7d: ('gc_bif2', 6),
  0x99: ('line', 1),
  0xa0: ('build_stacktrace', 0),
  0xa4: ('put_tuple2', 2),
  0xa5: ('bs_get_tail', 3),
  0xa6: ('bs_start_match3', 4),
  0xa7: ('bs_get_position', 3),
  0xa8: ('bs_set_position', 2),
  0xa9: ('swap', 2),
  0xb6: ('bs_match3', 3),
}


"""

-define(tag_u, 0).
-define(tag_i, 1).
-define(tag_a, 2).
-define(tag_x, 3).
-define(tag_y, 4).
-define(tag_f, 5).
-define(tag_h, 6).
-define(tag_z, 7).

"""
tags = ['u', 'i', 'a', 'x', 'y', 'f', 'h', 'z']


def decode_int(data, offset):
  value = data[offset]
  if not (value & 0x08):
    return (value >> 4, offset + 1)

  if not (value & 0x10):
    return (data[offset+1], offset + 2)

  value = value >> 5
  if value == 7:
    assert False, 'Decode long-ish int'

  read_bytes = value + 2
  value = 0
  size = 1
  while read_bytes:
    value = value << 8 | data[offset + size]
    size += 1
    read_bytes -= 1

  return (value, offset + size)

def decode_z(data, offset, literals, atoms, imports):
  typ_n = data[offset] >> 4
  if typ_n == 1:
    value = []
    asize = data[offset + 1] >> 4
    offset = offset + 2

    while asize:
      (apart, offset) = consume_arg(data, offset, literals, atoms, imports)
      asize -= 1
      value.append(apart)

    return (value, offset)

  if typ_n == 4:
    (value, offset) = decode_int(data, offset + 1)
    return (literals[value], offset)

  if typ_n == 5:
    (reg, offset) = consume_arg(data, offset + 1, literals, atoms, imports)
    (typ, offset) = consume_arg(data, offset, literals, atoms, imports)
    return (reg, offset)

  assert False, f'decode z {typ_n}'

def consume_arg(data, offset, literals, atoms, imports):
  value = data[offset]
  tag = tags[value & 0b111]
  # print('consume arg', tag, value)

  if tag == 'z':
    return decode_z(data, offset, literals, atoms, imports)

  (value, offset) = decode_int(data, offset)

  if tag == 'a':
    if not value:
      return (None, offset)

    value = atoms[value - 1]
    return (value, offset)

  if tag == 'f':
    return (('label', value), offset)

  if tag == 'x' or tag == 'y':
    return (('reg', tag, value), offset)

  return (value, offset)

def parse_code(data, literals, atoms, imports):
  offset = 0
  (header1, header2, header3, header4, header5) = struct.unpack_from('>IIIII', data, offset=offset)
  """
  print('header1', hex(header1))
  print('header2', hex(header2))
  print('header3', hex(header3))
  print('header4', hex(header4))
  print('header5', hex(header5))
  """

  offset += 20

  ops = []
  dlen = len(data)
  while offset < dlen:
    op = data[offset]
    if op not in op_tab:
      raise ValueError(f'Unknown opcode {hex(op)} (decimal {op})')

    (cmd, arity) = op_tab[op]
    offset += 1

    if op == 3: break

    args = []
    while arity > 0:
      (arg, offset) = consume_arg(data, offset, literals, atoms, imports)
      arity -= 1
      args.append(arg)

    # print('cmd', cmd, args)
    ops.append((cmd, args))

  assert op == 3 and offset == dlen


  functions = []
  current_label = None
  for (cmd, args) in ops:
    if cmd == 'label' and current_label:
      functions[-1].statements.extend(current_label)

    if cmd == 'label':
      current_label = []

    if cmd == 'label' and functions and not functions[-1].start_label:
      [functions[-1].start_label] = args
      # print('start label', args)

    if cmd == 'func_info':
      mod_name, func_name, arity = args
      functions.append(Func(func_name, int(arity), None))

    current_label.append(((cmd,) + tuple(args)))

  functions[-1].statements.extend(current_label)

  return functions

def parse(data):
  chunks = parse_beam_chunks(data)

  atoms = parse_atoms(chunks['AtU8'])
  imports = parse_imports(chunks['ImpT'], atoms)
  exports = parse_exports(chunks['ExpT'], atoms)

  literals = parse_literals(chunks['LitT']) if 'LitT' in chunks else []
  code = parse_code(chunks['Code'], literals, atoms, imports)

  return Module(
    atoms[0],
    [ (fn, arity) for (fn, arity, start) in exports ],
    code,
    {},
    imports,
  )


def main(fname):
  with open(fname, 'rb') as beam_f:
    data = beam_f.read()

  parse(data)

if __name__ == '__main__':
  import sys
  main(*sys.argv[1:])

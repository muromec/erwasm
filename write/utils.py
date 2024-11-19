import struct
from erparse import Atom
from write.literals import add_literal, add_named_literal, GLOBAL_CONST, pack_reg_value, add_atom

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
  if typ == 'x':
    ctx.max_xregs = max(ctx.max_xregs, num + 1)
  elif typ == 'y':
    ctx.max_yregs = max(ctx.max_yregs, num + 1)
  elif typ == 'fr':
    ctx.max_fregs = max(ctx.max_fregs, num + 1)
  else:
    assert False

  return f'(local.set $var_{typ}reg_{num}_val)\n'

def push(ctx, typ, num):
  if typ == 'x':
    ctx.max_xregs = max(ctx.max_xregs, num + 1)
  elif typ == 'y':
    ctx.max_yregs = max(ctx.max_yregs, num + 1)
  elif typ == 'fr':
    ctx.max_fregs = max(ctx.max_fregs, num + 1)
  else:
    assert False

  return f'(local.get $var_{typ}reg_{num}_val)\n'

def move(ctx, styp, snum, dtyp, dnum):
  b = ';; move\n'
  b += push(ctx, styp, snum)
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
    (atom_name, atom_id) = add_atom(ctx, str(val))
    b += f'''
      (i32.shl
        (global.get $__unique_atom__{str(atom_name)}) ;; atom {val}\n
        (i32.const 6)
      )
      (i32.or (i32.const 0xB))
    '''
  elif typ == 'literal' or typ == 'string':
    (_offset, literal_name) = add_literal(ctx, val)
    b += f'(global.get ${literal_name})\n'
  elif typ == 'x' or typ == 'y' or typ == 'fr':
    b += push(ctx, typ, int(val))
  else:
    assert False, 'not implemented {typ}'.format(typ=typ)

  return b

def populate_with(ctx, dtyp, dnum, value):
  b = populate_stack_with(ctx, value)
  b += pop(ctx, dtyp, dnum)
  return b

def arg(value):
  [typ, [num]] = value
  typ = str(typ)
  assert typ in ('x', 'y'), f'Wrong type {typ}'
  return typ, int(num)

def add_atoms_table_literal(ctx):
  table_list = [0] * (len(ctx.atoms) + 1)
  table_binary = bytearray(len(table_list) * 4)
  for (atom_id, offset) in ctx.atoms.values():
    table_list[atom_id] = offset

  for idx, offset in enumerate(table_list):
    struct.pack_into('<I', table_binary, idx * 4, offset)

  add_named_literal(ctx, bytes(table_binary), 'unique_table_of_atoms')

def write_atoms(ctx):
  b = ';; atoms table\n'
  for (key, (atom_id, offset)) in ctx.atoms.items():
    b += GLOBAL_CONST.format(name=f'__unique_atom__{key}', value=atom_id, hvalue=hex(atom_id))

  return b


def write_exception_handlers(ctx, mod_name, func_name):
  add_import(ctx, 'minibeam', 'add_trace', 3)

  return f'''
    (if
     (i32.load (global.get $__unique_exception__literal_ptr_raw))
     (then
       (global.get $__unique_atom__{mod_name})
       (global.get $__unique_atom__{func_name})
       (local.get $line)
       (call $minibeam_add_trace_3) (drop)

       (if (local.get $exception_h)
         (then
          (local.set $jump (local.get $exception_h))
         )
         (else (return (i32.const 0xFF_FF_FF_00)))
       )
     )
    )
    '''

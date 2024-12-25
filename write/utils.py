import struct
from erparse import Atom, Fun
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
    mod=sanitize_atom(ext_mod),
    fn=sanitize_atom(ext_fn),
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
    value = ['integer', value]
  if isinstance(value, Atom):
    value = ['atom', value]

  if value[0] == 'tr':
    value = value[1]

  if value[0] == 'reg':
    value = value[1:]

  [typ, val] = value
  b = ''
  if typ == 'integer':
    pval = pack_reg_value(ctx, int(val))
    b += f'(i32.const {pval})\n'
  elif typ == 'atom':
    # print('v', val)
    (atom_name, atom_id) = add_atom(ctx, str(val))
    b += f'''
      (i32.shl
        (global.get $__unique_atom__{str(sanitize_atom(atom_name))}) ;; atom {val}\n
        (i32.const 6)
      )
      (i32.or (i32.const 0xB))
    '''
  elif typ == 'literal' or typ == 'string' or typ == 'fun':
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
  assert len(value) == 3
  [_reg, typ, num] = value
  assert _reg == 'reg'
  typ = str(typ)
  assert typ in ('x', 'y', 'fr'), f'Wrong type {typ}'
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
    b += GLOBAL_CONST.format(name=f'__unique_atom__{sanitize_atom(key)}', value=atom_id, hvalue=hex(atom_id))

  return b


def write_exception_handlers(ctx, mod_name, func_name):
  add_import(ctx, 'minibeam', 'add_trace', 3)

  return f'''
    (if
     (i32.load (global.get $__unique_exception__literal_ptr_raw))
     (then
       (global.get $__unique_atom__{sanitize_atom(mod_name)})
       (global.get $__unique_atom__{sanitize_atom(func_name)})
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

def sanitize_atom(name):

  name = name.replace('upper__', 'upper__beam__'
    ).replace('-', '__beam_min__'
    ).replace('/', '__beam_slash__'
    ).replace('.', '__')

  if name[0].isupper():
    name = 'upper__' + name[0].lower() + name[1:]

  return name


def add_trampoline(ctx, scope, arity):
  args_in = ''
  for arg_x in range(0, arity):
    args_in += f'(param $in_{arg_x} i32) '

  args_out = ''
  for arg_x in range(0, arity):
    args_out += f'(local.get $in_{arg_x}) '

  calls = ''
  for (fscope, target, bound_count) in ctx.bound_functions:
    if scope != fscope:
      continue

    func = ctx.find_function(target)

    if func.arity != (arity + bound_count):
      continue

    bound_args_out = ''
    for b_arg in range(0, bound_count):
      offset = (b_arg * 4) + 8
      bound_args_out += f'(i32.load (i32.add (local.get $ctx) (i32.const {offset})))\n'

    calls += f'''
      (if
        ;; check if {func.name}/{func.arity} matches
        (i32.and
          (i32.eq (i32.const {target}) (local.get $target))
          (i32.eq (i32.const {bound_count}) (local.get $bound_count))
        )
        (then
          { args_out }
          { bound_args_out }
          (call ${sanitize_atom(func.name)}_{func.arity})
          (return)
        )
      )
    '''

    print ('generate arity', arity, 'trampoline for', target, 'with', bound_count, 'bound variables')
    print ('func', func, func.arity)


  return f'''
    (func $__module_trampoline_{arity} (param $ctx i32) { args_in } (result i32)
      (local $target i32)
      (local $bound_count i32)

      (i32.load (local.get $ctx))
      (i32.const 6)
      (i32.shr_u)
      (local.set $target)

      (i32.load (i32.add (local.get $ctx) (i32.const 4)))
      (local.set $bound_count)

      { calls }
      (unreachable)
    )
  '''


def add_dispatch(ctx, arity):
  args_in = ''
  for arg_x in range(0, arity):
    args_in += f'(param $__unique_in_{arg_x} i32) '

  args_out = ''
  for arg_x in range(0, arity):
    args_out += f'(local.get $__unique_in_{arg_x}) '

  (atom_name, _atom_id, offset) = ctx.resolve_atom(ctx.mod_name)

  atom_value = populate_stack_with(ctx, ['atom', str(ctx.mod_name)])
  calls = ''
  for (fscope, target, bound_count) in ctx.bound_functions:
    if 'global' != fscope:
      continue

    func = ctx.find_function(target)

    if func.arity != (arity + bound_count):
      continue

    fn_atom_value = populate_stack_with(ctx, ['atom', str(func.name)])

    calls += f'''
      (if
        ;; check if {func.name}/{func.arity} matches
        (i32.eq {fn_atom_value} (local.get $target_fun))
        (then
          { args_out }
          (call ${sanitize_atom(func.name)}_{func.arity})
          (return)
        )
      )
    '''



  return f'''
    (func $__unique__global_dispatch_{arity} (param $__unique_ctx i32) {args_in} (result i32)
      (local $__unique_target_mod i32)
      (i32.load (i32.add (local.get $__unique_ctx) (i32.const 4)))
      (local.set $__unique_target_mod)

      (if (i32.eq (local.get $__unique_target_mod) {atom_value})
          (then
            (local.get $__unique_ctx)
            { args_out }
            (return (call $__export_trampoline_{arity}))
          )
      )
      (unreachable)
    )

    (func $__export_trampoline_{arity} (param $ctx i32) {args_in} (result i32)
      (local $target_fun i32)
      (i32.load (i32.add (local.get $ctx) (i32.const 8)))
      (local.set $target_fun)

      { calls }

      (unreachable)
    )
  '''

def write_trampolines(ctx):
  if not ctx.trampolines:
    return ''

  ret = ';; let there be trampolines\n'
  for (scope, arity) in ctx.trampolines:
    if scope == 'module':
      ret += add_trampoline(ctx, scope, arity)
    elif scope == 'global':
      ret += add_dispatch(ctx, arity)

  return ret

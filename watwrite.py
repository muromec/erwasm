from codecs import decode
MODULE = '''(module
   ;; module name: {name}
   {imports}
   (memory 1)
   (export "memory" (memory 0))
   ;; data section
   {data}
   ;; module body
   {body}
)'''

FUNC = '''
(func ${name}_{arity} {params} {result}
{localvars}
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
MEM_NEXT_FREE = '''
  ;; next free memory offset
  (data (i32.const {offset0}) "{offset}")
'''

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

def fix_string(value):
  value = decode(value, 'unicode-escape')
  ret = ''
  for symbol in value:
    s = pad(hex(ord(symbol))[2:])
    ret += f'\\{s}'

  return ret

def pack_literal(value, push):
  if isinstance(value, str):
    return (fix_string(value), 10)

  if isinstance(value, int):
    return (make_len(value), 0)

  if isinstance(value, list) or isinstance(value, typle):
    n_items = len(value)
    ret = [
      push(element)
      for element in value
    ] + [[0, 0]]
    packed_ret = [
      make_len(off) +
      make_len(typ) +
      make_len((n_items - 1 - idx) * 3)
      for idx, (off, typ) in enumerate(ret)
    ]
    buffer = "".join(packed_ret)
    return (buffer, 20)

  assert False, f'cant pack as constant value {value}'

def produce_wasm(module):
  body = ''
  data = ''
  imports = []

  def add_import(ext_mod, ext_fn, ext_fn_arity):
    import_line = FUNC_IMPORT.format(
      mod=ext_mod, fn=ext_fn,
      arity=int(ext_fn_arity),
      params = make_params_n(int(ext_fn_arity) * 2),
    )
    if import_line not in imports:
      imports.append(import_line)

  def add_literal(sval):
    nonlocal data
    nonlocal literalidx
    (packed_value, packed_value_type) = pack_literal(sval, add_literal)
    mem_offset = literalidx
    data += LITERAL.format(
      offset0 = literalidx,
      offset1 = literalidx + 4,
      llen = make_len(len(packed_value)),
      lval = packed_value,
    )
    literalidx += 4
    literalidx += len(packed_value)
    return (mem_offset, packed_value_type)

  literalidx = 4
  for func in module.functions:
    max_xregs = max(int(func.arity), 1)
    max_yregs = 0
    if (func.name, func.arity) in module.export_funcs:
      body += FUNC_EXPORT.format(name=func.name, arity=func.arity)

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

    b += f';; arity {func.arity}, input put into X registers\n'

    def push(typ, num, part):
      nonlocal b
      assert part in ['val', 'tag']
      assert typ in ['x', 'y']
      if typ == 'x':
        assert num <= max_xregs
      if typ == 'y':
        assert num <= max_yregs

      b += f'local.get $var_{typ}reg_{num}_{part}\n'

    def pop(typ, num, part):
      nonlocal b
      nonlocal max_xregs
      nonlocal max_yregs

      assert part in ['val', 'tag']
      assert typ in ['x', 'y']

      if typ == 'x':
        max_xregs = max(max_xregs, num + 1)
      if typ == 'y':
        max_yregs = max(max_yregs, num, + 1)

      b += f'local.set $var_{typ}reg_{num}_{part}\n'

    def load_if_int(dtyp, dnum):
      nonlocal b
      push(dtyp, dnum, 'tag')
      b += f'''
      (if
         (then nop)
         (else
          local.get $var_{dtyp}reg_{dnum}_val
          i32.const 4
          i32.add
          i32.load
          local.set $var_{dtyp}reg_{dnum}_val
         )
      )
      '''

    def set_typ_reg(typ, num, tag):
      nonlocal b
      b += f'(local.set $var_{typ}reg_{num}_tag (i32.const {tag}))\n'

    def set_val_reg(typ, num, val):
      nonlocal b
      b += f'(local.set $var_{typ}reg_{num}_val (i32.const {val}))\n'

    def set_const(typ, num, val, tag):
      set_typ_reg(typ, num, tag)
      set_val_reg(typ, num, val)

    def move(styp, snum, dtyp, dnum):
      nonlocal b
      b += f';; move {styp}{snum} -> {dtyp}{dnum} \n'
      push(styp, snum, 'tag')
      pop(dtyp, dnum, 'tag')
      push(styp, snum, 'val')
      pop(dtyp, dnum, 'val')

    def push_return():
      nonlocal b
      b += ';; push X0 to stack\n'

      # Beam uses X0 as function result.
      # Put return registers to stack.
      push('x', 0, 'tag')
      push('x', 0, 'val')
      b += 'return\n'


    def populate_with(dtyp, reg_n, value):
      [typ, [val]] = value
      if typ == 'integer':
        set_const(dtyp, reg_n, val, 0)
      elif typ == 'literal':
        (mem_offset, literal_typ) = add_literal(val)
        set_const(dtyp, reg_n, mem_offset, literal_typ)
      elif typ == 'atom':
        set_const(dtyp, reg_n, 0, 20) # TODO: implement atoms
      elif typ == 'x' or typ == 'y':
        val = int(val)
        move(typ, val, dtyp, reg_n)
      else:
        assert False, 'not implemented {typ}'.format(typ=typ)

    def populate_stack_with(value):
      if value[0] == 'tr':
        value = value[1][0]
      [typ, [val]] = value
      nonlocal b
      if typ == 'integer':
        b += f'(i32.const {val})\n'
      elif typ == 'literal':
        (mem_offset, literal_typ) = add_literal(val)
        b += f'(i32.const {mem_offset})\n'
      elif typ == 'atom':
        b += f'(i32.const 0)\n' # TODO: implement atoms
      elif typ == 'x' or typ == 'y':
        push(typ, int(val), 'val')
      else:
        assert False, 'not implemented {typ}'.format(typ=typ)

    depth = 0
    labels = list([
      statement[1][0]
      for statement in func.statements
      if statement[0] == 'label'
    ])

    labels.pop(0)
    while labels:
      label = labels.pop()
      b += f'(block $label_{label} \n'

    for statement in func.statements:
      styp = statement[0]
      sbody = statement[1]
      if styp == 'return':
        push_return()

      if styp == 'allocate':
        [yreg, xreg] = sbody
        max_yregs = max(max_yregs, int(yreg))
        max_xregs = max(max_xregs, int(xreg))

      if styp == 'trim':
        [nremove, nleft] = sbody
        nremove = int(nremove)
        nleft = int(nleft)
        for yreg in range(0, nleft):
          move('y', yreg + nremove, 'y', yreg)

      if styp == 'move':
        [source, (dtyp, [dval])] = sbody
        dval = int(dval)
        populate_with(dtyp, dval, source)

      if styp == 'label':
        b += f';; label {sbody[0]}, deep {depth}\n'
        if depth > 0:
          b += f') ;; end of depth {depth}\n'

        depth += 1

      if styp == 'test':
        [op, (_f, [jump]), args] = sbody
        for arg in args:
          populate_stack_with(arg)

        b += f' ;; test and jump to {jump}\n'
        b += {
          'is_lt': 'i32.lt_u\n',
          'is_le': 'i32.le_u\n',
          'is_gt': 'i32.gt_u\n',
          'is_ge': 'i32.ge_u\n',
          'is_nonempty_list': 'i32.load\n'
        }[op]

        b += '(i32.const 0)\n'
        b += '(i32.eq)\n'
        b += f'(br_if $label_{jump})\n'

      if styp == 'call_ext':
        [ext_mod, ext_fn, ext_fn_arity] = statement[1][1][1]
        add_import(ext_mod, ext_fn, ext_fn_arity)
        max_xregs = max(max_xregs, int(ext_fn_arity))

        for xreg in range(0, int(ext_fn_arity)):
          push('x', xreg, 'tag')
          push('x', xreg, 'val')

        b += f'call ${ext_mod}_{ext_fn}_{ext_fn_arity}\n'
        pop('x', 0, 'val')
        pop('x', 0, 'tag')

      if styp == 'call_ext_only':
        [ext_mod, ext_fn, ext_fn_arity] = statement[1][1][1]
        add_import(ext_mod, ext_fn, ext_fn_arity)
        max_xregs = max(max_xregs, int(ext_fn_arity))

        for xreg in range(0, int(ext_fn_arity)):
          push('x', xreg, 'tag')
          push('x', xreg, 'val')

        b += f'call ${ext_mod}_{ext_fn}_{ext_fn_arity}\n'
        b += 'return';

      if styp == 'call_ext_last':
        [_arity, (_e, [ext_mod, ext_fn, ext_fn_arity]), _regs] = sbody
        add_import(ext_mod, ext_fn, ext_fn_arity)
        max_xregs = max(max_xregs, int(ext_fn_arity))

        for xreg in range(0, int(ext_fn_arity)):
          push('x', xreg, 'tag')
          push('x', xreg, 'val')

        b += f'call ${ext_mod}_{ext_fn}_{ext_fn_arity}\n'
        b += 'return';

      if styp == 'call_only':
        [arity, (_f, [findex])] = sbody
        arity = int(arity)
        max_xregs = max(max_xregs, arity)
        findex = int(findex)
        into_func = module.find_function(findex)

        for xreg in range(0, arity):
          push('x', xreg, 'tag')
          push('x', xreg, 'val')

        b += f'call ${into_func.name}_{into_func.arity}\n'
        b += 'return';

      if styp == 'call':
        [arity, (_f, [findex])] = sbody
        arity = int(arity)
        max_xregs = max(max_xregs, arity)
        findex = int(findex)
        into_func = module.find_function(findex)

        for xreg in range(0, arity):
          push('x', xreg, 'tag')
          push('x', xreg, 'val')

        b += f'call ${into_func.name}_{into_func.arity}\n'
        pop('x', 0, 'val')
        pop('x', 0, 'tag')

      if styp == 'call_last':
        [arity, (_f, [findex]), regs] = sbody
        arity = int(arity)
        max_xregs = max(max_xregs, arity)
        findex = int(findex)
        into_func = module.find_function(findex)

        for xreg in range(0, arity):
          push('x', xreg, 'tag')
          push('x', xreg, 'val')

        b += f'call ${into_func.name}_{into_func.arity}\n'
        b += 'return';

      if styp == 'gc_bif':
        [op, _fall, arity, [arg0, arg1], ret] = sbody
        (retT, [retV]) = ret

        populate_stack_with(arg0)
        populate_stack_with(arg1)

        if op == "'+'":
          b += 'i32.add\n'

        if retT == 'x' or retT == 'y':
          pop(retT, int(retV), 'val')
          set_typ_reg(retT, retV, 0)

      if styp == 'get_hd':
        b += ';; get_hd\n'

        [sarg, darg] = sbody
        [styp, [snum]] = sarg
        snum = int(snum)
        [dtyp, [dnum]] = darg
        dnum = int(dnum)

        # set_val_reg(dtyp, dnum, 3)
        push(styp, snum, 'val')
        push(styp, snum, 'val')
        b += 'i32.const 4\n'
        b += 'i32.add\n'
        b += 'i32.load\n'
        pop(dtyp, dnum, 'val')

        b += 'i32.const 8\n'
        b += 'i32.add\n'
        b += 'i32.load\n'
        pop(dtyp, dnum, 'tag')
        load_if_int(dtyp, dnum)

      if styp == 'get_tl':
        b += ';; get_tl\n'
        [sarg, darg] = sbody
        [styp, [snum]] = sarg
        snum = int(snum)
        [dtyp, [dnum]] = darg
        dnum = int(dnum)

        push(styp, snum, 'val')
        b += 'i32.const 12\n'
        b += 'i32.add\n'
        pop(dtyp, dnum, 'val')
        set_typ_reg(dtyp, dnum, 20)

      # print('s', styp)

    assert stack == 0

    localvars = '\n'
    for xreg in range(0, max_xregs):
      localvars += f'(local $var_xreg_{xreg}_tag i32)\n'
      localvars += f'(local $var_xreg_{xreg}_val i32)\n'

    for yreg in range(0, max_yregs):
      localvars += f'(local $var_yreg_{yreg}_tag i32)\n'
      localvars += f'(local $var_yreg_{yreg}_val i32)\n'

    body += FUNC.format(
      name=func.name,
      arity=func.arity,
      start_label=func.start_label,
      params=make_in_params_n(int(func.arity) * 2),
      result=make_result_n(2),
      localvars=localvars,
      body=b,
    )
  data = MEM_NEXT_FREE.format(
    offset0=0,
    offset=make_len(literalidx),
  ) + data
  return MODULE.format(
    name=module.name,
    imports="\n".join(imports),
    data=data,
    body=body
  )

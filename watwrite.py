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
(export "{mod}#{name}-a{arity}" (func ${name}_{arity}))
'''

FUNC_IMPORT = '''
(import "{mod}" "{fn}" (func ${mod}_{fn}_{arity} {params} (result i32)))
'''

LITERAL = '''
  (data (i32.const {offset}) "{value}")
'''
GLOBAL_CONST = '''
  (global ${name} i32 (i32.const {value}))
'''
MEM_NEXT_FREE = '''
  ;; next free memory offset
  (global $__free_mem i32 (i32.const {offset}))
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
  return  decode(value, 'unicode-escape')

def pack_literal(value, push):
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

def produce_wasm(module):
  body = ''
  data = ''
  imports = []

  def ignore_call(ext_mod, ext_fn):
    if ext_mod == 'erlang' and ext_fn == 'get_module_info':
      return True

  def add_import(ext_mod, ext_fn, ext_fn_arity):
    import_line = FUNC_IMPORT.format(
      mod=ext_mod, fn=ext_fn,
      arity=int(ext_fn_arity),
      params = make_params_n(int(ext_fn_arity)),
    )
    if import_line not in imports:
      imports.append(import_line)

  def add_literal(sval):
    nonlocal data
    nonlocal literalidx
    packed_value = pack_literal(sval, add_literal)
    data += LITERAL.format(
      offset = literalidx,
      value = packed_value,
    )
    name = f'__{literalidx}__literal_ptr_raw'
    data += GLOBAL_CONST.format(
      name = name,
      value = literalidx,
    )
    name = f'__{literalidx}__literal_ptr_e'
    data += GLOBAL_CONST.format(
      name = name,
      value = (literalidx << 2) | 2,
    )

    ret = literalidx + 0
    literalidx += len(packed_value)
    return name

  literalidx = 4
  for func in module.functions:
    max_xregs = max(int(func.arity), 1)
    max_yregs = 0
    if (func.name, func.arity) in module.export_funcs:
      body += FUNC_EXPORT.format(name=func.name, arity=func.arity, mod=module.name)

    b = '\n'

    stack = 0
    arg = int(func.arity)
    while arg > 0:
      b += f'local.get $in_{arg - 1}\n'
      b += f'local.set $var_xreg_{arg - 1}_val\n'
      arg -= 1

    b += f';; arity {func.arity}, input put into X registers\n'

    def push(typ, num, part):
      nonlocal b
      assert part == 'val'
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

      assert part == 'val'
      assert typ in ['x', 'y']

      if typ == 'x':
        max_xregs = max(max_xregs, num + 1)
      if typ == 'y':
        max_yregs = max(max_yregs, num, + 1)

      b += f'local.set $var_{typ}reg_{num}_{part}\n'

    def load_if_int(dtyp, dnum):
      nonlocal b
      # push(dtyp, dnum, 'tag')
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

    def set_val_reg(typ, num, val):
      nonlocal b
      b += f'(local.set $var_{typ}reg_{num}_val (i32.const {val}))\n'

    def set_val_mem_offset(typ, num, name):
      nonlocal b
      b += f'(local.set $var_{typ}reg_{num}_val (global.get ${name}))'

    def set_const(typ, num, val):
      #set_typ_reg(typ, num, tag)
      set_val_reg(typ, num, val)

    def move(styp, snum, dtyp, dnum):
      nonlocal b
      b += f';; move {styp}{snum} -> {dtyp}{dnum} \n'
      # push(styp, snum, 'tag')
      # pop(dtyp, dnum, 'tag')
      push(styp, snum, 'val')
      pop(dtyp, dnum, 'val')

    def push_return():
      nonlocal b
      b += ';; push X0 to stack\n'

      # Beam uses X0 as function result.
      # Put return registers to stack.
      # push('x', 0, 'tag')
      push('x', 0, 'val')
      b += 'return\n'


    def populate_with(dtyp, reg_n, value):
      [typ, rval] = value
      val = rval[0]
      if typ == 'integer':
        set_const(dtyp, reg_n, (int(val) << 4) | 0xF)
      elif typ == 'literal':
        literal_name = add_literal(rval[0])
        set_val_mem_offset(dtyp, reg_n, literal_name)
      elif typ == 'atom':
        # set_const(dtyp, reg_n, 0, 20) # TODO: implement atoms
        pass
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
        val = (int(val) << 4 | 0xF)
        b += f'(i32.const {val})\n'
      elif typ == 'literal':
        literal_name = add_literal(val)
        b += f'(i32.const {mem_offset})\n'
        assert False
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
    labels_to_idx = labels[:]
    jump_depth = labels_to_idx.index(str(func.start_label))

    b += f'(local.set $jump (i32.const {jump_depth}))\n'
    labels0 = list(map(str,range(0, len(labels))))
    labels0 = " ".join(labels0[:])
    b += f'(loop $start\n'
    while labels:
      label = labels.pop()
      b += f'(block $label_{label} \n'

    b += f'(br_table  {labels0} (local.get $jump))\n'
    b += f'unreachable\n'

    current_label = None
    for statement in func.statements:
      styp = statement[0]
      sbody = statement[1]
      if styp == 'return':
        push_return()

      if styp == 'func_info':
        b += 'unreachable ;; func info trap\n'

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
          'is_nonempty_list': f'''
            ;; test that the list it not empty
            (local.set $temp)

            (local.get $temp)
            (i32.and (i32.const 3))
            (if
              (i32.eq (i32.const 2)) ;; mem ref
              (then
                (local.get $temp)
                (i32.shr_u (i32.const 2))
                (i32.load)
                (i32.and (i32.const 3))
                (i32.eq (i32.const 1))
                (local.set $temp)
              )
              (else
                (i32.const 0)
                (local.set $temp)
              )
            )
            (local.get $temp)
          '''
        }[op]

        b += '(i32.eqz)\n'
        jump_depth = labels_to_idx.index(jump)
        b += f'(local.set $jump (i32.const {jump_depth}))\n'
        b += f'(br_if $start)\n'

      if styp == 'call_ext':
        [ext_mod, ext_fn, ext_fn_arity] = statement[1][1][1]
        add_import(ext_mod, ext_fn, ext_fn_arity)
        max_xregs = max(max_xregs, int(ext_fn_arity))

        for xreg in range(0, int(ext_fn_arity)):
          # push('x', xreg, 'tag')
          push('x', xreg, 'val')

        b += f'call ${ext_mod}_{ext_fn}_{ext_fn_arity}\n'
        pop('x', 0, 'val')
        # pop('x', 0, 'tag')

      if styp == 'call_ext_only':
        [ext_mod, ext_fn, ext_fn_arity] = statement[1][1][1]
        if ignore_call(ext_mod, ext_fn):
          continue
        add_import(ext_mod, ext_fn, ext_fn_arity)
        max_xregs = max(max_xregs, int(ext_fn_arity))

        for xreg in range(0, int(ext_fn_arity)):
          # push('x', xreg, 'tag')
          push('x', xreg, 'val')

        b += f'call ${ext_mod}_{ext_fn}_{ext_fn_arity}\n'
        b += 'return';

      if styp == 'call_ext_last':
        [_arity, (_e, [ext_mod, ext_fn, ext_fn_arity]), _regs] = sbody
        add_import(ext_mod, ext_fn, ext_fn_arity)
        max_xregs = max(max_xregs, int(ext_fn_arity))

        for xreg in range(0, int(ext_fn_arity)):
          # push('x', xreg, 'tag')
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
          # push('x', xreg, 'tag')
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
          # push('x', xreg, 'tag')
          push('x', xreg, 'val')

        b += f'call ${into_func.name}_{into_func.arity}\n'
        pop('x', 0, 'val')
        # pop('x', 0, 'tag')

      if styp == 'call_last':
        [arity, (_f, [findex]), regs] = sbody
        arity = int(arity)
        max_xregs = max(max_xregs, arity)
        findex = int(findex)
        into_func = module.find_function(findex)

        for xreg in range(0, arity):
          # push('x', xreg, 'tag')
          push('x', xreg, 'val')

        b += f'call ${into_func.name}_{into_func.arity}\n'
        b += 'return';

      if styp == 'gc_bif':
        [op, _fall, arity, [arg0, arg1], ret] = sbody
        (retT, [retV]) = ret

        populate_stack_with(arg0)
        populate_stack_with(arg1)

        if op == "'+'":
          b += '(i32.xor (i32.const 0xF))\n'
          b += 'i32.add\n'

        if retT == 'x' or retT == 'y':
          pop(retT, int(retV), 'val')

      if styp == 'get_hd':
        b += '(block ;; get_hd\n'
        b += ';; get_hd\n'

        [sarg, darg] = sbody
        [styp, [snum]] = sarg
        snum = int(snum)
        [dtyp, [dnum]] = darg
        dnum = int(dnum)

        b += f'''
        (local.get $var_{styp}reg_{snum}_val)
        (i32.and (i32.const 3))
        (if
          (i32.eq (i32.const 2)) ;; mem ref
          (then
            (local.get $var_{styp}reg_{snum}_val)
            (i32.shr_u (i32.const 2))
            (local.set $temp) ;; this hold reference of list head
            (i32.load (local.get $temp))
            (i32.and (i32.const 3))
            (if (i32.eq (i32.const 1))
              (then
                (i32.load (i32.add (i32.const 4) (local.get $temp)))
                (local.set $var_{dtyp}reg_{dnum}_val)
              )
              (else
                (unreachable)
              )
            )
          )
          (else
            (unreachable)
          )
        )
        \n'''

        b += ') ;; end get_hd\n'

      if styp == 'get_tl':
        b += '(block ;; get_tl\n'
        b += ';; get_tl\n'
        #print('s', styp, sbody)

        [sarg, darg] = sbody
        [styp, [snum]] = sarg
        snum = int(snum)
        [dtyp, [dnum]] = darg
        dnum = int(dnum)

        b += f'''
        (local.get $var_{styp}reg_{snum}_val)
        (i32.and (i32.const 3))
        (if
          (i32.eq (i32.const 2)) ;; mem ref
          (then
            (local.get $var_{styp}reg_{snum}_val)
            (i32.shr_u (i32.const 2))
            (local.set $temp) ;; this hold reference of list head
            (i32.load (local.get $temp))
            (if
              (i32.eq (i32.const 0x3b))
              (then
                (local.set $var_{dtyp}reg_{dnum}_val (i32.const 0))
                (br 0)
              )
            )
            (i32.load (local.get $temp))
            (i32.and (i32.const 3))
            (if (i32.eq (i32.const 1))
              (then
                (i32.add
                  (i32.shr_u
                    (i32.load (local.get $temp))
                    (i32.const 2)
                  )
                  (local.get $temp)
                )
                (i32.const 2)
                (i32.shl)
                (i32.or (i32.const 2))
                (local.set $var_{dtyp}reg_{dnum}_val)
              )
              (else
                (unreachable)
              )
            )
          )
          (else
            (unreachable)
          )
        )
        \n'''

        b += ') ;; $2 end get_tl\n'

      # print('s', styp)

    b += ') ;; end of loop\n'
    b += 'unreachable\n';
    assert stack == 0

    localvars = '\n'
    for xreg in range(0, max_xregs):
      localvars += f'(local $var_xreg_{xreg}_val i32)\n'

    for yreg in range(0, max_yregs):
      localvars += f'(local $var_yreg_{yreg}_val i32)\n'

    localvars += f'(local $temp i32)\n'
    localvars += f'(local $jump i32)\n'

    body += FUNC.format(
      name=func.name,
      arity=func.arity,
      start_label=func.start_label,
      params=make_in_params_n(int(func.arity)),
      result=make_result_n(1),
      localvars=localvars,
      body=b,
    )
  data = MEM_NEXT_FREE.format(
    offset=literalidx,
  ) + data
  return MODULE.format(
    name=module.name,
    imports="\n".join(imports),
    data=data,
    body=body
  )

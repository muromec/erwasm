from codecs import decode

from write.line import Line
from write.jump import Jump
from write.move import Move
from write.test import Test
from write.ret import Ret

from write.utils import (
  add_import, populate_stack_with, make_result_n, make_in_params_n,
  pop as _pop, push as _push, move as _move,
)


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

def produce_wasm(module):
  body = ''

  def ignore_call(ext_mod, ext_fn):
    if ext_mod == 'erlang' and ext_fn == 'get_module_info':
      return True

  class Ctx:
    labels_to_idx = []
    imports = []
    data = ''
    literalidx = 4

    max_xregs = 1
    max_yregs = 0

  for func in module.functions:
    Ctx.max_xregs = max(int(func.arity), 1)
    Ctx.max_yregs = 0
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
      b += _push(Ctx, typ, num)

    def pop(typ, num, part):
      nonlocal b
      b += _pop(Ctx, typ, num)

    def set_val_reg(typ, num, val):
      nonlocal b
      b += f'(local.set $var_{typ}reg_{num}_val (i32.const {val}))\n'

    def move(styp, snum, dtyp, dnum):
      nonlocal b
      _move(Ctx, styp, snum, dtyp, dnum)

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
    assert func.statements[0][0] == 'function'

    Ctx.labels_to_idx = labels_to_idx

    for statement in func.statements[1:]:
      styp = statement[0]
      sbody = statement[1]
      
      op_cls = {
        'line': Line,
        'jump': Jump,
        'move': Move,
        'test': Test,
        'return': Ret,
      }.get(styp)
      op_imp = op_cls(*sbody) if op_cls else None

      if op_imp:
        b += op_imp.to_wat(Ctx)

      elif styp == "'%'":
        pass

      elif styp == 'func_info':
        b += 'unreachable ;; func info trap\n'

      elif styp == 'allocate':
        [yreg, xreg] = sbody
        Ctx.max_yregs = max(Ctx.max_yregs, int(yreg))
        Ctx.max_xregs = max(Ctx.max_xregs, int(xreg))

      elif styp == 'trim':
        [nremove, nleft] = sbody
        nremove = int(nremove)
        nleft = int(nleft)
        for yreg in range(0, nleft):
          move('y', yreg + nremove, 'y', yreg)

      elif styp == 'label':
        b += f';; label {sbody[0]}, deep {depth}\n'
        b += f') ;; end of depth {depth}\n'

        depth += 1

      elif styp == 'call_ext':
        [ext_mod, ext_fn, ext_fn_arity] = statement[1][1][1]
        add_import(Ctx, ext_mod, ext_fn, ext_fn_arity)
        Ctx.max_xregs = max(Ctx.max_xregs, int(ext_fn_arity))

        for xreg in range(0, int(ext_fn_arity)):
          # push('x', xreg, 'tag')
          push('x', xreg, 'val')

        b += f'call ${ext_mod}_{ext_fn}_{ext_fn_arity}\n'
        pop('x', 0, 'val')
        # pop('x', 0, 'tag')

      elif styp == 'call_ext_only':
        [ext_mod, ext_fn, ext_fn_arity] = statement[1][1][1]
        Ctx.max_xregs = max(Ctx.max_xregs, int(ext_fn_arity))

        if ignore_call(ext_mod, ext_fn):
          continue
        add_import(Ctx, ext_mod, ext_fn, ext_fn_arity)

        for xreg in range(0, int(ext_fn_arity)):
          # push('x', xreg, 'tag')
          push('x', xreg, 'val')

        b += f'call ${ext_mod}_{ext_fn}_{ext_fn_arity}\n'
        b += 'return\n';

      elif styp == 'call_ext_last':
        [_arity, (_e, [ext_mod, ext_fn, ext_fn_arity]), _regs] = sbody
        add_import(Ctx, ext_mod, ext_fn, ext_fn_arity)
        Ctx.max_xregs = max(Ctx.max_xregs, int(ext_fn_arity))

        for xreg in range(0, int(ext_fn_arity)):
          # push('x', xreg, 'tag')
          push('x', xreg, 'val')

        b += f'call ${ext_mod}_{ext_fn}_{ext_fn_arity}\n'
        b += 'return\n';

      elif styp == 'call_only':
        [arity, (_f, [findex])] = sbody
        arity = int(arity)
        Ctx.max_xregs = max(Ctx.max_xregs, int(arity))
        findex = int(findex)
        into_func = module.find_function(findex)

        for xreg in range(0, arity):
          # push('x', xreg, 'tag')
          push('x', xreg, 'val')

        b += f'call ${into_func.name}_{into_func.arity}\n'
        b += 'return\n';

      elif styp == 'badmatch':
        b += '(unreachable) ;; badmatch\n'

      elif styp == 'call':
        [arity, (_f, [findex])] = sbody
        arity = int(arity)
        Ctx.max_xregs = max(Ctx.max_xregs, int(arity))
        findex = int(findex)
        into_func = module.find_function(findex)

        for xreg in range(0, arity):
          # push('x', xreg, 'tag')
          push('x', xreg, 'val')

        b += f'call ${into_func.name}_{into_func.arity}\n'
        pop('x', 0, 'val')
        # pop('x', 0, 'tag')

      elif styp == 'call_last':
        [arity, (_f, [findex]), regs] = sbody
        arity = int(arity)
        Ctx.max_xregs = max(Ctx.max_xregs, int(arity))
        findex = int(findex)
        into_func = module.find_function(findex)

        for xreg in range(0, arity):
          # push('x', xreg, 'tag')
          push('x', xreg, 'val')

        b += f'call ${into_func.name}_{into_func.arity}\n'
        b += 'return\n';

      elif styp == 'gc_bif':
        [op, _fall, arity, [arg0, arg1], ret] = sbody
        (retT, [retV]) = ret

        b += populate_stack_with(Ctx, arg0)
        b += populate_stack_with(Ctx, arg1)

        if op == "'+'":
          b += '(i32.xor (i32.const 0xF))\n'
          b += 'i32.add\n'
        elif op ==  "'-'":
          b += '(i32.xor (i32.const 0xF))\n'
          b += 'i32.sub\n'
        elif op == "'*'":
          b += '''
          (local.set $temp (i32.shr_u))
          (i32.mul (i32.shr_u) (local.get $temp))
          '''

        else:
          assert False, f'unknown bif {op}'

        if retT == 'x' or retT == 'y':
          pop(retT, int(retV), 'val')

      elif styp == 'get_list':
        b += '(block ;; get_list\n'

        [sarg, darg_h, darg_t] = sbody
        [styp, [snum]] = sarg
        snum = int(snum)
        [dtyp_h, [dnum_h]] = darg_h
        [dtyp_t, [dnum_t]] = darg_t
        dnum_h = int(dnum_h)
        dnum_t = int(dnum_t)

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
                (local.set $var_{dtyp}reg_{dnum_h}_val) ;; head

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
                (local.set $var_{dtyp}reg_{dnum_t}_val) ;; tail
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

        b += ') ;; end get_listn\n'

      elif styp == 'get_hd':
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

      elif styp == 'get_tl':
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

      elif styp == 'select_val':
        b += ';; select_val\n'

        [sarg, [_f, [def_jump]], [_l, [comp_table]]] = sbody
        b += populate_stack_with(Ctx, sarg)

        b += '(local.set $temp)\n'

        b += f';; default target is {def_jump} \n'
        while comp_table:
          value = comp_table.pop(0)
          [_f, [jump]] = comp_table.pop(0)

          jump_depth = labels_to_idx.index(jump)
          b += f'(local.set $jump (i32.const {jump_depth}));; to label {jump}\n'

          b += populate_stack_with(Ctx, sarg)
          b += populate_stack_with(Ctx, value)

          b += '(i32.eq) (br_if $start)\n'

        jump_depth = labels_to_idx.index(def_jump)
        b += f'(local.set $jump (i32.const {jump_depth}));; to label {def_jump}\n'
        b += '(br $start)\n'

      elif styp == 'send':
        push('x', 1, 'val')
        b += ';; send \n'
        b += '(suspend $module_lib_fn_yield-i32)\n'

      else:
        # assert False, f'No support for {styp} added yet'
        print('s', styp)

    b += ') ;; end of loop\n'
    b += 'unreachable\n';
    assert stack == 0

    localvars = '\n'
    for xreg in range(0, Ctx.max_xregs):
      localvars += f'(local $var_xreg_{xreg}_val i32)\n'

    for yreg in range(0, Ctx.max_yregs):
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
    offset=Ctx.literalidx,
  ) + Ctx.data
  return MODULE.format(
    name=module.name,
    imports="\n".join(Ctx.imports),
    data=data,
    body=body
  )

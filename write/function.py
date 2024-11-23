from write.utils import arg, push, pop, add_import, populate_stack_with

class MakeFun3:
  def __init__(self, ftarget, n, nn, darg, bounds):
    [_f, [target]] = ftarget
    assert _f == 'f'
    self.target = int(target)
    self.darg = arg(darg)
    [_list, [bounds]] = bounds
    assert _list == 'list'
    self.bounds = bounds

  def to_wat(self, ctx):
    add_import(ctx, '__internal', 'fn_alloc', 2)
    ctx.mark_trampoline('module', self.target, len(self.bounds))
    store_args = ''
    for (idx, carg) in enumerate(self.bounds):
      off = (idx+2) * 4
      store_args += f'''
        ;; store bound arg {idx}
        (i32.store 
          (i32.add (local.get $temp) (i32.const {off}))
          { push(ctx, *arg(carg)) }
        )
      '''

    return f'''
      ;; make_fun3 f {self.target}
      (i32.const {self.target}) ;; f {self.target}
      (i32.const { len(self.bounds) })
      (call $__internal_fn_alloc_2)
      (local.set $temp)
      { store_args }
      (local.get $temp)
      (i32.const 2)
      (i32.shl)
      (i32.const 2)
      (i32.or)
      { pop(ctx, *self.darg) }
    '''

class CallFun2:
  def __init__(self, typ, arity, sarg):
    [_atom, [typ]] = typ
    self.arity = int(arity)
    self.sarg = sarg
    assert _atom == 'atom'
    assert typ == 'safe'

  def to_wat(self, ctx):
    args = ''
    for arg_x in range(0, self.arity):
      args = push(ctx, 'x', arg_x)

    ctx.request_trampoline('module', self.arity)

    print('call bound function through a trampoline', self.arity)

    return f'''
      ;; call function or arity {self.arity} stored in {self.sarg}
      (block $ok
      (block $err
      { populate_stack_with(ctx, self.sarg) }
      (local.set $temp)

      (if ;; check mem tag
        (i32.eq (i32.and (i32.const 0x3) (local.get $temp)) (i32.const 2))
        (then (nop)) ;; we are good, it's a mem ref
        (else (br $err))
      )
      ;; put raw mem addr in temp
      (local.set $temp (i32.shr_u (local.get $temp) (i32.const 2)))

      (if ;; check func tag
        (i32.eq (i32.and (i32.const 0x3F) (i32.load (local.get $temp))) (i32.const 0x14))
        (then (nop)) ;; we are good, it's a function
        (else (br $err))
      )

      ) ;; end of err
      (local.get $temp)
      { args }
      (call $__module_trampoline_{self.arity})
      { pop(ctx, 'x', 0) }
      ) ;; end of ok
    '''

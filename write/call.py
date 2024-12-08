from write.utils import push, pop, add_import, ignore_call, sanitize_atom, arg

class LocalCall:
  def __init__(self, arity, dest, regs=None):
    [_f, fnumber] = dest
    assert _f == 'f'
    self.arity = int(arity)
    self.fnumber = int(fnumber)
    self.regs = regs

  def populate_args(self, ctx):
    b = ''
    for xreg in range(0, self.arity):
      b += push(ctx, 'x', xreg)

    return b

  def populate_ret(self, ctx):
    return pop(ctx, 'x', 0)

  def make_call(self, ctx):
    into_func = ctx.find_function(self.fnumber)
    assert not (into_func is None)
    ctx.max_xregs = max(ctx.max_xregs, self.arity)

    return f'''
      (call ${sanitize_atom(into_func.name)}_{into_func.arity})
      (local.set $temp)
      (if (i32.eq (local.get $temp) (i32.const 0xFF_FF_FF_00))
          (then (br $start))
      )
      (local.get $temp)
    '''

  def to_wat(self, ctx):
    return self.populate_args(ctx) + self.make_call(ctx) + self.populate_ret(ctx)


class LocalCallDrop(LocalCall):
  def to_wat(self, ctx):
    # TODO: discard the result or pass it through?
    return self.populate_args(ctx) + self.make_call(ctx) + 'return\n'

class LocalCallTail(LocalCall):
  def to_wat(self, ctx):
    # TODO: use tail call proposal
    return self.populate_args(ctx) + self.make_call(ctx) + 'return\n'


class ExternalCall(LocalCall):
  def __init__(self, _arity, dest, regs=None):
    (_e, ext_mod, ext_fn, ext_fn_arity) = dest

    assert _e == 'extfunc', _e
    self.arity = int(ext_fn_arity)
    self.ext_mod = ext_mod
    self.ext_fn = ext_fn
    self.regs = regs

  def make_call(self, ctx):
    if ignore_call(self.ext_mod, self.ext_fn):
      return ''

    add_import(ctx, self.ext_mod, self.ext_fn, self.arity)
    ctx.max_xregs = max(ctx.max_xregs, self.arity)

    return f'''
      (call ${sanitize_atom(self.ext_mod)}_{sanitize_atom(self.ext_fn)}_{self.arity})
      (local.set $temp)
      (if (i32.eq (local.get $temp) (i32.const 0xFF_FF_FF_00))
          (then (br $start))
      )
      (local.get $temp)
    '''


class ExternalCallDrop(ExternalCall):
  def to_wat(self, ctx):
    # TODO: discard the result or pass it through?
    return self.populate_args(ctx) + self.make_call(ctx) + 'return\n'

class ExternalCallTail(ExternalCall):
  def to_wat(self, ctx):
    # TODO: use tail call proposal
    return self.populate_args(ctx) + self.make_call(ctx) + 'return\n'

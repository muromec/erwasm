from write.utils import add_import, add_atom, populate_stack_with

class Label:
  def __init__(self, fnumber):
    self.fnumber = int(fnumber)

  def to_wat(self, ctx):
    b = f';; label f{self.fnumber}, deep {ctx.depth}\n'
    b += f') ;; end of depth {ctx.depth}\n'

    ctx.depth += 1

    return b

class FuncInfo:
  def __init__(self, *args):
    pass

  def to_wat(self, ctx):
    return '(unreachable) ;; func info trap\n'


class BadMatch:
  def __init__(self, reason):
    self.reason = reason

  def to_wat(self, ctx):
    add_import(ctx, 'erlang', 'throw', 2)
    add_import(ctx, 'minibeam', 'tuple_alloc', 1)

    push_badmatch = populate_stack_with(ctx, ['atom', ['badmatch']])
    push_error = populate_stack_with(ctx, ['atom', ['error']])
    push_r = populate_stack_with(ctx, self.reason)

    return f'''
      (call $minibeam_tuple_alloc_1 (i32.const 2))
      (local.set $temp)

      (i32.store
        (i32.add (local.get $temp) (i32.const 4))
        {push_badmatch}
      )
      (i32.store
        (i32.add (local.get $temp) (i32.const 8))
        {push_r}
      )

      (i32.or (i32.shl (local.get $temp) (i32.const 2)) (i32.const 2))
      (local.set $temp)

      (call $erlang_throw_2 {push_error} (local.get $temp)) (drop)
      (br $start)
    '''

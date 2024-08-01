from write.utils import push, pop, add_import

def arg(value):
  [typ, [num]] = value
  assert typ in ('x', 'y')
  return typ, int(num)

class BsMatch:
  def __init__(self, fail_dest, sarg, command_table):
    [_f, [fnumber]] = fail_dest
    assert _f == 'f'
    self.fnumber = fnumber

    self.sreg = arg(sarg)
    [_c, [table]] = command_table
    assert _c == 'commands'

    self.commands = table

  def to_wat(self, ctx):
    jump_depth = ctx.labels_to_idx.index(self.fnumber)

    b = f';; bs_match or fail to {self.fnumber}\n'
    b += f'(local.set $jump (i32.const {jump_depth}));; to label {self.fnumber}\n'

    for cmd in self.commands:
      [cmd_name, cmd_args] = cmd
      b + ';; chech {cmd_name}'

      if cmd_name == '\'=:=\'':
        cmd_name = 'eq'
      fun = getattr(self, f'command_{cmd_name}')
      b += fun(ctx, *cmd_args)
      b += '(if (i32.eqz) (then (br $start)))\n'


    b += ';; end of bs_match\n'

    return b

  def command_ensure_at_least(self, ctx, s, n):
    add_import(ctx, 'minibeam', 'bs_ensure_at_least', 2)

    return f'''(call 
        $minibeam_bs_ensure_at_least_2
        ({ push(ctx, *self.sreg) })
        (i32.const {s})
        (i32.const {n})
     )\n'''

  def command_ensure_exactly(self, ctx, n):
    add_import(ctx, 'minibeam', 'bs_ensure_exactly', 1)

    return f'''(call
        $minibeam_bs_ensure_exactly_1
        ({ push(ctx, *self.sreg) })
        (i32.const {n})
     )\n'''

  def command_integer(self, ctx, _xn, _literal, s, n, dreg):
    add_import(ctx, 'minibeam', 'bs_load_integer', 1)

    dreg = arg(dreg)
    return f'''
      ;; get integer from bs match
      (i32.shl
        (call
          $minibeam_bs_load_integer_1
          ({ push(ctx, *self.sreg) })
          (i32.const {s})
        )
        (i32.const 4)
      )
      (i32.or (i32.const 0xF))
      ( { pop(ctx, *dreg) } )
      (i32.const 1)
     \n'''

  def command_skip(self, ctx, s):
    add_import(ctx, 'minibeam', 'bs_skip', 1)

    return f'''(call
        $minibeam_bs_skip_1
        ({ push(ctx, *self.sreg) })
        (i32.const {s})
     )\n'''

  def command_eq(self, ctx, _x, s, value):
    add_import(ctx, 'minibeam', 'bs_load_integer', 1)

    return f'''
      ;; get integer from bs match
      (call 
        $minibeam_bs_load_integer_1
        ({ push(ctx, *self.sreg) })
        (i32.const {s})
      )
      (i32.const {value})
      (i32.eq)
     \n'''


class BsGetPosition:
  def __init__(self, sarg, darg, _n):
     self.sreg = arg(sarg)
     self.dreg = arg(darg)

  def to_wat(self, ctx):
    add_import(ctx, 'minibeam', 'bs_get_position', 0)

    return f'''
      ;; get integer from bs_get_position
      (i32.shl
        (call
          $minibeam_bs_get_position_0
          ({ push(ctx, *self.sreg) })
        )
        (i32.const 4)
      )
      (i32.or (i32.const 0xF))
      ( { pop(ctx, *self.dreg) } )
     \n'''


class BsSetPosition:
  def __init__(self, sarg, darg):
     self.sreg = arg(sarg)
     self.dreg = arg(darg)

  def to_wat(self, ctx):
    add_import(ctx, 'minibeam', 'bs_set_position', 1)

    return f'''
      ;; pass integer to set position
      (call
        $minibeam_bs_set_position_1
        ({ push(ctx, *self.sreg) })
        (i32.shr_u ( { push(ctx, *self.dreg) } ) (i32.const 4))
      )
     \n'''

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

    b = ';; bs_match or fail to {self.fnumber}\n'
    b += f'(local.set $jump (i32.const {jump_depth}));; to label {self.fnumber}\n'

    for cmd in self.commands:
      [cmd_name, cmd_args] = cmd
      b + ';; chech {cmd_name}'
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

  def command_integer(self, ctx, _xn, _literal, s, n, dreg):
    add_import(ctx, 'minibeam', 'bs_load_integer', 1)

    dreg = arg(dreg)
    return f'''
      ;; get integer from bs match
      (call 
        $minibeam_bs_load_integer_1
        ({ push(ctx, *self.sreg) })
        (i32.const {s})
      )
      ( { pop(ctx, *dreg) } )
      (i32.const 1)
     \n'''


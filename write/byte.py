from write.utils import push, pop, add_import, arg, populate_with, populate_stack_with

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

      if cmd_name == '=:=':
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
        { push(ctx, *self.sreg) }
        (i32.const {s})
        (i32.const {n})
     )\n'''

  def command_ensure_exactly(self, ctx, n):
    add_import(ctx, 'minibeam', 'bs_ensure_exactly', 1)

    return f'''(call
        $minibeam_bs_ensure_exactly_1
        { push(ctx, *self.sreg) }
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
          { push(ctx, *self.sreg) }
          (i32.const {s})
        )
        (i32.const 4)
      )
      (i32.or (i32.const 0xF))
      { pop(ctx, *dreg) }
      (i32.const 1)
     \n'''


  def command_binary(self, ctx, *args):
    return '(unreachable)\n'

  def command_skip(self, ctx, s):
    add_import(ctx, 'minibeam', 'bs_skip', 1)

    return f'''(call
        $minibeam_bs_skip_1
        { push(ctx, *self.sreg) }
        (i32.const {s})
     )\n'''

  def command_eq(self, ctx, _x, s, value):
    add_import(ctx, 'minibeam', 'bs_load_integer', 1)

    return f'''
      ;; get integer from bs match
      (call 
        $minibeam_bs_load_integer_1
        { push(ctx, *self.sreg) }
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
          { push(ctx, *self.sreg) }
        )
        (i32.const 4)
      )
      (i32.or (i32.const 0xF))
      { pop(ctx, *self.dreg) }
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
        { push(ctx, *self.sreg) }
        (i32.shr_u { push(ctx, *self.dreg) } (i32.const 4))
      )
     \n'''


class BsGetTail:
  def __init__(self, sarg, darg, max_regs):
    self.sreg = arg(sarg)
    self.dreg = arg(darg)
    self.max_regs = max_regs

  def to_wat(self, ctx):
    add_import(ctx, 'minibeam', 'bs_get_tail', 0)

    return f'''
      ;; get tail bytes from context
      (call
        $minibeam_bs_get_tail_0
        { push(ctx, *self.sreg) }
      )
      { pop(ctx, *self.dreg) }
     \n'''

class BsStartMatch:
  def __init__(self, params, max_regs, sarg, darg):
    [_a, [op]] = params

    self.sarg = sarg
    self.sreg = arg(sarg)
    self.dreg = arg(darg)
    self.max_regs = max_regs
    self.op = op
    assert _a == 'atom'
    assert op == 'resume' or op == 'no_fail'

  def to_wat(self, ctx):
    b = f';; bs_start_match4 {self.sreg} -> {self.dreg} ({self.op})\n'
    # if source and dest are the same, do nothing
    # normally ref count should be here
    if self.op == 'resume':
      if self.sreg == self.dreg:
        b += ';; nop\n'
        return b

      return b + populate_with(ctx, *self.dreg, self.sarg)
    if self.op == 'no_fail':
      add_import(ctx, 'minibeam', 'make_match_context', 1)

      b += push(ctx, *self.sreg)
      b += '(i32.const 0)\n'
      b += '(call $minibeam_make_match_context_1)\n'
      b += pop(ctx, *self.dreg)
      return b

    assert False, 'unknown flag for bs_start_match4'

class BsCreateBin:
  def __init__(self, fdest, alloc, live, unit, darg, ops):
    self.dreg = arg(darg)
    [_list, [ops]] = ops
    assert _list == 'list'
    self.ops = ops

  def to_wat(self, ctx):
    add_import(ctx, 'minibeam', 'get_byte_size', 1)
    add_import(ctx, 'minibeam', 'alloc_binary', 1)
    add_import(ctx, 'minibeam', 'into_buf', 3)

    next_value = False
    to_read = []
    for op in self.ops:
      if op == 'nil':
        next_value = True
        continue

      if not next_value:
        continue

      if op[0] == 'tr':
        op = op[1][0]

      if op[0] == 'string' and not op[1]:
        continue

      to_read.append(populate_stack_with(ctx, op))

      next_value = False
    b = ';; bs_create_bin\n'
    b += '(local.set $temp (i32.const 0))\n'

    for segment in to_read:
      b += f'''
        { segment }
        (call $minibeam_get_byte_size_1)
        (i32.add (local.get $temp))
        (local.set $temp)
      '''

    b += '''
      (call $minibeam_alloc_binary_1 (i32.const 16) (local.get $temp))
      (local.set $temp)
    '''

    b += '(i32.const 0) ;; initial offset 0\n'
    for segment in to_read:
      b += f'''
        (local.get $temp)
        { segment }
        (call $minibeam_into_buf_3)
      '''

    b += f'''
      (drop)
      (i32.or (i32.shl (local.get $temp) (i32.const 2)) (i32.const 2))
      { pop(ctx, *self.dreg) }

    '''

    return b

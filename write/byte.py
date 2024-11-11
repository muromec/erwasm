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
    add_import(ctx, 'minibeam', 'bs_ensure_at_least', 3)

    return f'''(call 
        $minibeam_bs_ensure_at_least_3
        { push(ctx, *self.sreg) }
        (i32.const {s})
        (i32.const {n})
     )\n'''

  def command_ensure_exactly(self, ctx, n):
    add_import(ctx, 'minibeam', 'bs_ensure_exactly', 2)

    return f'''(call
        $minibeam_bs_ensure_exactly_2
        { push(ctx, *self.sreg) }
        (i32.const {n})
     )\n'''

  def helper_get_integer(self, ctx, s):
    add_import(ctx, 'minibeam', 'bs_get_integer_ptr', 2)
    bits_to_read = int(s)

    """
    ;; wasm doesnt have separate big endian and little instructions,
    ;; while beam has BE by default -> <<$A, $C>> is 0x4143
    """

    load8 = """
          (i32.load8_u)
    """
    load16 = """
          (i32.load16_u)
          (local.set $temp)
          (i32.or
            (i32.shr_u (local.get $temp) (i32.const 8))
            (i32.and (i32.shl (local.get $temp) (i32.const 8)) (i32.const 0xFF00))
          )
    """

    # this is fine
    load32 = """
          (i32.load)
          (local.set $temp)

          (i32.or
              (i32.or
                (i32.shr_u (local.get $temp) (i32.const 24))
                (i32.and (
                  i32.shr_u (local.get $temp) (i32.const 8)) (i32.const 0xff_00)
                )
              )
              (i32.or
                (i32.and (
                  i32.shl (local.get $temp) (i32.const 8)) (i32.const 0xff_00_00)
                )
                (i32.and 
                  (i32.shl (local.get $temp) (i32.const 24)) (i32.const 0xff_00_00_00)
                )
              )
         )
    """
    if bits_to_read == 8:
      load = load8
      shift = ''
    elif bits_to_read < 8:
      load = load8
      shift_bits = 8 - bits_to_read
      shift = f'(i32.const {shift_bits}) (i32.shr_u)\n'
    elif bits_to_read == 16:
      load = load16
      shift = ''
    elif bits_to_read < 16:
      load = load16
      shift_bits = 16 - bits_to_read
      shift = f'(i32.const {shift_bits}) (i32.shr_u)\n'
    elif bits_to_read == 32:
      load = load32
      shift = ''
    elif bits_to_read < 32:
      load = load32
      shift_bits = 32 - bits_to_read
      shift = f'(i32.const {shift_bits}) (i32.shr_u)\n'

    mask = ''
    for _ignore in range(0, bits_to_read):
      mask = mask + '1'

    mask = int(mask, 2)

    return f'''
      ;; get integer from bs match s={s}, mask={hex(mask)}
      (call
        $minibeam_bs_get_integer_ptr_2
        { push(ctx, *self.sreg) }
        (i32.const {bits_to_read})
      )
      { load }
      { shift }
      (i32.const {mask})
      (i32.and)

    \n'''

  def command_integer(self, ctx, _xn, _literal, s, n, dreg):
    load = self.helper_get_integer(ctx, s)
    dreg = arg(dreg)
    return f'''
      { load }
      ;; shift to erl format
      (i32.const 4)
      (i32.shl)
      (i32.or (i32.const 0xF))

      ;; save and ok
      { pop(ctx, *dreg) }
      (i32.const 1)
     \n'''

  def command_binary(self, ctx, *args):
    return '(unreachable)\n'

  def command_skip(self, ctx, s):
    add_import(ctx, 'minibeam', 'bs_skip', 2)

    return f'''(call
        $minibeam_bs_skip_2
        { push(ctx, *self.sreg) }
        (i32.const {s})
     )\n'''

  def command_debug(self, ctx):
    add_import(ctx, 'minibeam', 'bs_debug', 1)

    return f'''(call
        $minibeam_bs_debug_1
        { push(ctx, *self.sreg) }
     )\n'''

  def command_eq(self, ctx, _x, s, value):
    load = self.helper_get_integer(ctx, s)
    return f'''
      ;; compare integers
      { load }
      (i32.const {value})
      (i32.eq)
     \n'''


class BsGetPosition:
  def __init__(self, sarg, darg, _n):
     self.sreg = arg(sarg)
     self.dreg = arg(darg)

  def to_wat(self, ctx):
    add_import(ctx, 'minibeam', 'bs_get_position', 1)

    return f'''
      ;; get integer from bs_get_position
      (i32.shl
        (call
          $minibeam_bs_get_position_1
          { push(ctx, *self.sreg) }
        )
        (i32.const 4)
      )
      (i32.or (i32.const 0xF))
      { pop(ctx, *self.dreg) }
     \n'''


class BsSetPosition:
  def __init__(self, sarg1, sarg2):
    self.sreg1 = arg(sarg1)
    self.sreg2 = arg(sarg2)

  def to_wat(self, ctx):
    add_import(ctx, 'minibeam', 'bs_set_position', 2)

    return f'''
      ;; pass integer to set position
      (call
        $minibeam_bs_set_position_2
        { push(ctx, *self.sreg1) }
        (i32.shr_u { push(ctx, *self.sreg2) } (i32.const 4))
      )
      (drop)
     \n'''


class BsGetTail:
  def __init__(self, sarg, darg, max_regs):
    self.sreg = arg(sarg)
    self.dreg = arg(darg)
    self.max_regs = max_regs

  def to_wat(self, ctx):
    add_import(ctx, 'minibeam', 'bs_get_tail', 1)

    return f'''
      ;; get tail bytes from context
      (call
        $minibeam_bs_get_tail_1
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
      add_import(ctx, 'minibeam', 'make_match_context', 2)

      b += push(ctx, *self.sreg)
      b += '(i32.const 0)\n'
      b += '(call $minibeam_make_match_context_2)\n'
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
    add_import(ctx, 'minibeam', 'get_bit_size', 1)
    add_import(ctx, 'minibeam', 'get_bit_size_utf8', 1)
    add_import(ctx, 'minibeam', 'get_bit_size_utf16', 1)
    add_import(ctx, 'minibeam', 'alloc_binary', 1)
    add_import(ctx, 'minibeam', 'into_buf', 4)
    add_import(ctx, 'minibeam', 'into_buf_utf8', 3)
    add_import(ctx, 'minibeam', 'into_buf_utf16', 3)

    next_value = False
    ops = self.ops[:]
    to_read = []

    while ops:
      (_atom, [typ]) = ops.pop(0)
      _ignore_align = ops.pop(0)
      unit_size = ops.pop(0)
      _nil = ops.pop(0)
      value = ops.pop(0)

      if value[0] == 'tr':
        value = value[1][0]

      value = populate_stack_with(ctx, value)

      args = []
      while ops:
        arg = ops.pop(0)
        if not isinstance(arg, tuple):
          pass
        elif arg[0] == 'atom' and arg[1][0] == 'all':
          pass
        elif arg[0] == 'atom' and arg[1][0] == 'undefined':
          pass
        elif arg[0] == 'atom':
          ops.insert(0, arg)
          to_read.append((value, typ, unit_size, args))
          break
        args.append(arg)

    to_read.append((value, typ, unit_size, args))

    b = ';; bs_create_bin\n'
    b += '(local.set $temp (i32.const 0))\n'

    def int_size(option):
      if not isinstance(option, (list, tuple)):
        return
      if option[0] == 'integer':
        return int(option[1][0])

    def match_op(op_name, option):
      if not isinstance(option, (list, tuple)):
        return
      return option[0] == 'atom' and option[1][0] == op_name

    def find_op(values, fn):
      for value in values:
        ret = fn(value)
        if ret is not None:
          return ret

    def type_needs_measure(typ):
      return (
        typ == 'append' or
        typ == 'utf8' or
        typ == 'utf16' or
        typ == 'binary'
      )


    for (segment, typ, unit_size, args) in to_read:
      needs_measure = type_needs_measure(typ)
      units = find_op(args, int_size)

      if needs_measure and typ == 'utf8':
        b += f'''
          { segment } ;; all= { needs_measure }, typ { typ }, { units }
          (call $minibeam_get_bit_size_utf8_1)
        '''
      elif needs_measure and typ == 'utf16':
        b += f'''
          { segment } ;; all= { needs_measure }, typ { typ }, { units }
          (call $minibeam_get_bit_size_utf16_1)
        '''

      elif needs_measure:
        b += f'''
          { segment } ;; all= { needs_measure }, typ { typ }, { units }
          (call $minibeam_get_bit_size_1)
        '''

      elif units is None:
        print('v', segment, typ, args)
        raise ValueError('Segment doesnt have measuring instruction and doesnt have pre defined value too')
      else:
        assert units is not None
        assert unit_size is not None
        b += f'''
          ;; known to be { units * unit_size } bits
          ;; args: { args }
          (i32.const {units * unit_size})
        '''

      b += '''
          (i32.add (local.get $temp))
          (local.set $temp)
      '''

    b += '''
      (call $minibeam_alloc_binary_1 (local.get $temp))
      (local.set $temp)
    '''

    b += '(i32.const 0) ;; initial offset 0\n'
    for (segment, typ, unit_size, args) in to_read:
      needs_int_size = typ == 'integer'
      units = find_op(args, int_size)

      if needs_int_size:
         assert units and unit_size
         bits_size = units * unit_size
      else:
         bits_size = 0

      if typ == 'utf8':
        b += f'''
          (local.get $temp)
          { segment }
          (call $minibeam_into_buf_utf8_3)
        '''
      elif typ == 'utf16':
        b += f'''
          (local.get $temp)
          { segment }
          (call $minibeam_into_buf_utf16_3)
        '''
      else:
        b += f'''
          (local.get $temp)
          { segment }
          (i32.const {bits_size})
          (call $minibeam_into_buf_4)
        '''

    b += f'''
      (drop)
      (i32.or (i32.shl (local.get $temp) (i32.const 2)) (i32.const 2))
      { pop(ctx, *self.dreg) }

    '''

    return b

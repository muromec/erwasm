from write.utils import populate_stack_with, push, pop, add_import

def arg(value):
  [typ, [num]] = value
  assert typ in ('x', 'y')
  return typ, int(num)

class Test3:
  def __init__(self, test_op, fail_dest, test_args):
    [_f, [fnumber]] = fail_dest
    assert _f == 'f'
    self.fnumber = fnumber
    self.test_args = test_args
    self.test_op = test_op

  def to_wat(self, ctx):
    jump = self.fnumber

    jump_depth = ctx.labels_to_idx.index(jump)
    assert not (jump_depth is None)
    b = f'(local.set $jump (i32.const {jump_depth}));; to label {jump}\n'

    for arg in self.test_args:
      b += populate_stack_with(ctx, arg)

    b += f' ;; test {self.test_op} and jump to {jump}\n'
    b += {
      'is_lt': 'i32.lt_u\n',
      'is_le': 'i32.le_u\n',
      'is_gt': 'i32.gt_u\n',
      'is_ge': 'i32.ge_u\n',
      'is_eq_exact': 'i32.eq\n',
      'is_atom': '''
        (i32.and (i32.const 0x3F))
        (i32.eq (i32.const 0xB))
      ''',
      'is_nil': '''
        (local.set $temp)
        (loop $loop

        (local.get $temp)
        (i32.and (i32.const 3))
        (if
          (i32.eq (i32.const 2)) ;; mem ref
          (then
            (local.get $temp)
            (i32.shr_u (i32.const 2))
            (i32.load)
            (local.set $temp)
            (br $loop)
          )
          (else
            (local.set $temp
              (i32.eq (i32.const 0x3b) (local.get $temp))
            )
          )
        ))
        (local.get $temp)
      ''',
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
            (i32.eq (i32.const 0x3b))
            (i32.eqz)
            (local.set $temp)
          )
          (else
            (i32.const 0)
            (local.set $temp)
          )
        )
        (local.get $temp)
      '''
    }[self.test_op]

    # erlang test condition jump is inverted
    # jump to the label specified if the condition fails
    b += f'(i32.eqz) (br_if $start)\n'

    return b

class Test5:
  def __init__(self, test_op, fail_dest, _dn, test_args, dest):

    [_f, [fnumber]] = fail_dest
    assert _f == 'f'
    self.fnumber = fnumber
    self.test_args = test_args
    self.test_op = test_op
    self.dreg = arg(dest)

  def to_wat(self, ctx):
    jump_depth = ctx.labels_to_idx.index(self.fnumber)
    assert not (jump_depth is None)

    b = f'(local.set $jump (i32.const {jump_depth}));; to label {self.fnumber}\n'
   
    b += getattr(self, f'test_{self.test_op}')(ctx)
    b += f'(i32.eqz) (br_if $start)\n'

    return b

  def test_bs_start_match3(self, ctx):
    assert len(self.test_args) == 1
    [match_ctx_reg] = self.test_args
    sreg = arg(match_ctx_reg)

    add_import(ctx, 'minibeam', 'make_match_context', 1)
    return f'''
      ({ push(ctx, *sreg) })
      (i32.const 0) ;; do we really need to pass offset?
      (call $minibeam_make_match_context_1)
      (local.set $temp)
      (if (i32.eqz (local.get $temp))
        (then (nop))
        (else
          (local.get $temp)
          { pop(ctx, *self.dreg) }
        )
      )
      (i32.eqz (local.get $temp))
      (i32.eqz)
    '''

  def test_bs_get_binary2(self, ctx):
    add_import(ctx, 'minibeam', 'get_binary_from_ctx', 2)

    [_tr, [match_ctx_reg, [_reg_type, _n]]] = self.test_args[0]
    assert _tr == 'tr'
    assert _reg_type == 't_bs_context'
    [_tr, [size_reg, [_reg_type, _n]]] = self.test_args[1]
    assert _tr == 'tr'
    assert _reg_type == 't_integer'

    assert self.test_args[2] == 8

    sreg1 = arg(match_ctx_reg)
    sreg2 = arg(size_reg)

    return f'''
      ({ push(ctx, *sreg1) })
      ({ push(ctx, *sreg2) })
      (call $minibeam_get_binary_from_ctx_2)
      (local.set $temp)
      (if (i32.eqz (local.get $temp))
        (then (nop))
        (else
          (local.get $temp)
          { pop(ctx, *self.dreg) }
        )
      )
      (i32.eqz (local.get $temp))
      (i32.eqz)

    '''


class Test:
  def __new__(cls, *args):
    if len(args) == 3:
      return Test3(*args)
    
    if len(args) == 5:
      return Test5(*args)

    assert False


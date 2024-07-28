from write.utils import populate_stack_with

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
    }[self.test_op]

    # erlang test condition jump is inverted
    # jump to the label specified if the condition fails
    b += f'(i32.eqz) (br_if $start)\n'

    return b

class Test5:
  def __init__(self, test_op, fail_dest, _dn, test_args, dest):
    assert test_op == 'bs_start_match3'

    [_f, [fnumber]] = fail_dest
    assert _f == 'f'
    self.fnumber = fnumber
    self.test_args = test_args
    self.test_op = test_op
    self.dest = dest

  def to_wat(self, ctx):
    jump = self.fnumber

    jump_depth = ctx.labels_to_idx.index(jump)
    assert not (jump_depth is None)
    b = f'(local.set $jump (i32.const {jump_depth}));; to label {jump}\n'
    print('implement me')

    return b


class Test:
  def __new__(cls, *args):
    if len(args) == 3:
      return Test3(*args)
    
    if len(args) == 5:
      return Test5(*args)

    assert False


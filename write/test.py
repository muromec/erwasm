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
    b += f' ;; test {self.test_op} and jump to {jump}\n'

    test = getattr(self, f'test_{self.test_op}', self.test_common)

    b += test(ctx)

    # erlang test condition jump is inverted
    # jump to the label specified if the condition fails
    b += f'(i32.eqz) (br_if $start)\n'

    return b

  def load_args_to_stack(self, ctx):
    b = ''
    for arg in self.test_args:
      b += populate_stack_with(ctx, arg)

    return b

  def test_is_eq_exact(self, ctx):
    b = self.load_args_to_stack(ctx)
    add_import(ctx, 'minibeam', 'test_eq_exact', 2)

    return b + '(call $minibeam_test_eq_exact_2)\n'

  def test_is_ne_exact(self, ctx):
    b = self.load_args_to_stack(ctx)
    add_import(ctx, 'minibeam', 'test_eq_exact', 2)

    return b + '''
        (call $minibeam_test_eq_exact_2)
        (i32.eqz)
    '''

  def test_is_boolean(self, ctx):
    [sarg] = self.test_args
    return '(unreachable)\n'

  def test_test_arity(self, ctx):
    [sarg, tuple_arity] = self.test_args
    add_import(ctx, 'erdump', 'hexlog', 1)

    b = f'''
      ;; test test_arity
      { populate_stack_with(ctx, sarg) }
      (local.set $temp)

      (local.get $temp)
      (i32.and (i32.const 3))
      (if
        (i32.eq (i32.const 2)) ;; mem ref
        (then
          (local.get $temp)
          (i32.shr_u (i32.const 2))
          (local.set $temp) ;; raw pointer to tuple head

          (i32.load (local.get $temp))
          (i32.and (i32.const 0x3f))
          (if
            (i32.eqz) ;; is tuple
            (then
              (i32.load (local.get $temp))
              (i32.const 6)
              (i32.shr_u)
              (i32.eq (i32.const {tuple_arity}))
              (local.set $temp)
            )
            (else ;; not a tuple
              (local.set $temp (i32.const 0))
            )
          )
        )
        (else ;; not a mem ref
          (local.set $temp (i32.const 0))
        )
      )
      (local.get $temp)
    '''

    return b

  def test_is_tuple(self, ctx):
    [sarg] = self.test_args
    add_import(ctx, 'erdump', 'hexlog', 1)

    b = f'''
      ;; test is_tuple
      { populate_stack_with(ctx, sarg) }
      (local.set $temp)


      (local.get $temp)
      (i32.and (i32.const 3))
      (if
        (i32.eq (i32.const 2)) ;; mem ref
        (then
          (local.get $temp)
          (i32.shr_u (i32.const 2))
          (local.set $temp) ;; raw pointer to tuple head

          (i32.load (local.get $temp))
          (i32.and (i32.const 0x3f))
          (i32.eqz)
          (local.set $temp)
        )
        (else ;; not a mem ref
          (local.set $temp (i32.const 0))
        )
      )
      (local.get $temp)
    '''

    return b

  def test_is_tagged_tuple(self, ctx):
    [sarg, tuple_arity, tag_atom] = self.test_args
    assert tag_atom[0] == 'atom'
    add_import(ctx, 'erdump', 'hexlog', 1)

    b = f'''
      ;; test is_tagged_tuple
      { populate_stack_with(ctx, sarg) }
      (local.set $temp)

      (local.get $temp)
      (i32.and (i32.const 3))
      (if
        (i32.eq (i32.const 2)) ;; mem ref
        (then
          (local.get $temp)
          (i32.shr_u (i32.const 2))
          (local.set $temp) ;; raw pointer to tuple head


          (i32.load (local.get $temp))
          (i32.and (i32.const 0x3f))

          (if
            (i32.eqz) ;; is tuple
            (then

              (i32.load (local.get $temp))
              (i32.const 6)
              (i32.shr_u)
              (if
                (i32.eq (i32.const {tuple_arity}))
                (then
                  (i32.load (i32.add (local.get $temp) (i32.const 4)))

                  { populate_stack_with(ctx, tag_atom) }

                  (local.set $temp (i32.eq))
                )
                (else ;; not the right arity
                  (local.set $temp (i32.const 0))
                )
              )
            )
            (else ;; not a tuple
              (local.set $temp (i32.const 0))
            )
          )
        )
        (else ;; not a mem ref
          (local.set $temp (i32.const 0))
        )
      )
      (local.get $temp)


    '''
    return b

  def test_common(self, ctx):
    b = self.load_args_to_stack(ctx)

    return b + ({
      'is_lt': 'i32.lt_u\n',
      'is_le': 'i32.le_u\n',
      'is_gt': 'i32.gt_u\n',
      'is_ge': 'i32.ge_u\n',
      'is_function2': '(drop) (drop) (i32.const 0)\n', # its never a function
      'is_atom': '''
        (i32.and (i32.const 0x3F))
        (i32.eq (i32.const 0xB))
      ''',
      'is_integer': '''
        (i32.and (i32.const 0xF))
        (i32.eq (i32.const 0xF))
      ''',
      'is_float': ''' ;; is float is aliased to is integer because reasons
        (i32.and (i32.const 0xF))
        (i32.eq (i32.const 0xF))
      ''',
      'is_number': '''
        (i32.and (i32.const 0xF))
        (i32.eq (i32.const 0xF))
      ''',
      'is_binary': '''
        (local.set $temp)

        (local.get $temp)
        (i32.and (i32.const 3))
        (if
          (i32.eq (i32.const 2)) ;; mem ref
          (then
            (local.get $temp)
            (i32.shr_u (i32.const 2))
            (i32.load)
            (i32.and (i32.const 0x3F))
            (i32.eq (i32.const 0x24)) ;; should be heap binary
            (local.set $temp)
          )
          (else
            (i32.const 0)
            (local.set $temp)
          )
        )
        (local.get $temp)

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
            (i32.and (i32.const 3))
            (i32.eq (i32.const 1)) ;; list next item ref
            (local.set $temp)
          )
          (else
            (i32.const 0)
            (local.set $temp)
          )
        )
        (local.get $temp)
        (i32.or (i32.const 0xFF_00))
        (local.get $temp)
      ''',
      'is_list': f'''
        ;; test the list
        (local.set $temp)

        (local.get $temp)
        (i32.and (i32.const 3))
        (if
          (i32.eq (i32.const 2)) ;; mem ref
          (then
            (local.get $temp)
            (i32.shr_u (i32.const 2))
            (i32.load)
            (local.set $temp)

            (i32.and (i32.const 3) (local.get $temp))
            (if (i32.eq (i32.const 1)) ;; list next item ref
              (then (local.set $temp (i32.const 1)))
              (else
                (i32.eq (local.get $temp) (i32.const 0x3b))
                (local.set $temp)
              )
            )
          )
          (else
            (i32.const 0)
            (local.set $temp)
          )
        )
        (local.get $temp)
        (i32.or (i32.const 0xFF_00))
        (local.get $temp)
      '''

    }[self.test_op])


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

    add_import(ctx, 'minibeam', 'make_match_context', 2)
    return f'''
      { push(ctx, *sreg) }
      (i32.const 0) ;; do we really need to pass offset?
      (call $minibeam_make_match_context_2)
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

  def test_bs_get_utf8(self, ctx):
    add_import(ctx, 'minibeam', 'get_utf8_from_ctx', 1)

    [_tr, [match_ctx_reg, [_reg_type, _n]]] = self.test_args[0]
    assert _tr == 'tr'
    assert _reg_type == 't_bs_context'

    return f'''
      { populate_stack_with(ctx, self.test_args[0]) }
      (call $minibeam_get_utf8_from_ctx_1)
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

  def test_bs_get_utf16(self, ctx):
    return '(unreachable)\n'

  def test_bs_get_binary2(self, ctx):
    add_import(ctx, 'minibeam', 'get_binary_from_ctx', 2)

    [_tr, [match_ctx_reg, [_reg_type, _n]]] = self.test_args[0]
    assert _tr == 'tr'
    assert _reg_type == 't_bs_context'

    assert self.test_args[2] == 8

    return f'''
      { populate_stack_with(ctx, self.test_args[0]) }
      { populate_stack_with(ctx, self.test_args[1]) }
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


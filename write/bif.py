from write.utils import push, pop, populate_stack_with, add_import, add_atom

def arg(value):
  [typ, [num]] = value
  assert typ in ('x', 'y', 'fr')
  return typ, int(num)

class Bif:
  def __init__(self, op, fdest, sargs, dest):
    [_f, [fnumber]] = fdest
    assert _f == 'f'

    self.sargs = sargs
    self.darg = arg(dest)
    self.op = op
    self.fnumber = fnumber

  def load_args_to_stack(self, ctx):
    b = ''
    for arg in self.sargs:
      b += populate_stack_with(ctx, arg)

    return b

  def make_bif(self, ctx):
    b = ''
    if self.op == "+":
      b += '(i32.xor (i32.const 0xF))\n'
      b += '(i32.add)\n'
    elif self.op ==  "-":
      b += '(i32.xor (i32.const 0xF))\n'
      b += '(i32.sub)\n'
    elif self.op == "*":
      b += '''
      (i32.shr_u (i32.xor (i32.const 0xF)) (i32.const 4))
      (local.set $temp)
      (i32.shr_u (i32.xor (i32.const 0xF)) (i32.const 4))
      (i32.mul (local.get $temp))
      (local.set $temp)

      (i32.shl (local.get $temp) (i32.const 4))
      (i32.or (i32.const 0xF))
      '''
    elif self.op == "byte_size":
      add_import(ctx, 'minibeam', 'get_bit_size', 1)
      b += f'''
        (call $minibeam_get_bit_size_1)
        (i32.const 1) ;; the size in bits, move one more to the left
                      ;; to fit in integer tag
        (i32.shl)
        (i32.or (i32.const 0xF))
      '''
    elif self.op == "length":
      add_import(ctx, 'erlang', 'length', 1)
      b += f'''(call $erlang_length_1)\n'''
    elif self.op == "div":
      b += '''
      (i32.shr_u (i32.xor (i32.const 0xF)) (i32.const 4))
      (local.set $temp)
      (i32.shr_u (i32.xor (i32.const 0xF)) (i32.const 4))
      (i32.div_u (local.get $temp))
      (i32.shl (local.get $temp) (i32.const 4))
      (i32.or (i32.const 0xF))
      '''
    elif self.op == "rem":
      b += '''
      (i32.shr_u (i32.xor (i32.const 0xF)) (i32.const 4))
      (local.set $temp)
      (i32.shr_u (i32.xor (i32.const 0xF)) (i32.const 4))
      (i32.rem_u (local.get $temp))
      (i32.shl (local.get $temp) (i32.const 4))
      (i32.or (i32.const 0xF))
      '''
    elif self.op == "bsr":
      b += '''
        (i32.const 4)
        (i32.shr_u)
        (i32.shr_u)
        (i32.const 0xF)
        (i32.or)
      '''
    elif self.op == "band":
      b += '''
        (i32.and)
        (i32.const 0xF)
        (i32.or)
      '''
    elif self.op == "fdiv":
      b += '(unreachable);; fdiv\n'
    elif self.op == "fmul":
      b += '(unreachable);; fdiv\n'
    else:
      assert False, f'unknown bif {self.op}'

    return b

  def bif_inline(self, ctx):
    b = self.load_args_to_stack(ctx)
    b += self.make_bif(ctx)

    return b

  def bif_sub(self, ctx):
    b = ''
    if len(self.sargs) == 1:
      b += '(i32.const 0)\n'

    b += self.load_args_to_stack(ctx)
    b += self.make_bif(ctx)
    return b

  def bif_raise(self, ctx):
    add_import(ctx, 'erlang', 'throw', 2)

    ex_typ =  self.darg
    [_ex_trace, ex_val] = self.sargs

    push_typ = push(ctx, *ex_typ)
    push_val = push(ctx, *arg(ex_val))

    return f'''
      (call $erlang_throw_2 {push_typ} {push_val}) (drop)
      (br $start)
    '''

  def bif_and(self, ctx):
    add_import(ctx, 'minibeam', 'assert_atom', 1)
    add_import(ctx, '__internal', 'to_atom', 1)

    add_atom(ctx, 'error')
    add_atom(ctx, 'badarg')
    add_atom(ctx, 'true')
    add_atom(ctx, 'false')

    [val_a, val_b] = self.sargs

    push_a = push(ctx, *arg(val_a))
    push_b = push(ctx, *arg(val_b))

    return f'''
      (if
        (call $minibeam_assert_atom_1 {push_a})
        (then (br $start))
      )
      (if
        (call $minibeam_assert_atom_1 {push_b})
        (then (br $start))
      )

      (if  (result i32)
        (i32.and
          (i32.eq (global.get $__unique_atom__true) (i32.shr_u {push_a} (i32.const 6)))
          (i32.eq (global.get $__unique_atom__true) (i32.shr_u {push_b} (i32.const 6)))
        )
        (then
          (global.get $__unique_atom__true)
        )
        (else
          (global.get $__unique_atom__false)
        )
      )
      (call $__internal_to_atom_1)
    '''

  def bif_or(self, ctx):
    add_import(ctx, 'minibeam', 'assert_atom', 1)
    add_import(ctx, '__internal', 'to_atom', 1)

    add_atom(ctx, 'error')
    add_atom(ctx, 'badarg')
    add_atom(ctx, 'true')
    add_atom(ctx, 'false')

    [val_a, val_b] = self.sargs

    push_a = push(ctx, *arg(val_a))
    push_b = push(ctx, *arg(val_b))

    return f'''
      (if
        (call $minibeam_assert_atom_1 {push_a})
        (then (br $start))
      )
      (if
        (call $minibeam_assert_atom_1 {push_b})
        (then (br $start))
      )

      (if  (result i32)
        (i32.or
          (i32.eq (global.get $__unique_atom__true) (i32.shr_u {push_a} (i32.const 6)))
          (i32.eq (global.get $__unique_atom__true) (i32.shr_u {push_b} (i32.const 6)))
        )
        (then
          (global.get $__unique_atom__true)
        )
        (else
          (global.get $__unique_atom__false)
        )
      )
      (call $__internal_to_atom_1)
    '''

  def bif_element(self, ctx):
    jump_depth = ctx.labels_to_idx.index(self.fnumber) if self.fnumber else None
    fail_jump = f'''
        (local.set $jump (i32.const {jump_depth}));; to label {self.fnumber}\n'
        (br $start)
    ''' if jump_depth else '(unreachable)'

    [num, subj] = self.sargs
    load_n = populate_stack_with(ctx, num)
    load_s = populate_stack_with(ctx, subj)

    return f'''
      { load_s }
      (i32.and (i32.const 3))
      (if
        (i32.eq (i32.const 2)) ;; mem ref
        (then
          { load_s }
          (i32.const 2)
          (i32.shr_u)
          (local.set $temp) ;; raw pointer to tuple head

          (i32.load (local.get $temp))
          (i32.and (i32.const 0x3f))

          (if
            (i32.eqz) ;; is tuple
            (then
              { load_n }
              (i32.const 2)
              (i32.shr_u)
              (i32.const 3)
              (i32.xor)
              (local.get $temp)
              (i32.add)
              (i32.load)
              (local.set $temp)
            )
            (else ;; not a tuple
              { fail_jump }
            )
          )
        )
        (else ;; not a mem ref
          { fail_jump }
        )
      )
      (local.get $temp)
    '''
  def bif_eq(self, ctx):
    b = self.load_args_to_stack(ctx)
    add_import(ctx, 'minibeam', 'test_eq_exact', 2)

    return b + '(call $minibeam_test_eq_exact_2)\n'

  def to_wat(self, ctx):
    b = f';; bif {self.op}\n'

    fn_name = {
      '-': 'sub',
      '=/=': 'eq',
    }.get(self.op) or self.op
    bif_fn = getattr(self, f'bif_{fn_name}', self.bif_inline)
    b += bif_fn(ctx)

    b += pop(ctx, *self.darg)

    b += f';; end bif {self.op}\n'

    return b

class GcBif(Bif):
  def __init__(self, op, fdest, _max_regs, sargs, dest):
    [_f, [fnumber]] = fdest
    assert _f == 'f'

    self.sargs = sargs
    self.darg = arg(dest)
    self.op = op
    self.fnumber = fnumber


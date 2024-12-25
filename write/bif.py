from write.utils import push, pop, populate_stack_with, add_import, add_atom, arg

class Bif:
  def __init__(self, op, fdest, sargs, dest):
    [_f, fnumber] = fdest
    assert _f == 'f'

    self.sargs = sargs
    self.darg = arg(dest)
    bif = op
    self.fnumber = fnumber

  def load_args_to_stack(self, ctx):
    b = ''
    for arg in self.sargs:
      b += populate_stack_with(ctx, arg)

    return b

  def make_bif(self, ctx):
    (_mod, bif, arity) = ctx.resolve_import(self.import_id)
    b = ''
    if bif == "+":
      b += '(i32.xor (i32.const 0xF))\n'
      b += '(i32.add)\n'
    elif bif ==  "-":
      b += '(i32.xor (i32.const 0xF))\n'
      b += '(i32.sub)\n'
    elif bif == "*":
      b += '''
      (i32.shr_u (i32.xor (i32.const 0xF)) (i32.const 4))
      (local.set $temp)
      (i32.shr_u (i32.xor (i32.const 0xF)) (i32.const 4))
      (i32.mul (local.get $temp))
      (local.set $temp)

      (i32.shl (local.get $temp) (i32.const 4))
      (i32.or (i32.const 0xF))
      '''
    elif bif == "byte_size":
      add_import(ctx, 'minibeam', 'get_bit_size', 1)
      b += f'''
        (call $minibeam_get_bit_size_1)
        (i32.const 1) ;; the size in bits, move one more to the left
                      ;; to fit in integer tag
        (i32.shl)
        (i32.or (i32.const 0xF))
      '''
    elif bif == "length":
      add_import(ctx, 'erlang', 'length', 1)
      b += f'''(call $erlang_length_1)\n'''
    elif bif == "div":
      b += '''
      (i32.shr_u (i32.xor (i32.const 0xF)) (i32.const 4))
      (local.set $temp)
      (i32.shr_u (i32.xor (i32.const 0xF)) (i32.const 4))
      (i32.div_u (local.get $temp))
      (i32.shl (local.get $temp) (i32.const 4))
      (i32.or (i32.const 0xF))
      '''
    elif bif == "rem":
      b += '''
      (i32.shr_u (i32.xor (i32.const 0xF)) (i32.const 4))
      (local.set $temp)
      (i32.shr_u (i32.xor (i32.const 0xF)) (i32.const 4))
      (i32.rem_u (local.get $temp))
      (i32.shl (local.get $temp) (i32.const 4))
      (i32.or (i32.const 0xF))
      '''
    elif bif == "bsr":
      b += '''
        (i32.const 4)
        (i32.shr_u)
        (i32.shr_u)
        (i32.const 0xF)
        (i32.or)
      '''
    elif bif == "band":
      b += '''
        (i32.and)
        (i32.const 0xF)
        (i32.or)
      '''
    elif bif == "fdiv":
      b += '(unreachable);; fdiv\n'
    elif bif == "fmul":
      b += '(unreachable);; fdiv\n'
    else:
      assert False, f'unknown bif {bif}'

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

    add_atom(ctx, 'error')
    add_atom(ctx, 'badarg')

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

      (i32.and
          (i32.eq (global.get $__unique_atom__true) (i32.shr_u {push_a} (i32.const 6)))
          (i32.eq (global.get $__unique_atom__true) (i32.shr_u {push_b} (i32.const 6)))
      )
      {self.boolean_ret_helper(ctx)}
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

    return b + '(i32.eq)\n' + self.boolean_ret_helper(ctx)


  def bif_same(self, ctx):
    b = self.load_args_to_stack(ctx)
    add_import(ctx, 'minibeam', 'test_eq_exact', 2)

    return b + '(call $minibeam_test_eq_exact_2)\n' + self.boolean_ret_helper(ctx)

  def boolean_ret_helper(self, ctx):
    add_import(ctx, '__internal', 'to_atom', 1)
    add_atom(ctx, 'true')
    add_atom(ctx, 'false')

    return '''
      (if  (result i32)
        (then
          (global.get $__unique_atom__true)
        )
        (else
          (global.get $__unique_atom__false)
        )
      )
      (call $__internal_to_atom_1)
    '''

  def to_wat(self, ctx):
    (_mod, bif, arity) = ctx.resolve_import(self.import_id)
    b = f';; bif {bif}\n'

    assert arity == len(self.sargs)
    assert _mod == 'erlang'

    fn_name = {
      '-': 'sub',
      '=/=': 'same',
      '==': 'eq',
    }.get(bif) or bif
    bif_fn = getattr(self, f'bif_{bif}', self.bif_inline)
    b += bif_fn(ctx)

    b += pop(ctx, *self.darg)

    b += f';; end bif {bif}\n'

    return b

class GcBif(Bif):
  def __init__(self, fdest, _max_regs, bif, sarg1, sarg2, dest):
    [_f, fnumber] = fdest
    assert _f == 'label'

    self.sargs = [sarg1, sarg2]
    self.darg = arg(dest)
    self.import_id = bif
    self.fnumber = fnumber


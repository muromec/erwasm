from write.utils import push, pop, add_import, arg, populate_stack_with

class PutTuple2:
  def __init__(self, dreg, value):
    self.dreg = arg(dreg)
    self.value = value

  def to_wat(self, ctx):
    b = ';; put_tuple2\n'
    add_import(ctx, 'minibeam', 'tuple_alloc', 1)

    [_list, [vlist]] = self.value
    assert _list == 'list'

    size = len(vlist)
    b += f'(call $minibeam_tuple_alloc_1 (i32.const {size}))\n'
    b += '(local.set $temp)\n'

    for idx, item in enumerate(vlist):
      b += f'''
        ;; put tuple item {idx}
        (i32.add (local.get $temp) (i32.const {(idx + 1) * 4}))
        { populate_stack_with(ctx, item) }
        (i32.store)
      '''

    b += '(i32.or (i32.shl (local.get $temp) (i32.const 2)) (i32.const 2))\n'
    b += pop(ctx, *self.dreg)
    b += ';; end put_tuple2\n'


    return b

class GetTupleElement:
  def __init__(self, sreg, offset, dreg):
    self.dreg = arg(dreg)
    self.sreg = arg(sreg)
    self.offset = offset

  def to_wat(self, ctx):
    b = f';; get_tuple_element {self.offset}\n'
    b += f'''
      { push(ctx, *self.sreg) }
      (local.set $temp)

      (local.get $temp)
      (i32.and (i32.const 3))
      (if
        (i32.eq (i32.const 2)) ;; mem ref
        (then
          (i32.shr_u (local.get $temp) (i32.const 2))
          (local.set $temp) ;; raw pointer to tuple head

          (i32.load (local.get $temp))
          (i32.and (i32.const 0x3f))

          (if
            (i32.eqz) ;; is tuple
            (then
              (local.get $temp)
              (i32.const {4 + (self.offset) * 4})
              (i32.add)
              (i32.load) ;; load element {self.offset}
              (local.set $temp)
            )
            (else ;; not a tuple
              (unreachable)
            )
          )
        )
        (else ;; not a mem ref
          (unreachable)
        )
      )
      (local.get $temp)
      { pop(ctx, *self.dreg) }
    ;; end get tuple element
    '''
    return b


class SelectTupleArity:
  def __init__(self, sarg, fail, table):
    [_tr, [sarg, _info]] = sarg
    assert _tr == 'tr'
    self.sarg = arg(sarg)
    self.fail = fail
    [_list, [table]] = table
    assert _list == 'list'
    self.table = table

  def to_wat(self, ctx):
    b = f'''
      ;; select_tuple_arity
      { push(ctx, *self.sarg) }
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
              (local.set $temp)
            )
            (else ;; not a tuple
              (unreachable)
            )
          )
        )
        (else ;; not a mem ref
          (local.set $temp (i32.const 0))
        )
      )
    '''

    table = self.table[:]
    while table:
      arity = table.pop(0)
      [_f, [jump]] = table.pop(0)
      assert _f == 'f'
      jump = int(jump)
      jump_depth = ctx.labels_to_idx.index(jump)
      assert not (jump_depth is None)

      b += f'''
        ;; for arity {arity} jump to label {jump}
        (local.set $jump (i32.const {jump_depth}))
        (i32.eq (i32.const {arity}) (local.get $temp))
        (br_if $start)
      '''

    [_f, [jump]] = self.fail
    jump = int(jump)
    jump_depth = ctx.labels_to_idx.index(jump)

    b += f'''
      ;; fallthrough to {jump_depth}
      (local.set $jump (i32.const {jump_depth}))
      (br $start)
    ;; end of select_tuple_arity
    '''


    return b

class UpdateRecord:
  def __init__(self, update_type, arity, sreg, dreg, table):
    [_atom, [_inplace] ] = update_type
    assert _atom == 'atom'
    assert _inplace == 'inplace'

    self.arity = arity
    self.sreg = sreg
    self.dreg = arg(dreg)

    [_list, [table]] = table
    assert _list == 'list'
    self.table = table

  def to_wat(self, ctx):
    [offset, new_value] = self.table
    add_import(ctx, '__internal', 'hexlog', 1)
    b = f'''
      ;; update_record in place
      { populate_stack_with(ctx, self.sreg) }
      (local.set $temp)

      (local.get $temp)
      (i32.and (i32.const 3))
      (if
        (i32.eq (i32.const 2)) ;; mem ref
        (then (nop))
        (else (unreachable))
      )

      (i32.shr_u (local.get $temp) (i32.const 2))
      (local.set $temp) ;; raw pointer to tuple head

      (i32.load (local.get $temp))
      (i32.and (i32.const 0x3f))

      (if (i32.eqz) ;; is tuple
        (then (nop))
        (else (unreachable))
      )

      (local.get $temp)
      (i32.const {int(offset) * 4})
      (i32.add)  ;; pos of element {offset}
      { populate_stack_with(ctx, new_value) }
      (i32.store) ;; save to mem

      { populate_stack_with(ctx, self.sreg) }
      { pop(ctx, *self.dreg) }

    ;; end update record
    '''
    return b


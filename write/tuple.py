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


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

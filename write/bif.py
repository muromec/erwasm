from write.utils import push, pop, populate_stack_with, add_import

def arg(value):
  [typ, [num]] = value
  assert typ in ('x', 'y')
  return typ, int(num)

class Bif:
  def __init__(self, op, fdest, _max_regs, sargs, dest):
    [_f, [fnumber]] = fdest
    assert _f == 'f'

    self.sargs = sargs
    self.darg = arg(dest)
    self.op = op

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
      add_import(ctx, 'minibeam', 'get_byte_size', 1)
      b += f'''
        (call $minibeam_get_byte_size_1)
        (i32.const 4)
        (i32.shl)
        (i32.or (i32.const 0xF))
      '''

    else:
      assert False, f'unknown bif {self.op}'

    return b

  def bif_inline(self, ctx):
    b = ''
    for arg in self.sargs:
      b += populate_stack_with(ctx, arg)

    b += self.make_bif(ctx)

    return b

  def bif_sub(self, ctx):
    b = ''
    if len(self.sargs) == 1:
      b += '(i32.const 0)\n'

    for arg in self.sargs:
      b += populate_stack_with(ctx, arg)

    b += self.make_bif(ctx)
    return b

  def to_wat(self, ctx):
    b = f';; bif {self.op}\n'

    fn_name = {
      '-': 'sub',
    }.get(self.op) or self.op
    bif_fn = getattr(self, f'bif_{fn_name}', self.bif_inline)
    b += bif_fn(ctx)

    b += pop(ctx, *self.darg)

    b += f';; end bif {self.op}\n'

    return b

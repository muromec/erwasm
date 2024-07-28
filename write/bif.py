from write.utils import push, pop

def arg(value):
  [typ, [num]] = value
  assert typ in ('x', 'y')
  return typ, int(num)

class Bif:
  def __init__(self, op, fdist, arity, sargs, dest):
    [_f, [fnumber]] = fdest
    assert _f == 'f'
    self.arity = int(arity)
    assert self.arity == len(sargs)

    self.sargs = sargs
    self.darg = arg(dest)
    self.op = op

  def make_test(self):
    if self.op == "'+'":
      b += '(i32.xor (i32.const 0xF))\n'
      b += 'i32.add\n'
    elif self.op ==  "'-'":
      b += '(i32.xor (i32.const 0xF))\n'
      b += 'i32.sub\n'
    elif self.op == "'*'":
      b += '''
      (local.set $temp (i32.shr_u))
      (i32.mul (i32.shr_u) (local.get $temp))
      '''
    else:
      assert False, f'unknown bif {op}'


  def to_wat(self, ctx):
    b = ''
    for arg in self.sargs:
      b += populate_stack_with(ctx, arg)

    b += self.make_test()

    b += pop(ctx, *self.darg)

    return b

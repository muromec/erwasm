from write.utils import push

class Ret:
  def __init__(self):
    pass

  def to_wat(self, ctx):
    b = ';; push X0 to stack\n'

    # Beam uses X0 as function result.
    # Put return registers to stack.
    b += push(ctx, 'x', 0)
    b += 'return\n'
    return b



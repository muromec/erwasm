from write.utils import push

# Not implemented yet
class Send:
  def __init__(self, *args):
    pass

  def to_wat(self, ctx):
    b = push(ctx, 'x', 1)
    b += ';; send \n'
    b += '(suspend $module_lib_fn_yield-i32)\n'

    return b

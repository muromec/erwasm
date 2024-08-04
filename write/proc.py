from write.utils import push, add_import

class Send:
  def __init__(self, *args):
    pass

  def to_wat(self, ctx):
    add_import(ctx, 'eractor', 'proc_send', 2)

    b = ';; send \n'
    b += push(ctx, 'x', 1)
    b += push(ctx, 'x', 0)
    b += '(call $eractor_proc_send_2)\n'

    return b

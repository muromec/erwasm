from write.utils import add_import

class Line:
  def __init__(self, info):
    if len(info) == 2:
      [scope, info] = info
    elif info:
      [info] = info

    if (info):
      [_loc, self.filename, self.linen] = info
      assert _loc == 'location'

    else:
      self.filename = None
      self.linen = None

  def to_wat(self, ctx):
    b = ''

    if self.filename:
      b += f';; original {self.filename} {self.linen}\n'

    if self.linen:
      b += f'(local.set $line (i32.const {self.linen}))\n'

    return b

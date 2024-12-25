from write.utils import add_import

class Line:
  def __init__(self, linen):
    self.filename = None
    self.linen = linen

  def to_wat(self, ctx):
    b = ''

    if self.filename:
      b += f';; original {self.filename} {self.linen}\n'

    if self.linen:
      b += f'(local.set $line (i32.const {self.linen}))\n'

    return b

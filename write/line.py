
class Line:
  def __init__(self, info):
    if (info):
      [_loc, [self.filename, self.linen]] = info[0]
      assert _loc == 'location'

    else:
      self.filename = None
      self.linen = None

  def to_wat(self, _ctx):
    if self.filename:
      return f';; original {self.filename} {self.linen}\n'

    return ''

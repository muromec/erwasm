from write.utils import populate_with

class Move:
  def __init__(self, source, dest):
    (dtyp, [dval]) = dest
    self.dtyp = dtyp
    self.dval = dval
    self.source = source

  def to_wat(self, ctx):
    return populate_with(ctx, self.dtyp, self.dval, self.source)

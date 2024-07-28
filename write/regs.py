from write.utils import move

class Allocate:
  def __init__(self, yreg, xreg):
    self.yreg = int(yreg)
    self.xreg = int(xreg)

  def to_wat(self, ctx):
    ctx.max_yregs = max(ctx.max_yregs, self.yreg)
    ctx.max_xregs = max(ctx.max_xregs, self.xreg)

    return ''


class Trim:
  def __init__(self, nremove, nleft):
    self.nremove = int(nremove)
    self.nleft = int(nleft)

  def to_wat(self, ctx):
    b = ''
    for yreg in range(0, self.nleft):
      b += move(ctx, 'y', yreg + self.nremove, 'y', yreg)

    return b


class VariableMetaNop:
  def __init__(self, *info):
    pass

  def to_wat(self, ctx):
    return ''


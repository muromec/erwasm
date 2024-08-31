from write.utils import move, push, pop

def arg(value):
  [typ, [num]] = value
  assert typ in ('x', 'y')
  return typ, int(num)

class Allocate:
  def __init__(self, yreg, xreg):
    self.yreg = int(yreg)
    self.xreg = int(xreg)

  def to_wat(self, ctx):
    ctx.max_yregs = max(ctx.max_yregs, self.yreg + 1)
    ctx.max_xregs = max(ctx.max_xregs, self.xreg + 1)

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

class Swap:
  def __init__(self, sarg, darg):
    self.sreg = arg(sarg)
    self.dreg = arg(darg)

  def to_wat(self, ctx):
    return f'''
    { push(ctx, *self.sreg) }
    (local.set $temp)
    { push(ctx, *self.dreg) }
    { pop(ctx, *self.sreg) }

    (local.get $temp)
    { pop(ctx, *self.dreg) }
    '''

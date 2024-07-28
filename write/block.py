
class Label:
  def __init__(self, fnumber):
    self.fnumber = int(fnumber)

  def to_wat(self, ctx):
    b = f';; label f{self.fnumber}, deep {ctx.depth}\n'
    b += f') ;; end of depth {ctx.depth}\n'

    ctx.depth += 1

    return b

class FuncInfo:
  def __init__(self, *args):
    pass

  def to_wat(self, ctx):
    return 'unreachable ;; func info trap\n'


class BadMatch:
  def __init__(self, *args):
    pass

  def to_wat(self, ctx):
    return 'unreachable ;; badmatch trap\n'



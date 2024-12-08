
class Jump:
  def __init__(self, dest):
    [_f, fnumber] = dest
    assert _f == 'f'
    self.fnumber = fnumber

  def to_wat(self, ctx):
    jump = self.fnumber

    jump_depth = ctx.labels_to_idx.index(jump)

    b = f' ;; unconditional jump to {jump}\n'
    b += f'(local.set $jump (i32.const {jump_depth}));; to label {jump}\n'
    b += f'(br $start)\n'

    return b


from write.utils import populate_stack_with

class SelectVal:
  def __init__(self, sarg, dest, value_table):
    [_f, [fnumber]] = dest
    assert _f == 'f'
    [_l, [comp_table]] = value_table
    assert _l == 'list'

    self.fnumber = fnumber
    self.sarg = sarg
    self.dest = dest
    self.comp_table = comp_table

  def to_wat(self, ctx):
    comp_table = self.comp_table[:]

    b = f';; select_val default target is {self.fnumber} \n'

    while comp_table:
      value = comp_table.pop(0)
      [_f, [jump]] = comp_table.pop(0)

      jump_depth = ctx.labels_to_idx.index(jump)
      b += f'(local.set $jump (i32.const {jump_depth}));; to label {jump}\n'

      b += populate_stack_with(ctx, self.sarg)
      b += populate_stack_with(ctx, value)

      b += '(i32.eq) (br_if $start)\n'

    jump_depth = ctx.labels_to_idx.index(self.fnumber)
    b += f'(local.set $jump (i32.const {jump_depth}));; to label {self.fnumber}\n'
    b += '(br $start)\n'

    return b

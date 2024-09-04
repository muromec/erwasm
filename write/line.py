from write.utils import add_import

class Line:
  def __init__(self, info):
    if len(info) == 2:
      [scope, info] = info
    elif info:
      [info] = info

    if (info):
      [_loc, [self.filename, self.linen]] = info
      assert _loc == 'location'

    else:
      self.filename = None
      self.linen = None

  def to_wat(self, ctx):
    add_import(ctx, 'minibeam', 'trace', 3)

    b = ''

    if self.filename:
      b += f';; original {self.filename} {self.linen}\n'

    if self.filename and self.linen:
      # if line number doesnt fit four digits, you are not my friend
      line_erl_digits = [
        (self.linen % 10000) // 1000,
        (self.linen % 1000) // 100,
        (self.linen % 100) // 10,
        (self.linen % 10),
      ]
      while not line_erl_digits[0]: line_erl_digits.pop(0)

      line_erl = 0
      for digit in reversed(line_erl_digits):
        line_erl = line_erl << 8 | (digit + 0x30)

      b += f'''
      (call $minibeam_trace_3
        (global.get $__{ctx.module_name_const}__literal_ptr_raw)
        (i32.const {line_erl})
        (global.get $__trace_enable)
      ) (drop)
      '''

    return b

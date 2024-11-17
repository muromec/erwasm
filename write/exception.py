from write.utils import add_import, pop, push, arg


class Try:
  def __init__(self, exreg, fail_dest):
    self.exreg = arg(exreg)
    [_f, [fnumber]] = fail_dest
    assert _f == 'f'
    self.fnumber = fnumber

  def to_wat(self, ctx):
    jump = self.fnumber

    jump_depth = ctx.labels_to_idx.index(jump)
    assert not (jump_depth is None)

    add_import(ctx, 'minibeam', 'tuple_alloc', 1)

    pop_ex = pop(ctx, *self.exreg)

    return f'''
      ;; start try catch block
      (call $minibeam_tuple_alloc_1 (i32.const 2))
      (global.set $__unique_exception)

      (global.get $__unique_exception)
      {pop_ex}

      (local.set $exception_h (i32.const {jump_depth}));; handler is at {jump}
    '''


class TryEnd:
  def __init__(self, exreg):
    self.exreg = arg(exreg)

  def to_wat(self, ctx):
    pop_ex = pop(ctx, *self.exreg)

    return f'''
      ;; end of the section covered by critical handler
      (i32.const 0)
      {pop_ex}
      (global.set $__unique_exception (i32.const 0))
      (local.set $exception_h (i32.const 0))
    '''

class TryCase:
  # This reads global exception info and puts
  # it into x 0 and x 1 (implicit)
  def __init__(self, exreg):
    self.exreg = arg(exreg)

  def to_wat(self, ctx):
    push_ex = push(ctx, *self.exreg)

    return f'''
        ;; start of exception handlers try_case
        (global.set $__unique_exception (i32.const 0))
        (local.set $exception_h (i32.const 0))

        { push_ex } ;; exc reg has raw mem pointer in it
        (i32.load) ;; read tuple from offset
        (i32.and (i32.const 0x3f))

        (if
          (i32.eqz) ;; is tuple
          (then
            {push_ex}
            (i32.const 4) ;; first element is exc type
            (i32.add)
            (i32.load) ;; load first el
            {pop(ctx, 'x', 0)}

            {push_ex}
            (i32.const 8) ;; second element is exc reason
            (i32.add)
            (i32.load) ;; load first el
            {pop(ctx, 'x', 1)}
          )
          (else ;; not a tuple
            (unreachable)
          )
        )

        ;; end of reading exception info
      '''

class TryCaseEnd:
  def __init__(self, exreg):
    # WARN: this exreg is not the same one where we allocated
    # exception handler to in Try..
    # This seems to cleanup implicit reads to x 0 and x 1
    # but only mentions one of them
    self.exreg = arg(exreg)

  def to_wat(self, ctx):
    pop_ex = pop(ctx, *self.exreg)

    return f'''
      ;; end of the try_case section
      (i32.const 0)
      {pop_ex}


    '''

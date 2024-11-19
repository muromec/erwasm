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

    add_import(ctx, 'minibeam', 'alloc', 2)

    pop_ex = pop(ctx, *self.exreg)

    return f'''
      ;; start try catch block
      (global.get $__unique_exception__literal_ptr_raw)
      (local.set $temp)
      (call $minibeam_alloc_2 (i32.const 4) (i32.const 16))
      (global.set $__unique_exception__literal_ptr_raw)

      (i32.store
        (i32.add
          (global.get $__unique_exception__literal_ptr_raw)
          (i32.const 8)
        )
        (local.get $temp)
      )

      (global.get $__unique_exception__literal_ptr_raw)
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

      (i32.load
        (i32.add
          (global.get $__unique_exception__literal_ptr_raw)
          (i32.const 8)
        )
      )
      (local.set $temp)

      (i32.store
        (global.get $__unique_exception__literal_ptr_raw)
        (i32.const 0)
      )

      (i32.store
        (i32.add
          (global.get $__unique_exception__literal_ptr_raw)
          (i32.const 4)
        )
        (i32.const 0)
      )

      (i32.store
        (i32.add
          (global.get $__unique_exception__literal_ptr_raw)
          (i32.const 8)
        )
        (i32.const 0)
      )
      (global.set $__unique_exception__literal_ptr_raw (local.get $temp))

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
        { push_ex } ;; exc reg has raw mem pointer in it
        (i32.load) ;; load first el
        {pop(ctx, 'x', 0)}

        {push_ex}
        (i32.const 4) ;; second element is exc reason
        (i32.add)
        (i32.load) ;; load first el
        {pop(ctx, 'x', 1)}

        ;; clear exception info
        (i32.load
          (i32.add
            (global.get $__unique_exception__literal_ptr_raw)
            (i32.const 8)
          )
        )
        (local.set $temp)

        (i32.store
          (global.get $__unique_exception__literal_ptr_raw)
          (i32.const 0)
        )

        (i32.store
          (i32.add
            (global.get $__unique_exception__literal_ptr_raw)
            (i32.const 4)
          )
          (i32.const 0)
        )

        (i32.store
          (i32.add
            (global.get $__unique_exception__literal_ptr_raw)
            (i32.const 8)
          )
          (i32.const 0)
        )
        (global.set $__unique_exception__literal_ptr_raw (local.get $temp))

      (local.set $exception_h (i32.const 0))
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

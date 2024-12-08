from write.utils import push, pop, add_import, arg, populate_stack_with, arg


class GetList:
  def __init__(self, sarg, darg_h, darg_t):
    self.sarg = arg(sarg)
    self.darg_h = arg(darg_h)
    self.darg_t = arg(darg_t)
    
  def to_wat(self, ctx):
    push_src = push(ctx, *self.sarg)
    pop_head = pop(ctx, *self.darg_h)
    pop_tail = pop(ctx, *self.darg_t)

    return f'''
      ;; get_list
      (block $get_list
      { push_src }
      (i32.and (i32.const 3))
      (if
        (i32.eq (i32.const 2)) ;; mem ref
        (then
          { push_src }
          (i32.shr_u (i32.const 2))
          (local.set $temp) ;; this hold reference of list head
          
          ;; try 
          (i32.load (local.get $temp))
          (i32.and (i32.const 3))
          (if (i32.eq (i32.const 1))
            (then
              (i32.load (i32.add (i32.const 4) (local.get $temp)))
              { pop_head } ;; head

              (i32.load (local.get $temp))
              (i32.xor (i32.const 3))
              { pop_tail }
              (br $get_list) ;; return ref to next element
            )
          )


          (i32.load (local.get $temp))
          (if
            (i32.eq (i32.const 0x3b))
            (then
              (i32.const 0x3b)
              { pop_tail }
              (br $get_list) ;; return nil atom
            )
          )
        )
      ) ;; end of get_list
      (unreachable)
      )
      '''

class GetHead:
  def __init__(self, sarg, darg_h):
    self.sarg = arg(sarg)
    self.darg_h = arg(darg_h)
    
  def to_wat(self, ctx):
    push_src = push(ctx, *self.sarg)
    pop_head = pop(ctx, *self.darg_h)

    return f'''
      ;; get_head
      (block $head

      ;; validate mem ref
      { push_src }
      (i32.and (i32.const 3))
      (i32.eq (i32.const 2)) ;; mem ref
      (if (i32.eqz) (then (unreachable)))

      { push_src }
      (i32.shr_u (i32.const 2))
      (local.set $temp) ;; this hold reference of list head

      ;; check for empty list
      (i32.load (local.get $temp))
      (if
        (i32.eq (i32.const 0x3b) )
        (then
          (i32.const 0x3b)
          { pop_head } ;; head
          (br $head)
        )
      )

      ;; load value from offset
      (i32.load (local.get $temp))
      (i32.and (i32.const 3))
      (if
        (i32.eq (i32.const 1))
        (then
          (i32.load (i32.add (i32.const 4) (local.get $temp)))
          { pop_head } ;; head
          (br $head)
        )
      )

      (unreachable)
      ) ;; end of get_head
      '''

class GetTail:
  def __init__(self, sarg, darg_t):
    self.sarg = arg(sarg)
    self.darg_t = arg(darg_t)
    
  def to_wat(self, ctx):
    push_src = push(ctx, *self.sarg)
    pop_tail = pop(ctx, *self.darg_t)

    return f'''
      ;; get_tail
      (block $get_tail
      { push_src }
      (i32.and (i32.const 3))
      (if
        (i32.eq (i32.const 2)) ;; mem ref
        (then
          { push_src }
          (i32.shr_u (i32.const 2))
          (local.set $temp) ;; this hold reference of list head
          
          ;; try 
          (i32.load (local.get $temp))
          (i32.and (i32.const 3))
          (if (i32.eq (i32.const 1))
            (then
              (i32.load (local.get $temp))
              (i32.xor (i32.const 3))
              { pop_tail }
              (br $get_tail) ;; return ref to next element
            )
          )

          (i32.load (local.get $temp))
          (if
            (i32.eq (i32.const 0x3b))
            (then
              (i32.const 0x3b)
              { pop_tail }
              (br $get_tail) ;; return nil atom
            )
          )
        )
      ) ;; end of get_tail
      (unreachable)
      )
      '''

class PutList:
  def __init__(self, head, tail, dreg):
    self.head = head
    self.tail = tail
    self.dreg = arg(dreg)

  def to_wat(self, ctx):
    add_import(ctx, 'minibeam', 'list_put', 2)

    b = ';; put_list\n'

    b += populate_stack_with(ctx, self.head)
    b += populate_stack_with(ctx, self.tail)

    return b + f'''
      (call $minibeam_list_put_2)
      { pop(ctx, *self.dreg) }
    '''

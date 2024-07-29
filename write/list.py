from write.utils import push, pop

def arg(value):
  [typ, [num]] = value
  assert typ in ('x', 'y')
  return typ, int(num)


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

              (i32.add
                (i32.shr_u
                  (i32.load (local.get $temp))
                  (i32.const 2)
                )
                (local.get $temp)
              )
              (i32.const 2)
              (i32.shl)
              (i32.or (i32.const 2))
              { pop_tail }
              (br $get_list) ;; return ref to next element
            )
          )

          (i32.load (local.get $temp))
          (i32.and (i32.const 3))

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
      ;; get_list
      { push_src }
      (i32.and (i32.const 3))
      (if
        (i32.eq (i32.const 2)) ;; mem ref
        (then
          { push_src }
          (i32.shr_u (i32.const 2))
          (local.set $temp) ;; this hold reference of list head
          (i32.load (local.get $temp))
          (i32.and (i32.const 3))
          (if (i32.eq (i32.const 1))
            (then
              (i32.load (i32.add (i32.const 4) (local.get $temp)))
              { pop_head } ;; head
            )
            (else
              (unreachable)
            )
          )
        )
        (else
          (unreachable)
        )
      ) ;; end of get_list
      '''

class GetTail:
  def __init__(self, sarg, darg_t):
    self.sarg = arg(sarg)
    self.darg_t = arg(darg_t)
    
  def to_wat(self, ctx):
    push_src = push(ctx, *self.sarg)
    pop_tail = pop(ctx, *self.darg_t)

    return f'''
      ;; get_list
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
              (i32.add
                (i32.shr_u
                  (i32.load (local.get $temp))
                  (i32.const 2)
                )
                (local.get $temp)
              )
              (i32.const 2)
              (i32.shl)
              (i32.or (i32.const 2))
              { pop_tail }
              (br $get_tail) ;; return ref to next element
            )
          )

          (i32.load (local.get $temp))
          (i32.and (i32.const 3))

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


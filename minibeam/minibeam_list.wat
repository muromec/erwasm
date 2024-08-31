(module

  (import "erdump" "alloc" (func $alloc (param i32 i32) (result i32)))
  (import "erdump" "hexlog_1" (func $hexlog (param i32) (result i32)))

  (func $put_list (param $head i32) (param $tail i32) (result i32)
    (local $ret i32)
    (local $ptr i32)
    (local $tail_ptr i32)
    (local $temp i32)

    ;; if tail is a mem pointer, load it
    (if (i32.eq (i32.and (local.get $tail) (i32.const 3)) (i32.const 2))
      (then
        (local.set $tail_ptr (i32.shr_u (local.get $tail) (i32.const 2)))
        (i32.load (local.get $tail_ptr))
        (local.set $tail)
      )
    )

    (block $switch
      (if
        ;; if we have nil, alloc four words
        (i32.eq (local.get $tail) (i32.const 0x3b))
        (then
          (call $alloc (i32.const 4) (i32.const 16))
          (local.set $ptr)
          (local.set $ret (local.get $ptr))
          (local.set $tail_ptr (i32.add (local.get $ptr) (i32.const 8)))

          (i32.shl (local.get $tail_ptr) (i32.const 2))
          (i32.or (i32.const 1))
          (local.set $tail)

          ;; 0
          (i32.store (local.get $ptr) (local.get $tail))
          (local.set $ptr (i32.add (i32.const 4) (local.get $ptr)))

          (i32.store (local.get $ptr) (local.get $head)) ;; 1
          (local.set $ptr (i32.add (i32.const 4) (local.get $ptr)))

          (i32.store (local.get $ptr) (i32.const 0x3b)) ;; 2
          (br $switch)
        )
      )
      ;; if we have array pointer
      (if (i32.eq (i32.and (local.get $tail) (i32.const 3)) (i32.const 1))
        (then
          (call $alloc (i32.const 4) (i32.const 8))
          (local.set $ptr)
          (local.set $ret (local.get $ptr))

          (i32.shl (local.get $tail_ptr) (i32.const 2))
          (i32.or (i32.const 1))
          (local.set $tail)

          ;; 0
          (i32.store (local.get $ptr) (local.get $tail))
          (local.set $ptr (i32.add (i32.const 4) (local.get $ptr)))

          (i32.store (local.get $ptr) (local.get $head)) ;; 1
          (br $switch)
        )
      )
      (unreachable)
    )

    (i32.or (i32.shl (local.get $ret) (i32.const 2)) (i32.const 2))
  )
  (export "minibeam#list_put_2" (func $put_list))

  (func $reverse_1 (param $arg i32) (result i32)
    (local $ret i32)
    (local $ptr i32)
    (local $in_ptr i32)
    (local $temp i32)
    (local $tail i32)

    (i32.eq (local.get $arg) (i32.const 0x3b))
    (if
      (then
        (return (i32.const 0x3b))
      )
    )

    ;; check its a mem pointer
    (if (i32.eq (i32.and (local.get $arg) (i32.const 3)) (i32.const 2))
      (then
        (local.get $arg)
        (i32.shr_u (i32.const 2))
        (local.set $in_ptr)
      )
      (else
        (unreachable)
      )
    )

    ;; empty list is a reversed() of itself
    (if (i32.eq (i32.load (local.get $in_ptr)) (i32.const 0x3b))
      (then
        (return (local.get $arg))
      )
    )

    (call $alloc (i32.const 4) (i32.const 8))
    (local.set $ptr)

    ;; start with writing the end marker
    (i32.store (local.get $ptr) (i32.const 0x3b))
    (i32.store (i32.add (local.get $ptr) (i32.const 4)) (i32.const 0))
    (local.set $tail
      (i32.or
        (i32.shl (local.get $ptr) (i32.const 2))
        (i32.const 1)
      )
    )

    (block $out
    (loop $iter
      (i32.load (local.get $in_ptr))
      (if (i32.eq (i32.const 0x3b))
          (then (br $out))
      )

      ;; read current element
      (i32.load (i32.add (local.get $in_ptr) (i32.const 4)))
      (local.set $temp)

      (call $alloc (i32.const 4) (i32.const 8))
      (local.set $ptr)

      (i32.store (local.get $ptr) (local.get $tail))
      (i32.store (i32.add (local.get $ptr) (i32.const 4)) (local.get $temp))

      ;; form new tail pointer
      (local.set $tail
        (i32.or
          (i32.shl (local.get $ptr) (i32.const 2))
          (i32.const 1)
        )
      )

      ;; load tail pointer of input list
      (i32.load (local.get $in_ptr))
      (i32.shr_u (i32.const 2))
      (local.set $in_ptr)
      (br $iter)
    )
    )

    (local.get $tail)
    (i32.xor (i32.const 3))
  )
  (export  "lists#reverse_1" (func $reverse_1))

)

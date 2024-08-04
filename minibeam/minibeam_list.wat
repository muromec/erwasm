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
          (local.set $tail_ptr (i32.add (local.get $tail_ptr) (i32.const 8)))

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

)

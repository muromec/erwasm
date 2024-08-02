(module

  (import "erdump" "alloc" (func $alloc (param i32 i32) (result i32)))
  (import "erdump" "hexlog_1" (func $hexlog (param i32) (result i32)))

  (func $put_list (param $head i32) (param $tail i32) (result i32)
    (local $ret i32)
    (local $ptr i32)
    (local $tail_ptr i32)

    
    (if 
      (i32.eq (local.get $tail) (i32.const 0x3b))
      (then
        (call $alloc (i32.const 4) (i32.const 16))
        (local.set $ptr)
        (local.set $ret (local.get $ptr))

        (i32.store ;; 0
          (local.get $ptr)
          ;; list pointer to skip over next 4 bytes
          (i32.or (i32.shl (i32.const 4) (i32.const 2)) (i32.const 1))
        )
        (local.set $ptr (i32.add (i32.const 4) (local.get $ptr)))

        (i32.store (local.get $ptr) (local.get $head)) ;; 1
        (local.set $ptr (i32.add (i32.const 4) (local.get $ptr)))

        (i32.store (local.get $ptr) (i32.const 0x3b)) ;; 2
      )
      (else
        (unreachable)
      )
    )

    (i32.or (i32.shl (local.get $ret) (i32.const 2)) (i32.const 2))
  )

  (export "minibeam#list_put_2" (func $put_list))

)

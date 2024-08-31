(module

  (import "erdump" "alloc" (func $alloc (param i32 i32) (result i32)))
  (import "erdump" "hexlog_1" (func $hexlog (param i32) (result i32)))
  (memory 0)

  (func $tuple_alloc (param $size i32) (result i32)
    (local $ptr i32)
    (local $temp i32)

    ;; memory size
    (i32.mul (local.get $size) (i32.const 4))
    (i32.add (i32.const 4))
    (local.set $temp)

    (call $alloc (i32.const 4) (local.get $temp))
    (local.set $ptr)

    (i32.store ;; 0
      (local.get $ptr)
      ;; tag is 0 zeros, then length in words
      (i32.shl (local.get $size) (i32.const 6))
    )
    (local.get $ptr)
  )

  (export "minibeam#tuple_alloc_1" (func $tuple_alloc))
)

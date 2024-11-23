(module
  (import "__internal" "alloc" (func $alloc (param i32 i32) (result i32)))
  (memory 0)

  (func $fn_alloc (param $fnum i32) (param $args i32) (result i32)
    (local $ptr i32)
    (local $temp i32)

    ;; memory size 4 * (args num  + 2)
    (i32.mul (local.get $args) (i32.const 4))
    (i32.add (i32.const 8))
    (local.set $temp)

    (call $alloc (i32.const 4) (local.get $temp))
    (local.set $ptr)

    (i32.store
      (local.get $ptr)
      (i32.or
        (i32.const 0x14)
        (i32.shl
          (local.get $fnum)
          (i32.const 6)
        )
      )
    )

    (i32.store
      (i32.add
        (local.get $ptr) (i32.const 4)
      )
      (local.get $args)
    )
    (local.get $ptr)
  )

  (export "__internal#fn_alloc_2" (func $fn_alloc))
)

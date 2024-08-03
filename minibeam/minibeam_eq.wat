(module
  (import "erdump" "hexlog_1" (func $hexlog (param i32) (result i32)))

  (func $test_eq_exact_tuple (param $ptr_a i32) (param $head_a i32) (param $ptr_b i32) (param $head_b i32) (result i32)
    (local $size i32)

    (if (i32.eq (local.get $head_a) (local.get $head_b))
      (then)
      (else (return (i32.const 0)))
    )
    (local.set $size (i32.shr_u (local.get $head_a) (i32.const 6)))

    (i32.shr_u (local.get $ptr_a) (i32.const 2))
    (local.set $ptr_a)
    (i32.shr_u (local.get $ptr_b) (i32.const 2))
    (local.set $ptr_b)
    
    (if (i32.eqz (local.get $size))
      (then (return (i32.const 1)))
    )

    (loop $elements
      (local.set $ptr_a (i32.add (local.get $ptr_a) (i32.const 4)))
      (local.set $ptr_b (i32.add (local.get $ptr_b) (i32.const 4)))

      (call $test_eq_exact
        (i32.load (local.get $ptr_a))
        (i32.load (local.get $ptr_b))
      )
      (if (i32.eqz)
        (then 
          (return (i32.const 0))
        )
      )

      (local.set $size (i32.sub (local.get $size) (i32.const 1)))
      (if (local.get $size) (then (br $elements)))
    )

    (i32.const 1)
  )

  (func $test_eq_exact (param $value_a i32) (param $value_b i32) (result i32)
    (local $tag_a i32)
    (local $tag_b i32)
    (local $head_a i32)
    (local $head_b i32)


    (if (i32.eq (local.get $value_a) (local.get $value_b))
      (then (return (i32.const 1)))
    )

    ;; load a if needed
    (if (i32.eq (i32.and (local.get $value_a) (i32.const 3)) (i32.const 2))
      (then
        (i32.shr_u (local.get $value_a) (i32.const 2))
        (i32.load)
        (local.set $head_a)
      )
      (else
        (return (i32.const 0))
      )
    )

    ;; load b if needed
    (if (i32.eq (i32.and (local.get $value_b) (i32.const 3)) (i32.const 2))
      (then
        (i32.shr_u (local.get $value_b) (i32.const 2))
        (i32.load)
        (local.set $head_b)
      )
      (else
        (return (i32.const 0))
      )
    )

    (local.set $tag_a (i32.and (i32.const 0x3f) (local.get $head_a)))
    (local.set $tag_b (i32.and (i32.const 0x3f) (local.get $head_b)))

    (if (i32.eq (local.get $tag_a) (local.get $tag_b))
      (then)
      (else (return (i32.const 0)))
    )

    (if (i32.eq (local.get $tag_a) (i32.const 0))
      (then 
        (return
          (call $test_eq_exact_tuple 
            (local.get $value_a) (local.get $head_a)
            (local.get $value_b) (local.get $head_b)
          )
        )
      )
    )

    (i32.const 0)
  )

  (export "minibeam#test_eq_exact_2" (func $test_eq_exact))

)

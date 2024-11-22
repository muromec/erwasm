(module
  (import "__internal" "is_mem_ptr_1" (func $is_mem_ptr (param i32) (result i32)))

  (memory 0)

  (func $test_eq_helper (param $ptr_a i32) (param $ptr_b i32) (result i32)
    (local $element_a i32)
    (local $element_b i32)

    (i32.load (local.get $ptr_a))
    (local.set $element_a)

    (if
      (i32.eqz (i32.and (local.get  $element_a) (i32.const 0x3F)))
      (then
        (i32.shl (local.get $ptr_a) (i32.const 2))
        (i32.or (i32.const 2))
        (local.set $element_a)
      )
    )

    (i32.load (local.get $ptr_b))
    (local.set $element_b)
    (if
      (i32.eqz (i32.and (local.get  $element_b) (i32.const 0x3F)))
      (then
        (i32.shl (local.get $ptr_b) (i32.const 2))
        (i32.or (i32.const 2))
        (local.set $element_b)
      )
    )

    (call $test_eq_exact (local.get $element_a) (local.get $element_b))
  )

  (func $test_eq_exact_list (param $ptr_a i32) (param $head_a i32) (param $ptr_b i32) (param $head_b i32) (result i32)
    (local.set $ptr_a (i32.shr_u (local.get $ptr_a) (i32.const 2)))
    (local.set $ptr_b (i32.shr_u (local.get $ptr_b) (i32.const 2)))

    (loop $elements
      (call $test_eq_helper
        (i32.add (local.get $ptr_a) (i32.const 4))
        (i32.add (local.get $ptr_b) (i32.const 4))
      )
      (if (i32.eqz)
        (then
          (return (i32.const 0))
        )
      )
      ;; check end marker
      (if (i32.eq (local.get $head_a) (i32.const 0x3b))
        (then (nop))
        (else
          (i32.shr_u (local.get $head_a) (i32.const 2))
          (local.set $ptr_a)
          (local.set $head_a (i32.load (local.get $ptr_a)))

          (i32.shr_u (local.get $head_b) (i32.const 2))
          (local.set $ptr_b)
          (local.set $head_b (i32.load (local.get $ptr_b)))
          (br $elements)
        )
      )
    )

    (i32.const 1)
  )


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

  (func $test_eq_exact_buffer (param $ptr_a i32) (param $ptr_b i32) (result i32)
    (local $size_a i32)
    (local $size_b i32)

    (i32.add (i32.const 4) (local.get $ptr_a))
    (i32.load)
    (local.set $size_a) ;; in bits

    (i32.add (i32.const 4) (local.get $ptr_b))
    (i32.load)
    (local.set $size_b) ;; in bits


    (if (i32.eq (local.get $size_a) (local.get $size_b))
        (then)
        (else
          (return (i32.const 0))
        )
    )
    (i32.shr_u (local.get $size_a) (i32.const 3))
    (local.set $size_a) ;; in bytes

    (local.set $ptr_a (i32.add (local.get $ptr_a) (i32.const 8)))
    (local.set $ptr_b (i32.add (local.get $ptr_b) (i32.const 8)))

    (loop $elements
      (if (i32.eqz (local.get $size_a))
          (then (return (i32.const 1)))
      )

      (i32.load8_u (local.get $ptr_a))
      (i32.load8_u (local.get $ptr_b))

      (if (i32.eq)
        (then (nop))
        (else
          (return (i32.const 0))
        )
      )

      (local.set $ptr_a (i32.add (local.get $ptr_a) (i32.const 1)))
      (local.set $ptr_b (i32.add (local.get $ptr_b) (i32.const 1)))
      (local.set $size_a (i32.sub (local.get $size_a) (i32.const 1)))
      (br $elements)
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
    (if (call $is_mem_ptr (local.get $value_a))
      (then
        (i32.shr_u (local.get $value_a) (i32.const 2))
        (i32.load)
        (local.set $head_a)
      )
      (else
        (local.set $head_a (local.get $value_a))
      )
    )

    ;; load b if needed
    (if (call $is_mem_ptr (local.get $value_a))
      (then
        (i32.shr_u (local.get $value_b) (i32.const 2))
        (i32.load)
        (local.set $head_b)
      )
      (else
        (local.set $head_b (local.get $value_b))
      )
    )

    (local.set $tag_a (i32.and (i32.const 0x3f) (local.get $head_a)))
    (local.set $tag_b (i32.and (i32.const 0x3f) (local.get $head_b)))

    (if (i32.eq (local.get $tag_a) (local.get $tag_b))
      (then
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
      )
    )

    (if (i32.eq (local.get $tag_a) (local.get $tag_b))
      (then
        (if (i32.eq (local.get $tag_a) (i32.const 0x24))
          (then
            (return
              (call $test_eq_exact_buffer
                (i32.shr_u (local.get $value_a) (i32.const 2))
                (i32.shr_u (local.get $value_b) (i32.const 2))
              )
            )
          )
        )
      )
    )

    (local.set $tag_a (i32.and (i32.const 0x3) (local.get $head_a)))
    (local.set $tag_b (i32.and (i32.const 0x3) (local.get $head_b)))


    (if (i32.eq (local.get $tag_a) (local.get $tag_b))
      (then
        (if (i32.eq (local.get $tag_a) (i32.const 1))
          (then
            (return
              (call $test_eq_exact_list
                (local.get $value_a) (local.get $head_a)
                (local.get $value_b) (local.get $head_b)
              )
            )
          )
        )
      )
    )


    (i32.const 0)
  )

  (export "minibeam#test_eq_exact_2" (func $test_eq_exact))

)

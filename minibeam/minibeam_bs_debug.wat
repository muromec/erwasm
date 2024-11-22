(module
  (import "minibeam" "display_1" (func $display (param i32) (result i32)))
  (import "minibeam" "is_mem_ptr_1" (func $is_mem_ptr (param i32) (result i32)))
  (memory 0)

  (func $bs_debug (param $ctx i32) (result i32)
    (local $ptr i32)
    (local $bin_ptr i32)
    (local $size i32)
    (local $offset i32)

    (if (call $is_mem_ptr (local.get $ctx))
        (then nop)
        (else unreachable)
    )
    (local.set $ptr (i32.shr_u (local.get $ctx) (i32.const 2)))

    (i32.load (local.get $ptr))
    (i32.and (i32.const 0x3F))
    (if (i32.eq (i32.const 4)) ;; has to be match ctx
        (then nop)
        (else unreachable)
    )

    (i32.load (i32.add (local.get $ptr) (i32.const 4)))
    (local.set $bin_ptr)

    (if (call $is_mem_ptr (local.get $bin_ptr))
        (then nop)
        (else unreachable)
    )
    (local.set $bin_ptr (i32.shr_u (local.get $bin_ptr) (i32.const 2)))

    (i32.load (i32.add (local.get $ptr) (i32.const 8)))
    (local.set $offset)

    (i32.load (local.get $bin_ptr))
    (i32.and (i32.const 0x3F))
    (if (i32.eq (i32.const 0x24)) ;; has to be heap binary
        (then nop)
        (else unreachable)
    )
    (i32.load (i32.add (local.get $bin_ptr) (i32.const 4)))
    (local.set $size)

    (call
      $display
      (i32.or
        (i32.shl (global.get $__0__literal_ptr_raw) (i32.const 2))
        (i32.const 2)
      )
    ) (drop)

    (i32.const 1)
  )
  (export "minibeam#bs_debug_1" (func $bs_debug))
)

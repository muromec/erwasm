(module

  (import "erdump" "alloc" (func $alloc (param i32 i32) (result i32)))
  (import "erdump" "hexlog_1" (func $hexlog (param i32) (result i32)))
  (import "erdump" "write_buf" (func $make_erl_buf (param i32 i32) (result i32)))

  ;; inlie the two below
  (func $i16_flip (param $value i32) (result i32)
    (i32.or
      (i32.shr_u (local.get $value) (i32.const 8))
      (i32.and (i32.shl (local.get $value) (i32.const 8)) (i32.const 0xFF00))
    )
  )

  (func $i32_flip (param $value i32) (result i32)
    (i32.or
      (i32.or
        (i32.shr_u (local.get $value) (i32.const 24))
        (i32.and (
          i32.shr_u (local.get $value) (i32.const 8)) (i32.const 0xFF_00)
        )
      )
      (i32.or
        (i32.and (
          i32.shl (local.get $value) (i32.const 8)) (i32.const 0xFF_00_00)
        )
        (i32.and 
          (i32.shl (local.get $value) (i32.const 24)) (i32.const 0xFF_00_00_00)
        )
      )
    )
  )

  (func $make_match_context (param $mem i32) (param $offset i32) (result i32)
    (local $ptr i32)
    (local $ret i32)

    (if (i32.eq (i32.and (local.get $mem) (i32.const 2)) (i32.const 2))
        (then nop)
        (else unreachable)
    )
    (i32.load (i32.shr_u (local.get $mem) (i32.const 2)))
    (i32.and (i32.const 0x3F))

    ;; reufe existing context
    (if (i32.eq (i32.const 4))
      (then
        (return (local.get $mem))
      )
    )

    (local.set $ptr (call $alloc (i32.const 4) (i32.const 16)))
    (local.set $ret (local.get $ptr))

    ;; write header
    (i32.store (local.get $ptr) (i32.const 0x04)) ;; 0 tag match context
    (local.set $ptr (i32.add (i32.const 4) (local.get $ptr)))

    (i32.store (local.get $ptr) (local.get $mem)) ;; 1 binary ref
    (local.set $ptr (i32.add (i32.const 4) (local.get $ptr)))

    (i32.store (local.get $ptr) (local.get $offset)) ;; 2 offset
    (local.set $ptr (i32.add (i32.const 4) (local.get $ptr)))

    (i32.store (local.get $ptr) (i32.const 0x00)) ;; 3 saved state
    (local.set $ptr (i32.add (i32.const 4) (local.get $ptr)))

    (i32.or (i32.shl (local.get $ret) (i32.const 2)) (i32.const 2))
  )
  (export "minibeam#make_match_context_1" (func $make_match_context))

  (func $bs_integer (param $ctx i32) (param $bits_number i32) (result i32)
    (local $ptr i32)
    (local $bin_ptr i32)
    (local $temp i32)
    (local $offset i32)

    (if (i32.eq (i32.and (local.get $ctx) (i32.const 2)) (i32.const 2))
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

    ;; offset is in bits
    (i32.load (i32.add (local.get $ptr) (i32.const 8)))
    (local.set $offset)

    (if (i32.eq (i32.and (local.get $bin_ptr) (i32.const 2)) (i32.const 2))
        (then nop)
        (else unreachable)
    )
    (local.set $bin_ptr (i32.shr_u (local.get $bin_ptr) (i32.const 2)))

    (i32.load (local.get $bin_ptr))
    (i32.and (i32.const 0x3F))
    (if (i32.eq (i32.const 0x24)) ;; has to be heap binary
        (then nop)
        (else unreachable)
    )
    (i32.add 
      (i32.shr_u (local.get $offset) (i32.const 3))
      (i32.add (local.get $bin_ptr) (i32.const 8))
    )
    (local.set $temp) ;; remember pointer

    ;; wasm doesnt have separate big endian and little instructions,
    ;; while beam has BE by default -> <<$A, $C>> is 0x4143
    ;; todo: inline this
    (block $load
      (if 
        (i32.eq (local.get $bits_number) (i32.const 8))
        (then
          (i32.load8_u (local.get $temp))
          (local.set $temp)
          (br $load)
        )
      )

      (if 
        (i32.eq (local.get $bits_number) (i32.const 16))
        (then
          (local.set $temp (call $i16_flip (i32.load16_u (local.get $temp))))
          (br $load)
        )
      )

      (if 
        (i32.eq (local.get $bits_number) (i32.const 32))
        (then
          (i32.load (local.get $temp))
          ;; this is fine
          ;; who uses big endian anyway, right? right?
          (local.set $temp (call $i32_flip (i32.load (local.get $temp))))
          (br $load)
        )
      )
      (unreachable)
    )

    (local.set $offset (i32.add (local.get $offset) (local.get $bits_number)))
    (i32.store (i32.add (local.get $ptr) (i32.const 8)) (local.get $offset))

    (local.get $temp)
  )
  (export "minibeam#bs_load_integer_1" (func $bs_integer))

  (func $bs_ensure_at_least (param $ctx i32) (param $unit_size_bits i32) (param $unit_round i32) (result i32)
    (local $ptr i32)
    (local $bin_ptr i32)
    (local $size i32)
    (local $offset i32)

    (if (i32.eq (i32.and (local.get $ctx) (i32.const 2)) (i32.const 2))
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

    (if (i32.eq (i32.and (local.get $bin_ptr) (i32.const 2)) (i32.const 2))
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

    ;; everything above this point should be part of bs_match
    ;; and done once.
    ;; the reason its not inlined -- op code writers cant declare
    ;; local variables right now
    ;; everything below this point should be inlined instead of making this call

    ;; the size is in bits, add offset in bits to it
    (local.set $size (i32.sub (local.get $size) (local.get $offset)))

    (i32.and
      (i32.ge_u (local.get $size) (local.get $unit_size_bits))
      (i32.eqz (i32.rem_u (local.get $size) (local.get $unit_round)))
    )
  )
  (export "minibeam#bs_ensure_at_least_2" (func $bs_ensure_at_least))

  (func $bs_ensure_exactly (param $ctx i32) (param $unit_size_bits i32) (result i32)
    (local $ptr i32)
    (local $bin_ptr i32)
    (local $size i32)
    (local $offset i32)

    (if (i32.eq (i32.and (local.get $ctx) (i32.const 2)) (i32.const 2))
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

    (if (i32.eq (i32.and (local.get $bin_ptr) (i32.const 2)) (i32.const 2))
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

    ;; everything above this point should be part of bs_match
    ;; and done once.
    ;; the reason its not inlined -- op code writers cant declare
    ;; local variables right now
    ;; everything below this point should be inlined instead of making this call

    ;; the size is in bits, add offset in bits to it
    (local.set $size (i32.sub (local.get $size) (local.get $offset)))

    (i32.eq (local.get $size) (local.get $unit_size_bits))
  )
  (export "minibeam#bs_ensure_exactly_1" (func $bs_ensure_exactly))


  (func $bs_skip (param $ctx i32) (param $bits_number i32) (result i32)
    (local $ptr i32)
    (local $bin_ptr i32)
    (local $temp i32)
    (local $offset i32)

    (if (i32.eq (i32.and (local.get $ctx) (i32.const 2)) (i32.const 2))
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

    ;; offset is in bits
    (i32.load (i32.add (local.get $ptr) (i32.const 8)))
    (local.set $offset)
    (local.set $offset (i32.add (local.get $offset) (local.get $bits_number)))
    (i32.store (i32.add (local.get $ptr) (i32.const 8)) (local.get $offset))

    (i32.const 1);
  )
  (export "minibeam#bs_skip_1" (func $bs_skip))

  (func $bs_get_position (param $ctx i32) (result i32)
    (local $ptr i32)
    (local $bin_ptr i32)
    (local $offset i32)

    (if (i32.eq (i32.and (local.get $ctx) (i32.const 2)) (i32.const 2))
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

    ;; offset is in bits
    (i32.load (i32.add (local.get $ptr) (i32.const 8)))
  )
  (export "minibeam#bs_get_position_0" (func $bs_get_position))


  (func $bs_set_position (param $ctx i32) (param $offset i32) (result i32)
    (local $ptr i32)
    (local $bin_ptr i32)

    (if (i32.eq (i32.and (local.get $ctx) (i32.const 2)) (i32.const 2))
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

    ;; offset is in bits
    (i32.store (i32.add (local.get $ptr) (i32.const 8)) (local.get $offset))
    (i32.const 1)
  )
  (export "minibeam#bs_set_position_1" (func $bs_set_position))

  (func $bs_get_binary (param $ctx i32) (param $read_size i32) (result i32)
    (local $ptr i32)
    (local $bin_ptr i32)
    (local $size i32)
    (local $offset i32)
    (local $ret i32)

    (if (i32.eq (i32.and (local.get $ctx) (i32.const 2)) (i32.const 2))
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

    (local.get $read_size)
    (i32.and (i32.const 0xF))
    (if (i32.eq (i32.const 0xF)) ;; has to be integer
        (then nop)
        (else unreachable)
    )
    (local.set $read_size
      (i32.shr_u (local.get $read_size) (i32.const 4))
    )

    (i32.load (i32.add (local.get $ptr) (i32.const 4)))
    (local.set $bin_ptr)

    (if (i32.eq (i32.and (local.get $bin_ptr) (i32.const 2)) (i32.const 2))
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

    ;; everything above this point should be part of bs_match
    ;; and done once.
    ;; the reason its not inlined -- op code writers cant declare
    ;; local variables right now
    ;; everything below this point should be inlined instead of making this call

    ;; the size is in bits, add offset in bits to it
    (local.set $size (i32.sub (local.get $size) (local.get $offset)))

    (call $make_erl_buf
      (i32.add
        (i32.shr_u (local.get $offset) (i32.const 3))
        (i32.add (local.get $bin_ptr) (i32.const 8))
      )
      (i32.shr_u (local.get $read_size) (i32.const 3))
    )
    (local.set $ret)
    (if
      (i32.eqz (local.get $ret))
      (then (return (i32.const 0)))
    )

    (local.set $offset (i32.add (local.get $offset) (local.get $read_size)))
    (i32.store (i32.add (local.get $ptr) (i32.const 8)) (local.get $offset))

    (local.get $ret)
  )

  (export "minibeam#get_binary_from_ctx_1" (func $bs_get_binary))

  (func $bs_get_tail (param $ctx i32) (result i32)
    (local $ptr i32)
    (local $bin_ptr i32)
    (local $size i32)
    (local $offset i32)
    (local $ret i32)

    (if (i32.eq (i32.and (local.get $ctx) (i32.const 2)) (i32.const 2))
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

    (if (i32.eq (i32.and (local.get $bin_ptr) (i32.const 2)) (i32.const 2))
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

    ;; everything above this point should be part of bs_match
    ;; and done once.
    ;; the reason its not inlined -- op code writers cant declare
    ;; local variables right now
    ;; everything below this point should be inlined instead of making this call

    ;; the size is in bits, add offset in bits to it
    (local.set $size (i32.sub (local.get $size) (local.get $offset)))

    (call $make_erl_buf
      (i32.add
        (i32.shr_u (local.get $offset) (i32.const 3))
        (i32.add (local.get $bin_ptr) (i32.const 8))
      )
      (i32.shr_u (local.get $size) (i32.const 3))
    )
    (local.set $ret)
    (if
      (i32.eqz (local.get $ret))
      (then (return (i32.const 0)))
    )

    (local.set $offset (i32.add (local.get $offset) (local.get $size)))
    (i32.store (i32.add (local.get $ptr) (i32.const 8)) (local.get $offset))

    (local.get $ret)
  )

  (export "minibeam#bs_get_tail_0" (func $bs_get_tail))

)

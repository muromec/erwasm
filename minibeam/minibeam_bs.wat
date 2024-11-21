(module

  (import "erdump" "alloc" (func $alloc (param i32 i32) (result i32)))
  (import "erdump" "hexlog_1" (func $hexlog (param i32) (result i32)))
  (import "erdump" "write_buf" (func $make_erl_buf (param i32 i32) (result i32)))
  (import "minibeam" "display_1" (func $display (param i32) (result i32)))
  (import "minibeam" "is_mem_ptr_1" (func $is_mem_ptr (param i32) (result i32)))
  (import "__internal" "flip_endian_1" (func $flip_endian (param i32) (result i32)))

  (data (i32.const 0) "\24\00\00\00\18\00\00\00\58\58\0a")
  (global $__0__literal_ptr_raw i32 (i32.const 0))
  (global $__free_mem i32 (i32.const 16))

  (memory 0)

  (func $make_match_context (param $mem i32) (param $offset i32) (result i32)
    (local $ptr i32)
    (local $ret i32)
    (local $value i32)

    (if (call $is_mem_ptr (local.get $mem))
      (then nop)
      (else (return (i32.const 0)))
    )
    (i32.load (i32.shr_u (local.get $mem) (i32.const 2)))
    (local.set $value)

    (local.get $value)
    (i32.and (i32.const 0x3F))

    ;; reufe existing context
    (if (i32.eq (i32.const 4))
      (then
        (return (local.get $mem))
      )
    )

    (local.get $value)

    ;; check its heap binary
    (if (i32.eq (i32.const 0x24))
      (then (nop))
      (else (return (i32.const 0)))
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
  (export "minibeam#make_match_context_2" (func $make_match_context))

  (func $bs_integer_raw (param $ctx i32) (param $bits_number i32) (result i32)
    (local $ptr i32)
    (local $bin_ptr i32)
    (local $temp i32)
    (local $offset i32)
    (local $in_byte_offset i32)

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

    ;; offset is in bits
    (i32.load (i32.add (local.get $ptr) (i32.const 8)))
    (local.set $offset)
    (local.set $in_byte_offset (i32.and (i32.const 7) (local.get $offset)))

    (if (call $is_mem_ptr (local.get $bin_ptr))
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

    (local.set $offset (i32.add (local.get $offset) (local.get $bits_number)))
    (i32.store (i32.add (local.get $ptr) (i32.const 8)) (local.get $offset))

    (local.get $temp)
    (i32.load)
    (call $flip_endian)
    (local.get $in_byte_offset)
    (i32.shl)
  )
  (export "minibeam#bs_get_integer_raw_2" (func $bs_integer_raw))

  (func $bs_ensure_at_least (param $ctx i32) (param $unit_size_bits i32) (param $unit_round i32) (result i32)
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
  (export "minibeam#bs_ensure_at_least_3" (func $bs_ensure_at_least))

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

  (func $bs_ensure_exactly (param $ctx i32) (param $unit_size_bits i32) (result i32)
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

    ;; everything above this point should be part of bs_match
    ;; and done once.
    ;; the reason its not inlined -- op code writers cant declare
    ;; local variables right now
    ;; everything below this point should be inlined instead of making this call

    ;; the size is in bits, add offset in bits to it
    (local.set $size (i32.sub (local.get $size) (local.get $offset)))

    (i32.eq (local.get $size) (local.get $unit_size_bits))
  )
  (export "minibeam#bs_ensure_exactly_2" (func $bs_ensure_exactly))


  (func $bs_skip (param $ctx i32) (param $bits_number i32) (result i32)
    (local $ptr i32)
    (local $bin_ptr i32)
    (local $temp i32)
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

    ;; offset is in bits
    (i32.load (i32.add (local.get $ptr) (i32.const 8)))
    (local.set $offset)
    (local.set $offset (i32.add (local.get $offset) (local.get $bits_number)))
    (i32.store (i32.add (local.get $ptr) (i32.const 8)) (local.get $offset))

    (i32.const 1)
  )
  (export "minibeam#bs_skip_2" (func $bs_skip))

  (func $bs_get_position (param $ctx i32) (result i32)
    (local $ptr i32)
    (local $bin_ptr i32)
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

    ;; offset is in bits
    (i32.load (i32.add (local.get $ptr) (i32.const 8)))
  )
  (export "minibeam#bs_get_position_1" (func $bs_get_position))


  (func $bs_set_position (param $ctx i32) (param $offset i32) (result i32)
    (local $ptr i32)
    (local $bin_ptr i32)

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

    ;; offset is in bits
    (i32.store (i32.add (local.get $ptr) (i32.const 8)) (local.get $offset))
    (i32.const 1)
  )
  (export "minibeam#bs_set_position_2" (func $bs_set_position))

  (func $bs_get_binary (param $ctx i32) (param $read_size i32) (result i32)
    (local $ptr i32)
    (local $bin_ptr i32)
    (local $size i32)
    (local $offset i32)
    (local $ret i32)

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

    (local.get $read_size)
    (i32.and (i32.const 0xF))
    (if (i32.eq (i32.const 0xF)) ;; has to be integer
        (then nop)
        (else unreachable)
    )
    ;; erl integer
    (local.set $read_size ;; bytes
      (i32.shr_u (local.get $read_size) (i32.const 4))
    )
    (local.set $read_size ;; bits
      (i32.shl (local.get $read_size) (i32.const 3))
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

  (export "minibeam#get_binary_from_ctx_2" (func $bs_get_binary))

  (func $bs_get_utf8 (param $ctx i32) (result i32)
    (local $ptr i32)
    (local $bin_ptr i32)
    (local $offset i32)
    (local $ret i32)
    (local $bits_consumed i32)

    (if (call $is_mem_ptr (local.get $ctx))
        (then nop)
        (else (return (i32.const 0)))
    )
    (local.set $ptr (i32.shr_u (local.get $ctx) (i32.const 2)))

    (i32.load (local.get $ptr))
    (i32.and (i32.const 0x3F))
    (if (i32.eq (i32.const 4)) ;; has to be match ctx
        (then nop)
        (else (return (i32.const 0)))
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
    (local.set $bin_ptr
      (i32.add
        (i32.shr_u (local.get $offset) (i32.const 3))
        (i32.add (local.get $bin_ptr) (i32.const 8))
      )
    )
    (local.set $ret (i32.load (local.get $bin_ptr)))

    (block $byte_switch
    (if (i32.eqz (i32.and (local.get $ret) (i32.const 0x80))) ;; 0b0XXX XXXX
        (then
          (local.set $bits_consumed (i32.const 8))
          (br $byte_switch)
        )
    )
    ;; ї is U+0457 encoded as \xd1\x97
    (if (i32.eq (i32.and (local.get $ret) (i32.const 0xE0)) (i32.const 0xC0)) ;; 0b110X XXXX
        (then
          (local.set $bits_consumed (i32.const 16))
          (local.set $ret
            (i32.or
              (i32.shl (i32.and (i32.const 0x1F) (local.get $ret)) (i32.const 6))
              (i32.shr_u (i32.and (i32.const 0x3F00) (local.get $ret)) (i32.const 8))
            )
          )
          (br $byte_switch)
        )
    )
    ;; つ is U+3064, encoded as \xe3\x81\xa4
    ;; hex(
    ;;   (u8be & 0x3F_00_00) >> 16 |
    ;;   (u8be & 0x00_3F_00) >> 2  |
    ;;   (u8be & 0x00_00_0F) << 12
    ;; )
   (if (i32.eq (i32.and (local.get $ret) (i32.const 0xF0)) (i32.const 0xE0)) ;; 0b1110 XXXX
        (then
          (local.set $bits_consumed (i32.const 24))
          (local.set $ret
            (i32.or
            (i32.or
              (i32.shl (i32.and (i32.const 0x0F) (local.get $ret)) (i32.const 12))
              (i32.shr_u (i32.and (i32.const 0x3F00) (local.get $ret)) (i32.const 2))
              (i32.shr_u (i32.and (i32.const 0x3F0000) (local.get $ret)) (i32.const 16))
            )
            )
          )
          (br $byte_switch)
        )
    )
    ;; 🌞 is U+1F31E encoded as \xf0\x9f\x8c\x9E
    ;; hex((u8 & 0x07_00_00_00) >> 8 | (u8 & 0x3F_00_00) >> 4 | (u8 & 0x00_3F_00) >> 2 | (u8 & 0x00_00_3F))
    (if (i32.eq (i32.and (local.get $ret) (i32.const 0xF8)) (i32.const 0xF0)) ;; 0b1111 0XXX
        (then
          (local.set $bits_consumed (i32.const 32))
          (local.set $ret
            (i32.or
              (i32.or
                (i32.shl (i32.and (i32.const 0x07) (local.get $ret)) (i32.const 16))
                (i32.shl (i32.and (i32.const 0x3F00) (local.get $ret)) (i32.const 4))
              )
              (i32.or
                (i32.shr_u (i32.and (i32.const 0x3F_00_00) (local.get $ret)) (i32.const 10))
                (i32.shr_u (i32.and (i32.const 0x3F_00_00_00) (local.get $ret)) (i32.const 24))
              )
            )
          )
          (br $byte_switch)
        )
    )

    (unreachable)
    )

    (local.set $offset (i32.add (local.get $offset) (local.get $bits_consumed)))
    (i32.store (i32.add (local.get $ptr) (i32.const 8)) (local.get $offset))

    (i32.or
      (i32.shl (local.get $ret) (i32.const 4))
      (i32.const 0xF)
    )
  )

  (export "minibeam#get_utf8_from_ctx_1" (func $bs_get_utf8))


  (func $bs_get_utf16 (param $ctx i32) (result i32)
    (local $ptr i32)
    (local $bin_ptr i32)
    (local $offset i32)
    (local $ret i32)
    (local $bits_consumed i32)

    (if (call $is_mem_ptr (local.get $ctx))
        (then nop)
        (else (return (i32.const 0)))
    )
    (local.set $ptr (i32.shr_u (local.get $ctx) (i32.const 2)))

    (i32.load (local.get $ptr))
    (i32.and (i32.const 0x3F))
    (if (i32.eq (i32.const 4)) ;; has to be match ctx
        (then nop)
        (else (return (i32.const 0)))
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
    (local.set $bin_ptr
      (i32.add
        (i32.shr_u (local.get $offset) (i32.const 3))
        (i32.add (local.get $bin_ptr) (i32.const 8))
      )
    )
    (local.set $ret (i32.load (local.get $bin_ptr)))

    (if (i32.eq (i32.and (i32.const 0xFF00) (local.get $ret)) (i32.const 0xD800)) ;; surrogage pair
        (then
          (local.set $bits_consumed (i32.const 32))
          ;; high 10
          (i32.shl
            (i32.and (i32.const 0x3ff) (local.get $ret))
            (i32.const 10)
          )
          ;; low 10
          (i32.shr_u
            (local.get $ret)
            (i32.const 16)
          )
          (i32.const 0x3ff)
          (i32.and)
          (i32.or)
          (i32.const 0x1_00_00)
          (i32.or)
          (local.set $ret)
        )
        (else
          (local.set $bits_consumed (i32.const 16))
        )
    )

    (local.set $offset (i32.add (local.get $offset) (local.get $bits_consumed)))
    (i32.store (i32.add (local.get $ptr) (i32.const 8)) (local.get $offset))

    (i32.or
      (i32.shl (local.get $ret) (i32.const 4))
      (i32.const 0xF)
    )
  )

  (export "minibeam#get_utf16_from_ctx_1" (func $bs_get_utf16))


  (func $bs_get_tail (param $ctx i32) (result i32)
    (local $ptr i32)
    (local $bin_ptr i32)
    (local $size i32)
    (local $offset i32)
    (local $ret i32)

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

    ;; bc get tail should not consume the context,
    ;; as context can be reused later. this blows up json decoder on otp 26
    ;; (local.set $offset (i32.add (local.get $offset) (local.get $size)))
    ;; (i32.store (i32.add (local.get $ptr) (i32.const 8)) (local.get $offset))

    (local.get $ret)
  )

  (export "minibeam#bs_get_tail_1" (func $bs_get_tail))

  (func $bit_size_bin (param $ptr i32) (result i32)
    (local $size i32)
    (i32.load (i32.add (local.get $ptr) (i32.const 4)))
  )

  (func $bit_size_ctx (param $ptr i32) (result i32)
    (local $full_size i32)
    (local $bin_ptr i32)
    (local $offset i32)

    (i32.load (i32.add (local.get $ptr) (i32.const 4)))
    (local.set $bin_ptr)
    (call $get_bit_size (local.get $bin_ptr))
    (local.set $full_size) ;; in bits

    ;; offset is in bits
    (i32.load (i32.add (local.get $ptr) (i32.const 8)))
    (local.set $offset)

    (i32.sub (local.get $full_size) (local.get $offset))
  )


  (func $get_bit_size (param $mem i32) (result i32)
    (local $ptr i32)

    (if (call $is_mem_ptr (local.get $mem))
        (then nop)
        (else unreachable)
    )
    (local.set $ptr (i32.shr_u (local.get $mem) (i32.const 2)))

    (i32.load (local.get $ptr))
    (i32.and (i32.const 0x3F))
    (if (i32.eq (i32.const 0x24)) ;; has to be binary
        (then
          (return (call $bit_size_bin (local.get $ptr)))
        )
    )

    (i32.load (local.get $ptr))
    (i32.and (i32.const 0x3F))
    (if (i32.eq (i32.const 0x4)) ;; has to be match ctx
        (then
          (return (call $bit_size_ctx (local.get $ptr)))
        )
    )

    (unreachable)
  )
  (export "minibeam#get_bit_size_1" (func $get_bit_size))

  (func $get_bit_size_utf8 (param $v i32) (result i32)
    (local.set $v (i32.shr_u (local.get $v) (i32.const 4)))
    (if
      (i32.le_u (local.get $v) (i32.const 0x7F))
      (then (return (i32.const 8)))
    )
    (if
      (i32.le_u (local.get $v) (i32.const 0x7FF))
      (then (return (i32.const 16)))
    )
    (if
      (i32.le_u (local.get $v) (i32.const 0xFFFF))
      (then (return (i32.const 24)))
    )

    (if
      (i32.le_u (local.get $v) (i32.const 0x10FFFF))
      (then (return (i32.const 32)))
    )
    (unreachable)
  )
  (export "minibeam#get_bit_size_utf8_1" (func $get_bit_size_utf8))

  (func $get_bit_size_utf16 (param $v i32) (result i32)
    (local.set $v (i32.shr_u (local.get $v) (i32.const 4)))
    (if
      (i32.le_u (local.get $v) (i32.const 0xFF_FF))
      (then
        (return (i32.const 16))
      )
    )
    (if
      (i32.le_u (local.get $v) (i32.const 0x10_FF_FF))
      (then
        (return (i32.const 32))
      )
    )
    (unreachable)
  )

  (export "minibeam#get_bit_size_utf16_1" (func $get_bit_size_utf16))

  (func $binary_part_3 (param $mem i32) (param $pos i32) (param $len i32) (result i32)
    (local $ptr i32)

    (if (i32.eq (i32.and (local.get $pos) (i32.const 0xF)) (i32.const 0xF))
        (then nop)
        (else unreachable)
    )
    (local.set $pos (i32.shr_u (local.get $pos) (i32.const 4)))

    (if (i32.eq (i32.and (local.get $len) (i32.const 0xF)) (i32.const 0xF))
        (then nop)
        (else unreachable)
    )
    (local.set $len (i32.shr_u (local.get $len) (i32.const 4)))

    (if (call $is_mem_ptr (local.get $mem))
        (then nop)
        (else unreachable)
    )
    (local.set $ptr (i32.shr_u (local.get $mem) (i32.const 2)))

    (i32.load (local.get $ptr))
    (i32.and (i32.const 0x3F))
    (if (i32.eq (i32.const 0x24)) ;; has to be binary
        (then (nop))
        (else (unreachable))
    )
    (i32.add (local.get $ptr) (i32.const 8))
    (local.set $ptr)
    (i32.add (local.get $ptr) (local.get $pos))
    (local.set $ptr)

    (call $make_erl_buf (local.get $ptr) (local.get $len))
  )

  (export "binary#part_3" (func $binary_part_3))
)

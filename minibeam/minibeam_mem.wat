(module
  (import "wasi:cli/stdout@0.2.0" "get-stdout" (func $get_stdout (result i32)))
  (import "wasi:io/streams@0.2.0" "[method]output-stream.blocking-write-and-flush" (func $output_stream_write_flush (param i32 i32 i32 i32)))

  (memory 0)
  (data (i32.const 0) "") ;; 4
  (data (i32.const 4) "Hi\n") ;; 3
  (data (i32.const 8)  "0x00000000\n") ;; 18
  (data (i32.const 32) "00000000000\00\00") ;; 44

  (global $__unique__trace_enable (mut i32) (i32.const 0) (mut i32) (i32.const 0))
  (global $__ret__literal_ptr_raw i32 (i32.const 0))
  (global $__hi__literal_ptr_raw i32 (i32.const 4))
  (global $__buffer__literal_ptr_raw i32 (i32.const 8))
  (global $__nbuffer__literal_ptr_raw i32 (i32.const 10))
  (global $__dec_buffer__literal_ptr_raw i32 (i32.const 32))

  (global $__unique_atom__utf8 i32 (i32.const 2))

  (global $__free_mem (mut i32) (i32.const 44))

  (func $write_flush (param $stream i32) (param $ptr i32) (param $len i32) (result i32)
      ;; pass four args to write method
      ;; stdout handle, memory pointer, lentgh of data and mem pointer to store result
      (call $output_stream_write_flush (local.get $stream) (local.get $ptr) (local.get $len) (global.get $__ret__literal_ptr_raw))
      (i32.load (global.get $__ret__literal_ptr_raw))
  )

  (func $log (param $ptr i32) (param $len i32) (result i32)
      (local $stdout i32)

      ;; get stdout handle because you cant just assume its 0
      ;; everyone knows that magic constants are bad and unix isnt
      ;; well designed in this department
      (local.set $stdout (call $get_stdout))

      (call $write_flush (local.get $stdout) (local.get $ptr) (local.get $len))
  )
  (export "erdump#log" (func $log))

  (func $hexlog_format (param $value i32)
      (local $buf i32)
      (local $temp i32)
      (local $buflen i32)
      (local $len i32)
      (local.set $buf (i32.add (i32.const 9) (global.get $__buffer__literal_ptr_raw)))
      (local.set $len (i32.const 8))

      (loop $loop
      (local.get $value)
      (i32.and (i32.const 0xF))
      (local.set $temp)
      (if (i32.le_u (local.get $temp) (i32.const 9))
          (then
            (i32.store8 (local.get $buf) (i32.add (i32.const 0x30) (local.get $temp)))
          )
          (else
            (i32.store8 (local.get $buf) (i32.add (i32.const 0x37) (local.get $temp)))
          )
      )
      (local.set $buf (i32.sub (local.get $buf) (i32.const 1)))
      (local.set $value (i32.shr_u (local.get $value) (i32.const 4)))

      (local.set $len (i32.sub (local.get $len) (i32.const 1)))
      (local.get $len)
      (if (i32.eqz) (then) (else (br $loop)))
      )
  )

  (func $dec_format (param $value i32) (result i32)
      (local $buf i32)
      (local $rem i32)
      (local $pos i32)

      (local.set $buf
        (i32.add
          (global.get $__dec_buffer__literal_ptr_raw)
          (i32.const 10)
        )
      )
      (local.set $pos (i32.const 10))

      (loop $loop
        (local.get $buf)
        (i32.rem_u
          (local.get $value)
          (i32.const 10)
        )
        (i32.const 0x30)
        (i32.add)
        (i32.store8)

        (i32.div_u
          (local.get $value)
          (i32.const 10)
        )
        (local.set $value)

        (local.set $pos (i32.sub (local.get $pos) (i32.const 1)))
        (local.set $buf (i32.sub (local.get $buf) (i32.const 1)))

        (if (i32.eqz (local.get $pos))
            (then (unreachable))
        )
        (if (i32.eqz (local.get $value))
            (then (nop))
            (else (br $loop))
        )
      )
      (local.get $pos)
  )

  ;; this is terribly suboptimal as it does BE-LE conversion
  (func $int_bin_helper (param $value i32) (param $int_bits i32) (result i32)
    (local.get $value)
    (i32.const 4)
    (i32.shr_u)
    (local.set $value)

    (if
      (i32.eq (local.get $int_bits) (i32.const 8))
      (then
        (i32.store8
          (global.get $__nbuffer__literal_ptr_raw)
          (local.get $value)
        )
        (return (i32.const 1))
      )
    )
    (if
      (i32.eq (local.get $int_bits) (i32.const 16))
      (then
        (i32.store8
          (i32.add
            (global.get $__nbuffer__literal_ptr_raw)
            (i32.const 1)
          )
          (i32.and (local.get $value) (i32.const 0xFF))
        )
        (i32.store8
          (i32.add
            (global.get $__nbuffer__literal_ptr_raw)
            (i32.const 0)
          )
          (i32.and
            (i32.shr_u (local.get $value) (i32.const 8))
            (i32.const 0xFF)
          )
        )
        (return (i32.const 2))
      )
    )
    (if
      (i32.eq (local.get $int_bits) (i32.const 32))
      (then
        (i32.store8
          (i32.add
            (global.get $__nbuffer__literal_ptr_raw)
            (i32.const 3)
          )
          (i32.and (local.get $value) (i32.const 0xFF))
        )
        (i32.store8
          (i32.add
            (global.get $__nbuffer__literal_ptr_raw)
            (i32.const 2)
          )
          (i32.and
            (i32.shr_u (local.get $value) (i32.const 8))
            (i32.const 0xFF)
          )
        )
        (i32.store8
          (i32.add
            (global.get $__nbuffer__literal_ptr_raw)
            (i32.const 1)
          )
          (i32.and
            (i32.shr_u (local.get $value) (i32.const 16))
            (i32.const 0xFF)
          )
        )
        (i32.store8
          (i32.add
            (global.get $__nbuffer__literal_ptr_raw)
            (i32.const 0)
          )
          (i32.and
            (i32.shr_u (local.get $value) (i32.const 24))
            (i32.const 0xFF)
          )
        )

        (return (i32.const 4))
      )
    )
    (if
      (i32.eq (local.get $int_bits) (i32.const 24))
      (then
        (i32.store8
          (i32.add
            (global.get $__nbuffer__literal_ptr_raw)
            (i32.const 2)
          )
          (i32.and (local.get $value) (i32.const 0xFF))
        )
        (i32.store8
          (i32.add
            (global.get $__nbuffer__literal_ptr_raw)
            (i32.const 1)
          )
          (i32.and
            (i32.shr_u (local.get $value) (i32.const 8))
            (i32.const 0xFF)
          )
        )
        (i32.store8
          (i32.add
            (global.get $__nbuffer__literal_ptr_raw)
            (i32.const 0)
          )
          (i32.and
            (i32.shr_u (local.get $value) (i32.const 16))
            (i32.const 0xFF)
          )
        )

        (return (i32.const 3))
      )
    )
    (unreachable)
  )

  (func $serialize_int (param $value i32) (result i32)
    (local $len i32)

    (local.get $value)
    (i32.const 4)
    (i32.shr_u)


    (call $dec_format)
    (local.set $len)

    (i32.add
      (global.get $__dec_buffer__literal_ptr_raw)
      (local.get $len)
    )
    (i32.const 1) ;; yep, it's off by one
    (i32.add)
    (i32.sub (i32.const 10) (local.get $len))
    (call $write_buf)
  )

  (export "erlang#integer_to_binary_1" (func $serialize_int))

  (func $hexlog (param $value i32) (result i32)
      (call $hexlog_format (local.get $value))
      (call $log (global.get $__buffer__literal_ptr_raw ) (i32.const 11))
  )

  (export "erdump#hexlog_1" (func $hexlog))

  (func $display (param $erl_val i32) (result i32)
      (local $len i32)
      (call $read_erl_mem (local.get $erl_val) (global.get $__free_mem))
      (local.set $len)
      (if (i32.eqz (local.get $len))
        (then
          (return (i32.const 0))
        )
      )
      (return (call $log (global.get $__free_mem) (local.get $len)))
  )
  (export "minibeam#display_1" (func $display))


  (func $alloc (param $align i32) (param $size i32) (result i32)
      (local $tmp i32)
      (local $ret i32)
      (local.set $ret (global.get $__free_mem))

      (local.set $tmp (i32.ctz (local.get $align)))
      (i32.shl
        (i32.shr_u (local.get $ret) (local.get $tmp))
        (local.get $tmp)
      )
      (local.set $ret)
      (local.set $ret (i32.add (local.get $ret) (local.get $align)))
      (global.set $__free_mem (i32.add (local.get $ret) (local.get $size)))
      (local.get $ret)
  )
  (export "erdump#alloc" (func $alloc))
  (export "mimibeam#alloc_2" (func $alloc))

  (func $read_erl_mem (param $erl_val i32) (param $mem_buffer i32) (result i32)
    (local $their_ptr i32)
    (local $len i32)
    (local $int_v i32)
    (local $mem_start i32)
    (local $iter_len i32)
    (local.set $mem_start (local.get $mem_buffer))

    (loop $loop
    (block $find_type
    ;; 0xF is int
    (if (i32.eq (i32.const 0xF) (i32.and (i32.const 0xF) (local.get $erl_val)))
      (then
        (local.set $int_v (i32.shr_u (local.get $erl_val) (i32.const 4)))
        (i32.store (local.get $mem_buffer) (local.get $int_v))
        (i32.const 4)
        (local.set $mem_buffer (i32.add (local.get $mem_buffer)))
        (br $find_type)
      )
    )
    ;; 0b10 is mem pointer
    (if (i32.eq (i32.const 0x2) (i32.and (i32.const 0x3) (local.get $erl_val)))
      (then
        (local.set $their_ptr (i32.shr_u (local.get $erl_val) (i32.const 2)))
        (local.set $erl_val (i32.load (local.get $their_ptr)))

        (br $loop)
      )
    )


    ;; 0x24 is heap binary
    (if (i32.eq (i32.const 0x24) (i32.and (i32.const 0x3F) (local.get $erl_val)))
      (then
      (i32.load (i32.add (local.get $their_ptr) (i32.const 4)))
      (i32.const 3)
      (i32.shr_u)
      (local.set $iter_len)
      (local.set $their_ptr (i32.add (local.get $their_ptr) (i32.const 8)))

      (loop $iter
        (if (i32.eqz (local.get $iter_len))
          (then
            (br $find_type)
          )
        )
        (i32.store8 (local.get $mem_buffer) (i32.load8_u (local.get $their_ptr)))

        (local.set $iter_len (i32.sub (local.get $iter_len) (i32.const 1)))
        (local.set $their_ptr (i32.add (local.get $their_ptr) (i32.const 1)))
        (local.set $mem_buffer (i32.add (local.get $mem_buffer) (i32.const 1)))


        (br $iter)
      )
      )
    )

    ;; 0b01 is list head pointer
    (if (i32.eq (i32.const 0x1) (i32.and (i32.const 0x3) (local.get $erl_val)))
      (then
        (call
          $read_erl_mem
          (i32.load (i32.add (i32.const 4) (local.get $their_ptr)))
          (local.get $mem_buffer)
        )
        (local.set $mem_buffer (i32.add (local.get $mem_buffer)))

        (local.set
          $their_ptr
          (i32.shr_u (local.get $erl_val) (i32.const 2))
        )
        (local.set $erl_val (i32.load (local.get $their_ptr)))

        (if (i32.eq (local.get $erl_val) (i32.const 0x3b))
          (then (br $find_type))
        )

        (br $loop)
        ;; (br $find_type)
      )
    )

    (if (i32.eq (i32.const 0x3b) (local.get $erl_val))
      (then
        ;; null
        (i32.store (local.get $mem_buffer) (i32.const 0x4C4C554E))
        (i32.const 4)
        (local.set $mem_buffer (i32.add (local.get $mem_buffer)))
        (br $find_type)
      )
    )

    ;; type is unknow to us, dump it!
    ;;; (i32.store (local.get $mem_buffer) (local.get $erl_val)) ;; this should be a trap
    ;;; (local.set $mem_buffer (i32.add (local.get $mem_buffer) (i32.const 4)))

    (unreachable)

    );; end find_type
    );; end loop

    (local.set $len (i32.sub (local.get $mem_buffer) (local.get $mem_start)))
    (local.get $len)
  )
  (export "erdump#dump" (func $read_erl_mem ))

  (func $write_str (param $mem i32) (param $len i32) (result i32)
    (local $idx i32)
    (local $ptr i32)
    (local $ret i32)
    (local $erlen i32)
    (local.set $ptr (global.get $__free_mem))
    (local.set $idx (i32.const 0))
    (local.set $ret (local.get $ptr))

    ;; For N len string, allocate (N+1) * 8 mem
    (local.set
      $erlen
      (i32.mul (i32.const 8) (i32.add (i32.const 1) (local.get $len)))
    )

    (global.set $__free_mem
      (i32.add (local.get $ptr) (local.get $erlen))
    )
    (loop $loop
      (if (i32.eqz (local.get $len))
        (then (nop))
        (else
          (i32.store
            (local.get $ptr)
            ;; list pointer to skip over next 4 bytes
            (i32.or (i32.shl (i32.const 4) (i32.const 2)) (i32.const 1))
          )
          (local.set $ptr (i32.add (i32.const 4) (local.get $ptr)))

          (i32.store
            (local.get $ptr)
            (i32.or
              (i32.const 0xF)
              (i32.shl
                (i32.and (i32.load (local.get $mem)) (i32.const 0xFF))
                (i32.const 4)
              )
            )
          )
          (local.set $ptr (i32.add (i32.const 4) (local.get $ptr)))
          (local.set $mem (i32.add (i32.const 1) (local.get $mem)))

          (local.set $len (i32.sub (local.get $len) (i32.const 1)))
          (br $loop)
        )
      )
    )
    (i32.store (local.get $ptr) (i32.const 0x3b))
    (local.set $ptr (i32.add (i32.const 4) (local.get $ptr)))
    (i32.store (local.get $ptr) (i32.const 0x0))

    (i32.or (i32.shl (local.get $ret) (i32.const 2)) (i32.const 2))
    ;; (local.get $ret)
  )

  (export "erdump#write_str" (func $write_str))

  ;; len is in bits
  (func $alloc_write_buf (param $len i32) (result i32)
    (local $ptr i32)
    (local $erlen i32)

    ;; For N len binary, allocate (N + (2 * 4)) mem
    (local.set $erlen (i32.add (i32.const 64) (local.get $len)))
    (if (i32.eq (i32.const 0xA) (local.get $len))
       (then (unreachable))
    )

    ;; word align size
    (i32.shl
      (i32.shr_u (local.get $erlen) (i32.const 5))
      (i32.const 5)
    )
    (i32.add (i32.const 32))
    (local.set $erlen)

    (local.set $ptr (call $alloc (i32.const 4) (i32.shr_u (local.get $erlen) (i32.const 3))))

    ;; write header
    (i32.store (local.get $ptr) (i32.const 0x24)) ;; 0 tag heap binary

    (i32.store ;; 1 binary size in bits
      (i32.add (i32.const 4) (local.get $ptr))
      (local.get $len)
    )

    (local.get $ptr)
  )
  (export "minibeam#alloc_binary_1" (func $alloc_write_buf))

  (func $write_into_buf (param $ptr i32) (param $out_offset i32) (param $mem i32) (param $len i32) (result i32)
    (local.get $ptr)
    (i32.add (local.get $out_offset))
    (i32.add (i32.const 8))
    (local.set $ptr)
    (block $exit
    (loop $loop
      (if (i32.eqz (local.get $len))
        (then (br $exit))
      )

      (i32.store8 (local.get $ptr) (i32.load8_u (local.get $mem)))

      (local.set $ptr (i32.add (i32.const 1) (local.get $ptr)))
      (local.set $mem (i32.add (i32.const 1) (local.get $mem)))

      (local.set $len (i32.sub (local.get $len) (i32.const 1)))
      (br $loop)
    )
    )
    (local.get $len)
  )

  (func $write_buf (param $mem i32) (param $len i32) (result i32)
    (local $ret i32)
    (local $erlen i32)

    (call $alloc_write_buf (i32.shl (local.get $len) (i32.const 3)))
    (local.set $ret)
    (call $write_into_buf (local.get $ret) (i32.const 0) (local.get $mem) (local.get $len)) (drop)

    (i32.or (i32.shl (local.get $ret) (i32.const 2)) (i32.const 2))
  )
  (export "erdump#write_buf" (func $write_buf))

  (func $copy_into_buf (param $out_offset i32) (param $out_ptr i32) (param $in_ptr i32) (param $int_size_bits i32) (result i32)
    (local $len i32)
    (local $mem i32)

    (if (i32.eq (i32.and (local.get $in_ptr) (i32.const 0xF)) (i32.const 0xF))
        (then
           (local.set $len
             (call $int_bin_helper (local.get $in_ptr) (local.get $int_size_bits))
           )
	   (local.set $mem (global.get $__nbuffer__literal_ptr_raw))
           (call $write_into_buf (local.get $out_ptr) (local.get $out_offset) (local.get $mem) (local.get $len)) (drop)
	   (return (i32.add (local.get $len) (local.get $out_offset)))
	)
    )

    (if (i32.eq (i32.and (local.get $in_ptr) (i32.const 2)) (i32.const 2))
        (then nop)
        (else (unreachable))
    )
    (local.set $in_ptr (i32.shr_u (local.get $in_ptr) (i32.const 2)))

    (i32.load (local.get $in_ptr))
    (i32.and (i32.const 0x3F))
    (if (i32.eq (i32.const 0x24)) ;; has to be binary
        (then nop)
        (else (unreachable))
    )
    (i32.load (i32.add (local.get $in_ptr) (i32.const 4)))
    (i32.const 3)
    (i32.shr_u) ;; size in bytes
    (local.set $len)
    (local.set $mem (i32.add (i32.const 8) (local.get $in_ptr)))

    (call $write_into_buf (local.get $out_ptr) (local.get $out_offset) (local.get $mem) (local.get $len)) (drop)

    (i32.add (local.get $len) (local.get $out_offset))
  )
  (export "minibeam#into_buf_4" (func $copy_into_buf))

  (func $copy_into_buf_utf8 (param $out_offset i32) (param $out_ptr i32) (param $in_ptr i32) (result i32)
    (local $len i32)
    (local $mem i32)
    (local $value i32)

    (local.set $mem (global.get $__nbuffer__literal_ptr_raw))

    (if (i32.eq (i32.and (local.get $in_ptr) (i32.const 0xF)) (i32.const 0xF))
        (then (nop))
        (else (unreachable))
    )

    (local.set $value (i32.shr_u (local.get $in_ptr) (i32.const 4)))
    (block $bytes

    (if
      (i32.le_u (local.get $value) (i32.const 0x7F))
      (then
        (local.set $len (i32.const 8))
        (i32.store8 (local.get $mem) (local.get $value))

        (call $write_into_buf (local.get $out_ptr) (local.get $out_offset) (local.get $mem) (local.get $len)) (drop)
        (br $bytes)
      )
    )

    (if
      (i32.le_u (local.get $value) (i32.const 0x7FF))
      (then
        (local.set $len (i32.const 16))

        ;; write lower byte first
        (local.get $mem)
        (i32.const 1)
        (i32.add)

        ;; lower byte has 6 bits and 0b10 header
        (local.get $value)
        (i32.const 0x3F)
        (i32.and)
        (i32.const 0x80)
        (i32.or)
        (i32.store8)

        ;; discard 6 bits already written
        ;; and add 0b110 header
        (local.get $mem)
        (local.get $value)
        (i32.const 6)
        (i32.shr_u)
        (i32.const 0xC0)
        (i32.or)
        (i32.store8)

        (call $write_into_buf (local.get $out_ptr) (local.get $out_offset) (local.get $mem) (local.get $len)) (drop)
        (br $bytes)
      )
    )

    (if
      (i32.le_u (local.get $value) (i32.const 0xFFFF))
      (then
        (local.set $len (i32.const 24))

        ;; write lower byte first
        (local.get $mem)
        (i32.const 2)
        (i32.add)

        ;; lower byte has 6 bits and 0b10 header
        (local.get $value)
        (i32.const 0x3F)
        (i32.and)
        (i32.const 0x80)
        (i32.or)
        (i32.store8)

        ;; discard 6 bits already written
        ;; and add 0b10 header
        ;; again use only 6 bits
        (local.get $mem)
        (i32.const 1)
        (i32.add)

        (local.get $value)
        (i32.const 6)
        (i32.shr_u)
        (i32.const 0x3F)
        (i32.and)
        (i32.const 0x80)
        (i32.or)
        (i32.store8)

        ;; discard 12 bits already written
        ;; and add 0b1110 header
        ;; again use only 6 bits
        (local.get $mem)
        (local.get $value)
        (i32.const 12)
        (i32.shr_u)
        (i32.const 0xE0)
        (i32.or)
        (i32.store8)
        (call $write_into_buf (local.get $out_ptr) (local.get $out_offset) (local.get $mem) (local.get $len)) (drop)
        (br $bytes)
      )
    )

    (if
      (i32.le_u (local.get $value) (i32.const 0x10FFFF))
      (then
        (local.set $len (i32.const 32))

        ;; write lower byte first
        (local.get $mem)
        (i32.const 3)
        (i32.add)

        ;; lower byte has 6 bits and 0b10 header
        (local.get $value)
        (i32.const 0x3F)
        (i32.and)
        (i32.const 0x80)
        (i32.or)
        (i32.store8)

        ;; discard 6 bits already written
        ;; and add 0b10 header
        ;; again use only 6 bits
        (local.get $mem)
        (i32.const 2)
        (i32.add)

        (local.get $value)
        (i32.const 6)
        (i32.shr_u)
        (i32.const 0x3F)
        (i32.and)
        (i32.const 0x80)
        (i32.or)
        (i32.store8)

        ;; discard 12 bits already written
        ;; and add 0b10 header
        ;; again use only 6 bits
        (local.get $mem)
        (i32.const 1)
        (i32.add)

        (local.get $value)
        (i32.const 12)
        (i32.shr_u)
        (i32.const 0x3F)
        (i32.and)
        (i32.const 0x80)
        (i32.or)
        (i32.store8)

        ;; discard 18 bits already written
        ;; and add 0b1110 header
        ;; again use only 6 bits
        (local.get $mem)
        (local.get $value)
        (i32.const 18)
        (i32.shr_u)
        (i32.const 0xF0)
        (i32.or)
        (i32.store8)
        (call $write_into_buf (local.get $out_ptr) (local.get $out_offset) (local.get $mem) (local.get $len)) (drop)
        (br $bytes)
      )
    )

    (unreachable)
    )

    (return (i32.add (local.get $len) (local.get $out_offset)))
   )

  (export "minibeam#into_buf_utf8_3" (func $copy_into_buf_utf8))

  (func $copy_into_buf_utf16 (param $out_offset i32) (param $out_ptr i32) (param $in_ptr i32) (result i32)
    (local $len i32)
    (local $mem i32)
    (local $value i32)

    (local.set $mem (global.get $__nbuffer__literal_ptr_raw))

    (if (i32.eq (i32.and (local.get $in_ptr) (i32.const 0xF)) (i32.const 0xF))
        (then (nop))
        (else (unreachable))
    )
    (local.set $value (i32.shr_u (local.get $in_ptr) (i32.const 4)))

    (block $bytes
    (if
      (i32.le_u (local.get $value) (i32.const 0xFF_FF))
      (then
        (local.set $len (i32.const 16))

        ;; l
        (local.get $mem)
        (i32.const 1)
        (i32.add)
        (local.get $value)
        (i32.const 0xFF) ;; 8 lower bits
        (i32.and)
        (i32.store8)

        ;; h
        (local.get $mem)
        (local.get $value)
        (i32.const 8)
        (i32.shr_u)
        (i32.const 0xFF) ;; 8 lower bits
        (i32.and)
        (i32.store8)


        (call $write_into_buf (local.get $out_ptr) (local.get $out_offset) (local.get $mem) (local.get $len)) (drop)
        (br $bytes)
      )
    )
    (if
      (i32.le_u (local.get $value) (i32.const 0x10_FF_FF))
      (then
        ;; leave lower 10 bits
        (local.set $value (i32.and (local.get $value) (i32.const 0xff_ff)))
        (local.set $len (i32.const 32))

        ;; l1
        (local.get $mem)
        (i32.const 3)
        (i32.add)
        (local.get $value)
        (i32.const 0xFF) ;; 8 lower bits
        (i32.and)
        (i32.store8)

        ;; l0
        (local.get $mem)
        (i32.const 2)
        (i32.add)
        (local.get $value)
        (i32.const 8)
        (i32.shr_u)
        (i32.const 0x3) ;; 2 bytes of the lower 10
        (i32.and)
        (i32.const 0xDC)
        (i32.or)
        (i32.store8)

        ;; h1
        (local.get $mem)
        (i32.const 1)
        (i32.add)
        (local.get $value)
        (i32.const 10)
        (i32.shr_u)
        (i32.const 0xFF) ;; 8 lower bits
        (i32.and)
        (i32.store8)

        ;; h0
        (local.get $mem)
        (local.get $value)
        (i32.const 18)
        (i32.shr_u)
        (i32.const 0x3) ;; 2 bytes of the lower 10
        (i32.and)
        (i32.const 0xD8)
        (i32.or)
        (i32.store8)

        (call $write_into_buf (local.get $out_ptr) (local.get $out_offset) (local.get $mem) (local.get $len)) (drop)
        (br $bytes)
      )
    )

    (unreachable)
    )

    (return (i32.add (local.get $len) (local.get $out_offset)))
   )

  (export "minibeam#into_buf_utf16_3" (func $copy_into_buf_utf16))

  (func $trace (param $name_buf i32) (param $line_erl i32) (param $enable i32) (result i32)
    (if
       (i32.or
         (global.get $__unique__trace_enable)
         (local.get $enable)
       )
       (then
         (i32.store
           (i32.add
	     (local.get $name_buf)
             (i32.const 28)
           )
	   (local.get $line_erl)
         )
         (call $display
	    (i32.or (i32.shl (local.get $name_buf) (i32.const 2)) (i32.const 2))
	 ) (drop)
       )
    )
    (i32.const 0x3b)
  )
  (export "minibeam#trace_3" (func $trace))
  (func $trace_enable (result i32)
    (global.set $__unique__trace_enable (i32.const 1))
    (i32.const 0x3b)
  )
  (export "minibeam#trace_enable_0" (func $trace_enable))

  (func $atom_to_binary_2 (param $atom i32) (param $encoding i32) (result i32)
    (if 
      (i32.eq (i32.and (i32.const 0x3f) (local.get $atom)) (i32.const 0xb))
      (then
        (local.set $atom (i32.shr_u (local.get $atom) (i32.const 6)))
      )
      (else (unreachable)) ;; not an atom
    )

    (if 
      (i32.eq (i32.and (i32.const 0x3f) (local.get $encoding)) (i32.const 0xb))
      (then
        (local.set $encoding (i32.shr_u (local.get $encoding) (i32.const 6)))
      )
      (else (unreachable)) ;; not an atom
    )

    (if
      (i32.eq (local.get $encoding) (global.get $__unique_atom__utf8))
      (then (nop))
      (else (unreachable)) ;; bad encoding
    )

    (local.get $atom)
    (global.get $__unique_table_of_atoms_ptr_raw)
    (i32.const 4)
    (i32.add)
    (i32.load)
    (i32.const 5) ;; stored size in bits, each atom is a word
    (i32.shr_u)
    (if
      (i32.lt_u)
      (then (nop))
      (else (unreachable)) ;; item id is not in a table
    )


    (local.get $atom)
    (i32.const 2)
    (i32.add)

    (i32.const 2)
    (i32.shl)

    (global.get $__unique_table_of_atoms_ptr_raw)
    (i32.add)

    (i32.load)
    (i32.const 2)
    (i32.shl)
    (i32.const 2)
    (i32.or)
  )

  (export      "erlang#atom_to_binary_2" (func $atom_to_binary_2))

  (func $atom_to_binary_1 (param $atom i32) (result i32)
    (local.get $atom)
    (global.get $__unique_atom__utf8)
    (i32.const 6)
    (i32.shl)
    (i32.const 0xB)
    (i32.or)
    (call $atom_to_binary_2)
  )

  (export      "erlang#atom_to_binary_1" (func $atom_to_binary_1))

)


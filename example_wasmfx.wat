;; This is an example of typed continuations.
;; To run this, use forked version of wasmtime from https://github.com/wasmfx/wasmfxtime/
;; and use the following command:
;;
;; wasmtime run  -W typed-continuations=y -W exceptions=y -W function-references=y example_wasmfx.wat
;;
(module
    ;; Import the required fd_write WASI function which will write the given io vectors to stdout
    ;; The function signature for fd_write is:
    ;; (File Descriptor, *iovs, iovs_len, *nwritten) -> Returns 0 on success, nonzero on error
    (import "wasi_snapshot_preview1" "fd_write" (func $fd_write (param i32 i32 i32 i32) (result i32)))

    ;; inline
    (type $func (func))       ;; [] -> []
    (type $cont (cont $func)) ;; cont ([] -> [])

    (tag $yield)                   ;; [] -> []

    (memory 1)
    (export "memory" (memory 0))

    ;; Write 'hello world\n' to memory at an offset of 8 bytes
    ;; Note the trailing newline which is required for the text to appear
    (data (i32.const 8) "hello world\n")
    (data (i32.const 24) "Xello lowld\n")
    (data (i32.const 40) "resumed\n")

    (func $log (param $ptr i32) (param $len i32)
        (i32.store (i32.const 0) (local.get $ptr))  ;; iov.iov_base - This is a pointer to the start of the 'hello world\n' string
        (i32.store (i32.const 4) (local.get $len))  ;; iov.iov_len - The length of the 'hello world\n' string

        (call $fd_write
            (i32.const 1) ;; file_descriptor - 1 for stdout
            (i32.const 0) ;; *iovs - The pointer to the iov array, which is stored at memory location 0
            (i32.const 1) ;; iovs_len - We're printing 1 string stored in an iov - so one.
            (i32.const 20) ;; nwritten - A place in memory to store the number of bytes written
        )
        drop ;; Discard the number of bytes written from the top of the stack
    )

    (func $thread1
      (call $log (i32.const 8) (i32.const 12)) ;; print Hello world
      (suspend $yield) ;; transfer control out of function
      (call $log (i32.const 24) (i32.const 12)) ;; print Xello lowld
    )
    (elem declare func $thread1)

    (func $main (export "_start")
      (local $cont1 (ref null $cont)) ;; Declare local variable referencing suspended function
      (local.set $cont1 (cont.new $cont (ref.func $thread1))) ;; create suspended function for $thread

      ;; Quick refresher on WASM:
      ;; doing br $loop_name from inside the loop jump to the start of the loop
      ;; doing br $block_name from inside of the block jumps OUT of the block to
      ;; the next command.
      ;; You cannot jump into the loop or into the block from outside a-la goto.

      (loop $scheduler_loop   ;; main loop
        (block $on_yield (result (ref null $cont))
          ;; we get here normally through the loop
          ;; it looks like suspend will bring us to this line,
          ;; but this is not true

          ;; we run resume twice and the value of cont1
          ;; after each run is invalidated.
          ;; we tull resume to jump OUT of this block when yield happend
          (resume $cont (tag $yield $on_yield) (local.get $cont1))
          ;; we end up here once continuation is fully consumed
          ;; so we return empty reference
          (ref.null $cont)
        )
        ;; we jump to here when suspend $yield is called.
        ;; we also end up here when block $on_yield exits normally (with ref.null)
        ;; in both cases, set cont1 to the result of block
        (local.set $cont1)

        (call $log (i32.const 40) (i32.const 8)) ;; print resumed

        ;; if cont1 is NOT set to null, enter the next iteration of the loop
        (ref.is_null (local.get $cont1))
        (if (i32.eqz) (then (br $scheduler_loop)))
      )
      ;; br main jumps to here
    )
)

(module
  ;; this is a list of function referenced from somewhere, likely jsone
  ;; but having no implementation yet
  ;; if you have nothing better to do, you can try to make one of those work
  (import "erdump" "hexlog_1" (func $hexlog (param i32) (result i32)))

  (func $nop_1 (param $arg1 i32) (result i32)
    (call $hexlog (i32.const 0xDEAD_0001)) (drop)
    (unreachable)
  )

  (func $nop_2 (param $arg1 i32) (param $arg2 i32) (result i32)
    (call $hexlog (i32.const 0xDEAD_0002)) (drop)
    (unreachable)
  )
  (func $nop_3 (param $arg1 i32) (param $arg2 i32) (param $arg3 i32) (result i32)
    (call $hexlog (i32.const 0xDEAD_0003)) (drop)
    (unreachable)
  )

  (export      "maps#from_list_1" (func $nop_1))
  (export      "lists#duplicate_2" (func $nop_2))
  (export      "lists#filter_2" (func $nop_2))
  (export      "lists#sort_1" (func $nop_1))
  (export      "io_lib#format_2" (func $nop_2))
  (export      "unicode#characters_to_binary_1" (func $nop_1))

  (export      "erlang#binary_to_integer_2" (func $nop_2))
  (export      "erlang#binary_to_atom_2" (func $nop_2))
  (export      "erlang#binary_to_existing_atom_2" (func $nop_2))
  (export      "erlang#error_1" (func $nop_1))
  (export      "erlang#error_2" (func $nop_2))
  (export      "erlang#list_to_binary_1" (func $nop_1))
  (export      "erlang#iolist_to_binary_1" (func $nop_1))
  (export      "erlang#float_to_binary_2" (func $nop_2))
  (export      "erlang#integer_to_list_1" (func $nop_1))

  (export      "calendar#universal_time_to_local_time_1" (func $nop_1))
  (export      "calendar#datetime_to_gregorian_seconds_1" (func $nop_1))
)

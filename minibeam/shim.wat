(module
  (func $nop_1 (param $arg1 i32) (result i32)
    (call $module_erdump_fn_hexlog (i32.const 0xDEAD_0001)) (drop)
    (unreachable)
  )

  (func $nop_2 (param $arg1 i32) (param $arg2 i32) (result i32)
    (call $module_erdump_fn_hexlog (i32.const 0xDEAD_0002)) (drop)
    (unreachable)
  )
  (func $nop_3 (param $arg1 i32) (param $arg2 i32) (param $arg3 i32) (result i32)
    (call $module_erdump_fn_hexlog (i32.const 0xDEAD_0003)) (drop)
    (unreachable)
  )

  (export      "maps#from_list_1" (func $nop_1))
  (export      "erlang#binary_to_integer_2" (func $nop_2))
  (export      "erlang#binary_to_atom_2" (func $nop_2))
  (export      "erlang#binary_to_existing_atom_2" (func $nop_2))
  (export      "erlang#error_1" (func $nop_1))
  (export      "erlang#error_2" (func $nop_2))


)

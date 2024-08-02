(module
  (func $pow (param $value_a i32) (param $value_b i32) (result i32)
    (local.get $value_a)
  )

  (export "math#pow_2" (func $pow))
)


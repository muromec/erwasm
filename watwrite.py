from codecs import decode

from write.line import Line
from write.jump import Jump
from write.move import Move
from write.test import Test
from write.byte import BsMatch
from write.ret import Ret
from write.select_val import SelectVal
from write.list import GetList, GetHead, GetTail
from write.call import (
  LocalCall, LocalCallDrop, LocalCallTail,
  ExternalCall, ExternalCallDrop, ExternalCallTail,
)
from write.bif import Bif
from write.block import Label, FuncInfo, BadMatch
from write.regs import Allocate, Trim, VariableMetaNop
from write.proc import Send

from write.utils import make_result_n, make_in_params_n


MODULE = '''(module
   ;; module name: {name}
   {imports}
   (memory 1)
   (export "memory" (memory 0))
   ;; data section
   {data}
   ;; module body
   {body}
)'''

FUNC = '''
(func ${name}_{arity} {params} {result}
{localvars}
{body}
)
'''
FUNC_EXPORT = '''
(export "{mod}#{name}-a{arity}" (func ${name}_{arity}))
'''

LITERAL = '''
  (data (i32.const {offset}) "{value}")
'''
GLOBAL_CONST = '''
  (global ${name} i32 (i32.const {value}))
'''
MEM_NEXT_FREE = '''
  ;; next free memory offset
  (global $__free_mem i32 (i32.const {offset}))
'''

def produce_wasm(module):
  body = ''

  class Ctx:
    labels_to_idx = []
    imports = []
    data = ''
    literalidx = 4

    max_xregs = 1
    max_yregs = 0

    find_function = module.find_function

    depth = 0

  for func in module.functions:
    Ctx.max_xregs = max(int(func.arity), 1)
    Ctx.max_yregs = 0
    if (func.name, func.arity) in module.export_funcs:
      body += FUNC_EXPORT.format(name=func.name, arity=func.arity, mod=module.name)

    b = '\n'

    stack = 0
    arg = int(func.arity)
    while arg > 0:
      b += f'local.get $in_{arg - 1}\n'
      b += f'local.set $var_xreg_{arg - 1}_val\n'
      arg -= 1

    b += f';; arity {func.arity}, input put into X registers\n'

    labels = list([
      statement[1][0]
      for statement in func.statements
      if statement[0] == 'label'
    ])
    labels_to_idx = labels[:]
    jump_depth = labels_to_idx.index(str(func.start_label))

    b += f'(local.set $jump (i32.const {jump_depth}))\n'
    labels0 = list(map(str,range(0, len(labels))))
    labels0 = " ".join(labels0[:])
    b += f'(loop $start\n'
    while labels:
      label = labels.pop()
      b += f'(block $label_{label} \n'

    b += f'(br_table  {labels0} (local.get $jump))\n'
    b += f'unreachable\n'

    current_label = None
    assert func.statements[0][0] == 'function'

    Ctx.labels_to_idx = labels_to_idx

    for statement in func.statements[1:]:
      styp = statement[0]
      sbody = statement[1]

      op_cls = {
        'label': Label,
        'func_info': FuncInfo,
        'line': Line,
        'jump': Jump,
        'move': Move,
        'test': Test,
        'bs_match': BsMatch,
        'return': Ret,
        'select_val': SelectVal,
        'badmatch': BadMatch,

        'allocate': Allocate,
        'trim': Trim,
        '\'%\'': VariableMetaNop,

        'get_list': GetList,
        'get_hd': GetHead,
        'get_tl': GetTail,

        'call': LocalCall,
        'call_only': LocalCallDrop,
        'call_last': LocalCallTail,
        'call_ext': ExternalCall,
        'call_ext_only': ExternalCallDrop,
        'call_ext_last': ExternalCallTail,

        'gc_bif': Bif,

        'send': Send,
      }.get(styp)
      op_imp = op_cls(*sbody) if op_cls else None

      if op_imp:
        b += op_imp.to_wat(Ctx)
      else:
        # assert False, f'No support for {styp} added yet'
        print('not implemented', styp)

    b += ') ;; end of loop\n'
    b += 'unreachable\n';
    assert stack == 0

    localvars = '\n'
    for xreg in range(0, Ctx.max_xregs):
      localvars += f'(local $var_xreg_{xreg}_val i32)\n'

    for yreg in range(0, Ctx.max_yregs):
      localvars += f'(local $var_yreg_{yreg}_val i32)\n'

    localvars += f'(local $temp i32)\n'
    localvars += f'(local $jump i32)\n'

    body += FUNC.format(
      name=func.name,
      arity=func.arity,
      start_label=func.start_label,
      params=make_in_params_n(int(func.arity)),
      result=make_result_n(1),
      localvars=localvars,
      body=b,
    )
  data = MEM_NEXT_FREE.format(
    offset=Ctx.literalidx,
  ) + Ctx.data
  return MODULE.format(
    name=module.name,
    imports="\n".join(Ctx.imports),
    data=data,
    body=body
  )

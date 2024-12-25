import os
#from erparse import parse
from erparse_lark import parse as parse_disasm
from beamread import parse as parse_beam
from watwrite import produce_wasm

def main(fname, fname_out):
  parser = None
  file_mode = 'rt'
  if fname.endswith('.beam'):
    parser = parse_beam
    file_mode = 'rb'
  elif fname.endswith('.S'):
    parser = parse_disasm

  print('compile f', fname, fname_out)
  with open(fname, file_mode) as beam_text_f:
    mod = parser(beam_text_f.read())
    # mod.package = package
    wat_text = produce_wasm(mod)
    with open(fname_out, 'w') as wat_text_f:
      wat_text_f.write(wat_text)

if __name__ == '__main__':
  import sys
  main(*sys.argv[1:])

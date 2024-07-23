import os
from erparse import parse
from watwrite import produce_wasm

def main(fname, fname_out):
  print('compile f', fname, fname_out)
  with open(fname, 'r') as beam_text_f:
    mod = parse(beam_text_f.read())
    # mod.package = package
    wat_text = produce_wasm(mod)
    with open(fname_out, 'w') as wat_text_f:
      wat_text_f.write(wat_text)

if __name__ == '__main__':
  import sys
  main(*sys.argv[1:])

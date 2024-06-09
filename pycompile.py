import os
from erparse import parse
from watwrite import produce_wasm

def main(fname):
  print('compile f', fname)
  input_file = fname
  output_file = fname.replace('.erl', '.S')
  output_wat_file = fname.replace('.erl', '.wat')
  output_wasm_file = fname.replace('.erl', '.wasm')

  try:
    os.remove(output_file)
  except FileNotFoundError:
    pass
  os.system('erlc -S ' + fname)
  with open(output_file, 'r') as beam_text_f:
    mod = parse(beam_text_f.read())
    wat_text = produce_wasm(mod)
    with open(output_wat_file, 'w') as wat_text_f:
      wat_text_f.write(wat_text)

  os.system('wat2wasm ' + output_wat_file)
  os.system('node run.js ' + output_wasm_file)


if __name__ == '__main__':
  import sys
  main(*sys.argv[1:])

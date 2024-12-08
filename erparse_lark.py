from ermod import make_module
from new_parser import parser, BeamTransformer

def parse(beam_text):
  transform = BeamTransformer().transform
  parsed_sentences = parser.parse(beam_text)
  sentences =  transform(parsed_sentences)
  mod = make_module(sentences)
  return mod

def main(fname):
  with open(fname, 'r') as beam_text_f:
    mod = parse(beam_text_f.read())
    # print('mod', mod)

if __name__ == '__main__':
  import sys
  main(*sys.argv[1:])

from ermod import make_module
import os
from codecs import decode
from nodes import Atom, Fun
from beam_parser import Lark_StandAlone, Transformer

# Uncomment the lines below to generate parser in runtime,
# which requires lark as a dependency
# from lark import Lark, Transformer
#def load_grammar():
#  grammar_file = os.path.join(os.path.dirname(__file__), 'beam.g')
#  with open(grammar_file, 'r') as g_file:
#    return g_file.read()
# parser = Lark(load_grammar(), start='module')

parser = Lark_StandAlone()

class BeamTransformer(Transformer):
  def module(self, items):
    return list(items)

  def tuple_statement(self, items):
    return items[0]

  def atom_statement(self, items):
    return (items[0],)

  def statement(self, items):
    (statement,) = items
    return statement

  def list(self, items):
    if items == [None] or items == []:
      return []
    return list(items)

  def tuple(self, items):
    if items == [None] or items == []:
      return ()
    return tuple(items) #[0], items[1:])

  def string(self, items):
    return "".join(items)

  def bare_atom(self, items):
    return "".join(items)

  def escaped_atom(self, items):
    (name,) = items
    return Atom(name)

  def atom(self, items):
    (name,) = items
    return Atom(name)

  def number(self, items):
   return items[0]

  def value(self, items):
    (value,) = items
    return value

  def binary_part(self, items):
    (binary,) = items
    if isinstance(binary, int):
      return bytes([binary])
    return bytes(binary, 'latin1')

  def binary(self, items):
    if items == [None] or items == []:
      return b''
    return b"".join(items)

  def map_pair(self, items):
    assert len(items) == 2
    return tuple(items)

  def map(self, items):
    if items == [None] or items == []:
      return {}
    return dict(items)

  def fun(self, items):
    return Fun(*items)

  def ESCAPED_STRING(self, items):
    return items[1:-1].encode().decode('unicode_escape')

  def ESCAPED_ATOM(self, items):
    return items[1:-1]

  def LCASE_LETTER(self, items):
    return str(items)

  def UCASE_LETTER(self, items):
    return str(items)

  def UNDER(self, items):
    return '_'

  def SIGNED_NUMBER(self, items):
   return int(items, 10)


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

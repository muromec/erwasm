from ermod import make_module

class Atom(str):
  def __repr__(self):
    return f'<atom: {str(self)}>'

def is_num(value):
  return '0' <= value <= '9'

def is_atom(value):
  return ('a' <= value <= 'z') or value == '_' or ('0' <= value <= '9')

def is_atom_start(value):
  return 'a' <= value <= 'z'

def parse_list_sentence_helper(text, State, end_token, depth):
  # print('\t' * depth, 'down at', depth, State.idx)
  ret = []
  state = None
  acc = ''
  while State.idx < len(text):
    symbol = text[State.idx]
    # print('helper', State.idx, symbol, state)
    State.idx += 1

    if state == None and symbol == '{':
      child_sentence = parse_sentence_helper(text, State, depth = depth + 1)
      # print('c', child_sentence)
      ret.append(child_sentence)
    elif state == None and symbol == '[':
      child_sentence = parse_list_sentence_helper(text, State, ']', depth = depth + 1)
      # print('c', child_sentence)
      ret.append(child_sentence)
    elif state == None and is_num(symbol):
      state = 'num'
      acc = symbol
    elif state == 'num' and is_num(symbol):
      acc += symbol
    elif state == 'num' and not is_num(symbol):
      ret.append(int(acc))
      state = None
    elif state == None and is_atom_start(symbol):
      acc = symbol
      state = 'atom'
    elif state == 'atom' and is_atom(symbol):
      acc += symbol
    elif state == 'atom' and not is_atom(symbol):
      ret.append(Atom(acc))
      acc = None
      state = None
    elif state == None and symbol == '\'':
      state = 'atom_quote'
      acc = ''
    elif state == 'atom_quote' and symbol == '\'':
      ret.append(Atom(acc))
      acc = None
      state = None
    elif state == 'atom_quote':
      acc += symbol
    elif state == None and symbol == '"':
      state = 'str'
      acc = ''
    elif state == 'str' and symbol == '"':
      ret.append(acc)
      state = None
      acc = ''
    elif state == 'str' and symbol != '"':
      acc += symbol
    elif state == None and symbol in ['[']:
      assert False, 'cant be!'

    if symbol == end_token:
      break

  if acc and state == 'num':
    ret.append(int(acc))

  if acc and state == 'atom':
    ret.append(Atom(acc))

  # print('\t' * depth, 'up at', State.idx)
  return ret


def clean_v(value):
  if value[0] == '"' and value[-1] == '"':
    value = value[1:-1]
  return value

def parse_sentence_helper(text, State, depth):
  child_sentence = parse_list_sentence_helper(text, State, '}', depth = depth + 1)
  # print('c', '\t' * depth, child_sentence)
  # TODO: remove this
  if isinstance(child_sentence[0], Atom):
    child_sentence_old = (child_sentence[0], list(child_sentence[1:]))
    return child_sentence_old

  return child_sentence


def parse_sentence(text):
  class State:
   idx = 1

  if text == 'return':
    return 'return', []

  if text == 'send':
    return 'send', []

  return parse_sentence_helper(text, State, depth=0)


def parse_beam(text):
  state = None
  ret = []
  sentence = None
  for symbol in text:
    if state == None and symbol == '{':
      state = 'inside'
      sentence = symbol
    elif state == None and symbol == '%':
      state = 'comment'
    elif state == None and (symbol == 'r' or symbol == 's'):
      state = 'inside'
      sentence = symbol
    elif state == 'comment' and symbol == '\n':
      state = None
    elif state == 'inside' and symbol == '.':
      state = None
      ret.append(sentence)
      sentence = None
    elif state == 'inside' and symbol == '"':
      state = 'inside_literal'
      sentence += symbol
    elif state == 'inside_literal' and symbol == '\\':
      state = 'inside_literal_quote'
      sentence += symbol
    elif state == 'inside_literal_quote':
      state = 'inside_literal'
      sentence += symbol
    elif state == 'inside_literal' and symbol == '"':
      state = 'inside'
      sentence += symbol
    elif state == 'inside' or state == 'inside_literal':
      sentence += symbol

  return ret

def parse(beam_text):
  sentences =  parse_beam(beam_text)
  mod = make_module(map(parse_sentence, sentences))
  return mod

def main(fname):
  with open(fname, 'r') as beam_text_f:
    mod = parse(beam_text_f.read())
    # print('mod', mod)

if __name__ == '__main__':
  import sys
  main(*sys.argv[1:])

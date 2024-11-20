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
  had_state = state
  acc = ''
  acc_key = None
  acc_bytes_str = None
  acc_bytes_codes = None
  while State.idx < len(text):
    had_state = state or had_state
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
    elif state == None and symbol == '<':
      state = 'open_bytes'

    elif state == 'open_bytes' and symbol == '<':
      state = 'bytes'
      acc = b''
      acc_bytes_codes = ''
    elif state == 'bytes' and symbol == '>':
      state = 'close_bytes'
      ret.append(acc)
      acc = None
    elif state == 'close_bytes' and symbol == '>':
      state = None
    elif state == 'bytes_str' and symbol == '\\':
      state = 'bytes_str_quote'
    elif state == 'bytes_str' and symbol == '"':
      state = 'bytes'
      acc += acc_bytes_str
      acc_bytes_str = None
    elif state == 'bytes_str' or state == 'bytes_str_quote':
      state = 'bytes_str'
      acc_bytes_str += bytes(symbol, 'utf8')
    elif state == 'bytes' and symbol == '"':
      state = 'bytes_str'
      acc_bytes_str = b''
    elif state == 'bytes' and is_num(symbol):
      acc_bytes_codes += symbol
    elif state == 'bytes' and symbol == ',':
      acc += bytes([int(acc_bytes_codes, 10)])
      acc_bytes_codes = ''
    elif state == 'bytes':
      assert False
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
    elif state == None and symbol == "'":
      state = 'atom_quote'
      acc = ''
    elif state == 'atom_quote' and symbol == "'":
      ret.append(Atom(acc))
      acc = None
      state = None
    elif state == 'atom_quote':
      acc += symbol
    elif state == None and symbol == '#':
      state = 'dict'
      acc = {}
      acc_key = ''
    elif state == 'dict'and symbol == '{':
      pass
    elif state == 'dict' and is_atom(symbol):
      acc_key += symbol
      state = 'dict_key'
    elif state == 'dict_key' and is_atom(symbol):
      acc_key += symbol
    elif state == 'dict_key' and not is_atom(symbol):
      state = 'dict'
    elif state == 'dict' and symbol == '=':
      pass
    elif state == 'dict' and symbol == '>':
      [ value ] = parse_list_sentence_helper(text, State, None, depth = depth + 1)
      acc[acc_key] = value
      acc_key = ''
    elif state == 'dict' and symbol == '}':
      ret.append(acc)
      acc = None
      state = None
      continue
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

    if state == None and symbol == end_token:
      break

    if end_token == state and ret:
      break

  if acc and state == 'num':
    ret.append(int(acc))

  if acc and state == 'atom':
    ret.append(Atom(acc))

  if acc and state == 'dict':
    ret.append(acc)

  # print('\t' * depth, 'up at', State.idx)
  return ret


def clean_v(value):
  if value[0] == '"' and value[-1] == '"':
    value = value[1:-1]
  return value

def parse_sentence_helper(text, State, depth):
  child_sentence = parse_list_sentence_helper(text, State, '}', depth = depth)
  # print('c', '\t' * depth, child_sentence)
  # TODO: remove this
  if not child_sentence:
    return child_sentence
  if isinstance(child_sentence[0], Atom):
    child_sentence_old = (child_sentence[0], list(child_sentence[1:]))
    return child_sentence_old

  return tuple(child_sentence)


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
    elif state == 'inside' and symbol == '\'':
      state = 'inside_atom'
      sentence += symbol
    elif state == 'inside_atom' and symbol == '\\':
      state = 'inside_atom_esc'
    elif state == 'inside_atom_esc':
      state = 'inside_atom'
      sentence += symbol
    elif state == 'inside_atom' and symbol == '\'':
      state = 'inside'
      sentence += symbol
    elif state == 'inside_atom':
      sentence += symbol
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

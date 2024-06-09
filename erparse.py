from ermod import make_module

def parse_list_sentence_helper(text, State):
  ret = []
  state = None
  while State.idx < len(text):
    symbol = text[State.idx]
    State.idx += 1
    if symbol == ']':
      break
    elif state == None and symbol == '{':
      child_sentence = parse_sentence_helper(text, State)
      ret.append(child_sentence)
    elif state == None and symbol in ['[', '"']:
      assert False, 'cant be!'

  return ret


def clean_v(value):
  if value[0] == '"' and value[-1] == '"':
    value = value[1:-1]
  return value

def parse_sentence_helper(text, State):
  state = 'name'
  ret = []
  sentence = None
  name = ''
  children = []
  arg_name = ''

  while State.idx < len(text):
    symbol = text[State.idx]
    State.idx += 1
    if symbol == '}':
      break
    elif state == 'name' and symbol not in [' ', ',']:
      name += symbol
    elif state == 'name':
      state = None
    elif state == None and symbol in [' ', ',']:
      pass
    elif state == None and symbol == '[':
      child_sentence = parse_list_sentence_helper(text, State)
      children.append(child_sentence)
    elif state == None and symbol == '{':
      child_sentence = parse_sentence_helper(text, State)
      children.append(child_sentence)
    elif state == None:
      state = 'arg_name'
      arg_name = symbol
    elif state == 'arg_name' and symbol in [' ', ',']:
      children.append(clean_v(arg_name))
      state = None
      arg_name = None
    elif state == 'arg_name':
      arg_name += symbol
    
  if arg_name:
    children.append(clean_v(arg_name))

  return name, children

def parse_sentence(text):
  class State:
   idx = 1

  return parse_sentence_helper(text, State)


def parse_beam(text):
  state = None
  ret = []
  sentence = None
  for symbol in text:
    if state == None and symbol == '{':
      state = 'inside'
      sentence = symbol
    elif state == 'inside' and symbol == '.':
      state = None
      ret.append(sentence)
      sentence = None
    elif state == 'inside' and symbol == '"':
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


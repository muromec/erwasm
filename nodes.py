
class Atom(str):
  def __repr__(self):
    return f'<atom: {str(self)}>'

class Fun:
  def __init__(self, mod, name, arity):
    self.mod = mod
    self.name = name
    self.arity = arity

  def __repr__(self):
    return f'<fun: {self.mod}#{self.name}/{self.arity}>'



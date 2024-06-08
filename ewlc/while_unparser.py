# ------------------------------------------------------------
# while_unparser.py
#
# unparser for the extended WHILE language
# ------------------------------------------------------------
# The unparser is part of the AST :D
from while_ast import unparse as _unparse

class WhileUnparser(object):
  def unparse(self, ast):
    return _unparse(ast)

# Test on a simple program
if __name__ == '__main__':
  from while_parser import WhileParser
  code = """
    def func (a b c) -> (x y) {
      x := a + 1;
      y := b + 3;
      skip;
      if x == y {a := 4}
      else {b := 5;}
      while true {
        x := y;
        m := 3;
        for i in [x .. b+4] {
          x := x + i;
        }
        break;
      }
    }
  """
  parser = WhileParser()
  unparser = WhileUnparser()
  ast = parser.parse(code)
  raw = unparser.unparse(ast)
  print(raw)
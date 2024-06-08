# ------------------------------------------------------------
# while_lexer.py
#
# tokenizer for the extended WHILE language
# ------------------------------------------------------------
import ply.lex as lex

class WhileLexer(object):
  # Build the lexer
  def __init__(self, **kwargs):
    self.lexer = lex.lex(module=self, **kwargs)
  
  def input(self, *args, **kwargs):
    self.lexer.lineno = 1
    return self.lexer.input(*args, **kwargs)

  def token(self):
    return self.lexer.token()
  
  # List of reserved identifiers
  reserved = {
    'def' : 'DEF', 'skip' : 'SKIP',
    'if' : 'IF', 'else' : 'ELSE',
    'true' : 'BOOL', 'false' : 'BOOL',
    'continue' : 'CONTINUE', 'break' : 'BREAK',
    'for' : 'FOR', 'in' : 'IN',
    'while' : 'WHILE'
  }

  # List of tokens
  tokens = [
    'TO', 'SEMICOLON', 'ELLIPSES',
    'ID', 'NUMBER',
    'PLUS','MINUS',
    'TIMES', 'DIVIDE',
    'LPAREN', 'RPAREN',
    'LCURLY', 'RCURLY',
    'LBRACK', 'RBRACK',
    'ASSIGN', 'EQUALS',
    'LESS', 'GREATER'
  ] + list(set(reserved.values()))

  # Simple token rules
  t_TO, t_SEMICOLON  = r'->', r';'
  t_ELLIPSES         = r'\.\.'
  t_PLUS, t_MINUS    = r'\+', r'-'
  t_TIMES, t_DIVIDE  = r'\*', r'/'
  t_LPAREN, t_RPAREN = r'\(', r'\)'
  t_LCURLY, t_RCURLY = r'\{', r'\}'
  t_LBRACK, t_RBRACK = r'\[', r'\]'
  t_ASSIGN, t_EQUALS = r':=', r'=='
  t_LESS, t_GREATER  = r'<', r'>'

  # Variables / identifiers rule
  def t_ID(self, t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = WhileLexer.reserved.get(t.value, 'ID') # Check for reserved words
    if t.type == 'BOOL':
      t.value = (t.value == 'true')
    return t

  # Numbers rule
  def t_NUMBER(self, t):
    r'\d+'
    t.value = int(t.value)
    return t

  # Ignored characters (spaces, tabs, newlines)
  t_ignore  = ' \t'
  t_ignore_COMMENT = r'\#.*'
  def t_newline(self, t):
    r'\n+'
    t.lexer.lineno += len(t.value)

  # Error handling rule
  def t_error(self, t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

# Test on a simple program
if __name__ == '__main__':
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
  wl = WhileLexer()
  wl.input(code)
  while True:
    t = wl.token()
    if not t: break
    print(t)
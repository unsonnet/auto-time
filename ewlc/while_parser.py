# ------------------------------------------------------------
# while_parser.py
#
# parser for the extended WHILE language
# ------------------------------------------------------------
import ply.yacc as yacc
import while_ast as AST

# Get the token map and build the lexer
from while_lexer import WhileLexer

# Extended While language parser
class ParsingError(Exception): pass
class WhileParser(object):
  tokens = WhileLexer.tokens

  # Build the parser
  def __init__(self, **kwargs):
    self.lexer = WhileLexer()
    self.parser = yacc.yacc(module=self, **kwargs)
  
  def parse(self, *args, **kwargs):
    self.context = [dict()]
    self.last_scope = None
    self.indices = []
    self.loop_depth = 0
    return self.parser.parse(*args, lexer=self.lexer, **kwargs)
  
  # Starting symbol
  # AST > DEF(fun, inp, out, body)
  def p_prog(self, p):
    '''prog : DEF ID LPAREN vars RPAREN TO LPAREN _begin_scope vars _end_scope RPAREN body'''
    p[0] = AST.DEF(p[2], p[4], p[9], p[12], p.lineno(1))
    missing = list(set(map(repr,p[0].node.out)) - set(self.last_scope))
    if missing:
      if len(missing) == 1: self.p_error(f'Output variable {missing[0]} is undefined')
      else: self.p_error(f'Output variables {", ".join(missing)} are undefined')

  # Parse input / output variables
  # AST > [id_1, ..., id_n]
  def p_vars(self, p):
    '''vars :'''
    p[0] = []

  def p_vars_chain(self, p):
    '''vars : var vars'''
    if p[1] in p[2]:
      kind = "Input" if len(self.context) == 1 else "Output"
      self.p_error(f'{kind} variable {p[1]} at line {p[1].line} is repeated')
    p[0] = [p[1]] + p[2]
  
  # Parse body
  # AST > BODY(exp)
  def p_body(self, p):
    '''body : LCURLY _begin_scope exp _end_scope RCURLY'''
    p[0] = AST.BODY(p[3])
  
  def p__begin_scope(self, p):
    '''_begin_scope :'''
    self.context.append(dict())
  
  def p__end_scope(self, p):
    '''_end_scope :'''
    self.last_scope = self.context.pop().keys()

  # Parse expressions
  # AST > [(stmt | ctrl)_1, ..., (stmt | ctrl)_n]
  def p_exp(self, p):
    '''exp :
           | stmt'''
    p[0] = [] if len(p) == 1 else [p[1]]

  def p_exp_chain(self, p):
    '''exp : ctrl exp
           | stmt SEMICOLON exp'''
    end = p[2] if len(p) == 3 else p[3]
    p[0] = [p[1]] + end

  # Parse statement
  # AST > SKIP() | ASSIGN(var, aexp) | BREAK() | CONTINUE()
  def p_stmt(self, p):
    '''stmt : SKIP
            | var ASSIGN aexp'''
    p[0] = AST.SKIP(p.lineno(1)) if len(p) == 2 else AST.ASSIGN(p[1], p[3], p.lineno(2))

  def p_stmt_jump(self, p):
    '''stmt : BREAK
            | CONTINUE'''
    if self.loop_depth < 1: self.p_error(f'{p[1].capitalize()} at line {p.lineno(1)} is outside of a loop')
    p[0] = AST.JUMP(p[1], p.lineno(1))

  # Parse control
  # AST > IF(cond, if_true, if_false) | WHILE(cond, while_true) | FOR(var, start, end, for_each)
  def p_ctrl(self, p):
    '''ctrl : IF bexp body
            | IF bexp body ELSE body'''
    if_false = AST.BODY([]) if len(p) == 4 else p[5]
    p[0] = AST.IF(p[2], p[3], if_false, p.lineno(1))
    
  def p_ctrl_loop(self, p):
    '''ctrl : WHILE bexp _begin_loop body _end_loop
            | FOR idx IN LBRACK aexp ELLIPSES aexp RBRACK _push_idx _begin_loop body _end_loop _pop_idx'''
    if len(p) == 6: p[0] = AST.WHILE(p[2], p[4], p.lineno(1))
    else: p[0] = AST.FOR(p[2], p[5], p[7], p[11], p.lineno(1))
  
  def p__begin_loop(self, p):
    '''_begin_loop :'''
    self.loop_depth = self.loop_depth + 1
  
  def p__end_loop(self, p):
    '''_end_loop :'''
    self.loop_depth = self.loop_depth - 1

  def p_idx(self, p):
    '''idx : new_var'''
    p[0] = p[1]
    self.indices.append(self.context[-1].pop(p[1].id))

  def p__pop_idx(self, p):
    '''_pop_idx :'''
    idx = self.indices.pop()
    self.context[-1].pop(idx.id)

  def p__push_idx(self, p):
    '''_push_idx :'''
    idx = self.indices[-1]
    self.context[-1][idx.id] = idx

  # Parse arithmetic expression following PEMDAS and associating on the left
  # AST > id | num | AEXP(left, op, right) | NEG(operand)
  def p_aexp(self, p):
    '''aexp : term
            | aexp PLUS term
            | aexp MINUS term'''
    p[0] = p[1] if len(p) == 2 else AST.AEXP(p[1], p[2], p[3])

  def p_term(self, p):
    '''term : fact
            | term TIMES fact
            | term DIVIDE fact'''
    p[0] = p[1] if len(p) == 2 else AST.AEXP(p[1], p[2], p[3])

  def p_fact(self, p):
    '''fact : old_var
            | num
            | MINUS aexp
            | LPAREN aexp RPAREN'''
    p[0] = p[len(p)//2] if len(p) != 3 else AST.AEXP(0, '-', p[2])
  
  def p_num(self, p):
    '''num : NUMBER'''
    p[0] = AST.NUM(p[1])

  # Parse boolean expression
  # AST > bool | BEXP(left, rel, right)
  def p_bexp(self, p):
    '''bexp : BOOL
            | aexp rel aexp'''
    p[0] = AST.BOOL(p[1]) if len(p) == 2 else AST.BEXP(p[1], p[2], p[3])

  def p_rel(self, p):
    '''rel : EQUALS
           | LESS
           | GREATER'''
    p[0] = p[1]

  # Parse variables and handle scoping
  def p_var(self, p):
    '''var : ID'''
    for scope in self.context:
      if p[1] in scope:
        p[0] = scope[p[1]]
        return
    self.context[-1][p[1]] = AST.VAR(p[1], p.lineno(1))
    p[0] = self.context[-1][p[1]]

  def p_new_var(self, p):
    '''new_var : ID'''
    for scope in self.context:
      if p[1] in scope:
        self.p_error(f'Index {p[1]} at line {p.lineno(1)} already exists')
    self.context[-1][p[1]] = AST.VAR(p[1], p.lineno(1))
    p[0] = self.context[-1][p[1]]
  
  def p_old_var(self, p):
    '''old_var : ID'''
    for scope in self.context:
      if p[1] in scope:
        p[0] = scope[p[1]]
        return
    self.p_error(f'Variable {p[1]} at line {p.lineno(1)} is undefined')

  # Handle errors
  def p_error(self, p):
    if isinstance(p, str): raise ParsingError(p)
    if p == None: raise ParsingError('Input ended unexpectedly')
    raise ParsingError(f'Token "{p.value}" at line {p.lineno} was unexpected')

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
  parser = WhileParser()
  result = parser.parse(code)
  print(result)
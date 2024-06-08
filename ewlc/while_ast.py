# ------------------------------------------------------------
# while_ast.py
#
# Abstract Syntax Tree for the extended WHILE language
# ------------------------------------------------------------
import while_cfg as CFG
from collections import namedtuple
from sympy import Symbol, Eq, parse_expr

def unparse(v):
  if isinstance(v, NODE):
    return v.unparse()
  if isinstance(v, list):
    return list(map(unparse, v))
  return str(v)

class NODE(object):
  def __init__(self, line=None, label='NODE', **kwargs):
    self.line, self.label = line, label
    self.node = namedtuple(label, kwargs.keys())(**kwargs)
  def __eq__(self, obj):
    return repr(self) == repr(obj)
  def __repr__(self):
    return repr(self.node)
  def unparse(self):
    raise NotImplementedError
  def bytecode(self):
    raise NotImplementedError

class DEF(NODE):
  def __init__(self, fun, inp, out, body, line=None):
    super().__init__(line, 'DEF', fun=fun, inp=inp, out=out, body=body)
  def unparse(self):
    fun, inp, out, body = map(unparse, self.node)
    return f'def {fun} ({" ".join(inp)}) -> ({" ".join(out)}) {body}'
  def bytecode(self):
    return self.node.body.bytecode() + [CFG.NODE('END')]

class BODY(NODE):
  def __init__(self, exp):
    super().__init__(None, 'BODY', exp=exp)
  def unparse(self):
    exp, = map(unparse, self.node)
    return f'{{{" ".join(exp)}}}'
  def bytecode(self):
    return sum(map(lambda v : v.bytecode(), self.node.exp), [])

class SKIP(NODE):
  def __init__(self, line=None):
    super().__init__(line, 'SKIP')
  def unparse(self):
    return 'skip;'
  def bytecode(self):
    return []

class ASSIGN(NODE):
  def __init__(self, var, aexp, line=None):
    super().__init__(line, 'ASSIGN', var=var, aexp=aexp)
  def unparse(self):
    var, aexp = map(unparse, self.node)
    return f'{var} := {aexp};'
  def bytecode(self):
    return [CFG.ASSIGN(self.node.var.reify(), self.node.aexp.reify())]

class JUMP(NODE):
  def __init__(self, kind, line=None):
    super().__init__(line, kind.upper())
  def unparse(self):
    return f'{self.label.lower()};'
  def bytecode(self):
    return [self.label]

class IF(NODE):
  def __init__(self, cond, if_true, if_false, line=None):
    super().__init__(line, 'IF', cond=cond, if_true=if_true, if_false=if_false)
  def unparse(self):
    cond, if_true, if_false = map(unparse, self.node)
    return f'if {cond} {if_true} else {if_false}'
  def bytecode(self):
    if_false = self.node.if_false.bytecode()
    if_true = self.node.if_true.bytecode() + [CFG.JUMP(len(if_false)+1)]
    cond = [CFG.CONDJUMP(self.node.cond.reify(), len(if_true)+1)]
    return cond + if_true + if_false

class WHILE(NODE):
  def __init__(self, cond, while_true, line=None):
    super().__init__(line, 'WHILE', cond=cond, while_true=while_true)
  def unparse(self):
    cond, while_true = map(unparse, self.node)
    return f'while {cond} {while_true}'
  def bytecode(self):
    while_true = self.node.while_true.bytecode()
    while_true += [CFG.JUMP(-len(while_true)-1)]
    for i in range(len(while_true)):
      if while_true[i] == 'CONTINUE': while_true[i] = CFG.JUMP(-i-1)
      if while_true[i] == 'BREAK': while_true[i] = CFG.JUMP(len(while_true)-i)
    cond = [CFG.CONDJUMP(self.node.cond.reify(), len(while_true)+1, loops=True)]
    return cond + while_true

class FOR(NODE):
  def __init__(self, idx, start, end, for_each, line=None):
    super().__init__(line, 'FOR', idx=idx, start=start, end=end, for_each=for_each)
  def unparse(self):
    idx, start, end, for_each = map(unparse, self.node)
    return f'for {idx} in [{start}..{end}] {for_each}'
  def bytecode(self):
    idx, start, end, for_each = self.node
    k, lim = VAR(idx.id + '_k'), VAR(idx.id + '_lim')
    desugar = BODY([
      ASSIGN(k, start),
      ASSIGN(lim, AEXP(end, '+', NUM(1))),
      WHILE(
        BEXP(k, '<', lim),
        BODY([
          ASSIGN(idx, k),
          ASSIGN(k, AEXP(k, '+', NUM(1)))
        ] + for_each.node.exp),
        self.line
      )
    ])
    return desugar.bytecode()

class AEXP(NODE):
  def __init__(self, left, op, right):
    super().__init__(label='AEXP', left=left, op=op, right=right)
  def unparse(self):
    left, op, right = map(unparse, self.node)
    return f'({left} {op} {right})'
  def reify(self):
    op = {'+' : lambda l, r : l + r,
          '-' : lambda l, r : l - r,
          '*' : lambda l, r : l * r,
          '/' : lambda l, r : l / r}
    return op[self.node.op](self.node.left.reify(), self.node.right.reify())

class VAR(object):
  def __init__(self, id, line=None):
    self.id, self.line = id, line
    self.sym = Symbol(self.id)
  def __repr__(self):
    return self.id
  def reify(self):
    return self.sym

class NUM(object):
  def __init__(self, val):
    self.val = parse_expr(repr(val))
  def __repr__(self):
    return repr(self.val)
  def reify(self):
    return self.val

class BEXP(NODE):
  def __init__(self, left, rel, right):
    super().__init__(label='BEXP', left=left, rel=rel, right=right)
  def unparse(self):
    left, rel, right = map(unparse, self.node)
    return f'{left} {rel} {right}'
  def reify(self):
    rel = {'==' : lambda l, r : Eq(l,r),
            '<' : lambda l, r : l < r,
            '>' : lambda l, r : l > r}
    cond = rel[self.node.rel](self.node.left.reify(), self.node.right.reify())
    return cond

class BOOL(object):
  def __init__(self, val):
    self.val = val
  def __repr__(self):
    return repr(self.val).lower()
  def reify(self):
    return self.val
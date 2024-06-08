# ------------------------------------------------------------
# while_cfg.py
#
# Control Flow Graph for the extended WHILE language
# ------------------------------------------------------------
from collections import namedtuple, defaultdict

def construct_cfg(ast):
  cfg, bytecode = [], ast.bytecode()
  for i, u in enumerate(bytecode[:-1]):
    if isinstance(u, JUMP): continue

    j = i+1
    while isinstance(bytecode[j], JUMP):
      j += bytecode[j].node.delta
    bytecode[j].enter.append(u)
    u.exit = bytecode[j] # if_true / while_true

    if isinstance(u, CONDJUMP):
      j = i+u.node.delta
      while isinstance(bytecode[j], JUMP):
        j += bytecode[j].node.delta
      bytecode[j].enter.append(u)
      u.diverge = bytecode[j] # if_false / while_break

    cfg.append(u)

  cfg.append(bytecode[-1])
  return cfg

def visualize_cfg(cfg, file='cfg.png'):
  try:
    import pygraphviz as pgv
  except Exception:
    print("ImportError : Unable to load PyGraphViz for visualizing the control flow graph. Make sure to have PyGraphViz, GraphViz, and a C/C++ compiler installed to use this utility.")
    return

  G = pgv.AGraph(directed=True)
  
  to_visit, visited = set([(0,cfg[0])]), set()
  while to_visit:
    i, u = to_visit.pop(); visited.add(u)
    if not u.exit: continue
    j, v = cfg.index(u.exit), u.exit
    G.add_edge(f'[{u}]^{i+1}', f'[{v}]^{j+1}', color='black')
    G.get_node(f'[{u}]^{i+1}').attr['label'] = ''
    G.get_node(f'[{v}]^{j+1}').attr['label'] = ''
    if not (v in visited): to_visit.add((j,v))
    if isinstance(u, CONDJUMP):
      j, v = cfg.index(u.diverge), u.diverge
      G.add_edge(f'[{u}]^{i+1}', f'[{v}]^{j+1}', color='red' if u.loops else 'blue')
      G.get_node(f'[{u}]^{i+1}').attr['label'] = ''
      G.get_node(f'[{v}]^{j+1}').attr['label'] = ''
      if not (v in visited): to_visit.add((j,v))
  
  G.node_attr['shape'] = 'circle'
  G.node_attr['width'] = '.2'
  G.node_attr['height'] = '.2'
  G.draw(file, args='-Gratio=1', prog='dot')

def negate(cond):
  return not cond if isinstance(cond, bool) else ~cond

class NODE(object):
  def __init__(self, label='NODE', **kwargs):
    self.label, self.enter, self.exit = label, [], None
    self.node = namedtuple(label, kwargs.keys())(**kwargs)
  def __repr__(self):
    return repr(self.node)

class JUMP(NODE):
  def __init__(self, delta):
    super().__init__('JUMP', delta=delta)

class ASSIGN(NODE):
  def __init__(self, var, aexp):
    super().__init__('ASSIGN', var=var, aexp=aexp)
  def __repr__(self):
    return f'{self.node.var} := {self.node.aexp}'

class CONDJUMP(NODE):
  def __init__(self, cond, delta, loops=False):
    super().__init__('CONDJUMP', cond=cond, delta=delta)
    self.loops, self.diverge, self.may_recur = loops, None, 0
  def __repr__(self):
    return f'{self.node.cond}'

class MEMO(NODE):
  def __init__(self, cond):
    super().__init__('MEMO', cond=cond)
    self.cont = []
    self.memo = lambda z : z
  def __repr__(self):
    return f'LOOP({self.node.cond})'

# Test on a simple program
if __name__ == '__main__':
  from while_parser import WhileParser
  import while_cfg as CFG # Fix double import trap in main
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
          if x == y {break;}
          else {z := 1;}
        }
        m := 4;
        break;
      }
      z := 1
    }
  """
  parser = WhileParser()
  result = parser.parse(code)
  cfg = CFG.construct_cfg(result)
  print(result.bytecode())
  print(cfg)

  # Visualize graph
  CFG.visualize_cfg(cfg)
# ------------------------------------------------------------
# while_analysis.py
#
# Big-O value analysis for the extended WHILE language
# ------------------------------------------------------------
import while_cfg as CFG
from collections import defaultdict

class BigO(dict):
  def __init__(self, branch=None, *args, **kwargs):
    super(BigO, self).__init__(*args, **kwargs)
    self.branch = branch
  def __getitem__(self, key):
    try: return super().__getitem__(key)
    except Exception: super().__setitem__(key, key); return key
  def __call__(self, O):
    assert isinstance(O, BigO)
    res = self.copy()
    for key in res:
      res[key] = res[key].subs(O)
    for key in O:
      if not res.has_key(key): res[key] = O[key]
    return res
  def copy(self, branch=None):
    res = BigO(branch=branch if branch else self.branch)
    for k,v in self.items():
      res[k] = v
    return res
  def has_key(self, key):
    try: self[key]; return True
    except Exception: return False

def extract_BigO(root, cfg):
  Os = [[] for _ in cfg]
  queue = [(root, BigO())]
  while queue:
    u, O = queue.pop()
    Os[cfg.index(u)].append(O)
    if isinstance(u, CFG.ASSIGN):
      f = BigO(); f[u.node.var] = u.node.aexp
      queue.append((u.exit, f(O)))
    elif isinstance(u, CFG.CONDJUMP):
      if u.loops:
        if O.branch == u: pass
        else: queue.append((u.exit, O.copy(O.branch if O.branch else u)))
      else:
        queue.extend([(u.exit, O.copy()), (u.diverge, O.copy())])
    elif isinstance(u, CFG.MEMO):
      queue.append((u.exit, u.memo(O.copy())))
      for v in u.cont: queue.append((v, O.copy()))
    else:
      pass
  return Os

def analyze(cfg):
  CFG.visualize_cfg(cfg, 'cfg_start.png')

  # Identify loops and precompute their recurrence relationship
  loops, visited = defaultdict(list), set([None])
  def trace_loop(u, end=None, depth=0):
    nonlocal cfg, loops, visited

    branches = []
    valid = lambda w : w not in visited and w != end
    to_visit = set([u.exit] if valid(u.exit) else [])
    while to_visit:
      v = to_visit.pop(); visited.add(v)
      if isinstance(v, CFG.CONDJUMP):
        if not v.loops: branches.append(v)
        else: loops[depth].append((v, trace_loop(v, v.diverge, depth+1)))
        if valid(v.diverge): to_visit.add(v.diverge)
      if valid(v.exit): to_visit.add(v.exit)
    
    return branches

  # Identify breakpoints in loop
  def find_breakpoints(u, branches):
    # Trace the relationship between conditional jumps
    queue, trace = [(u, False, u.exit)], []
    while queue:
      cond, diverged, end = queue.pop()
      if end == u: continue
      if not (end == u.diverge or end in branches): queue.append((cond, diverged, end.exit))
      else:
        trace.append((cond, diverged, end)); cond.may_recur = 2
        if end in branches: queue.extend([(end, False, end.exit), (end, True, end.diverge)])

    # Backpropagate loop breaks up the trace
    trace.reverse()
    flip = []
    for cond, diverged, end in trace:
      if cond in flip:
        diverged = not diverged
        flip.remove(cond)
      if (cond.loops and diverged) or (end in branches and (end.loops or not end.may_recur)):
        cond.may_recur -= 1
        continue
      cond.loops = not cond.loops
      if not diverged:
        cond.exit, cond.diverge = cond.diverge, cond.exit
        cond.node = cond.node._replace(cond = CFG.negate(cond.node.cond))
        flip.append(cond)
    
    return [branch for branch in ([u] + branches) if branch.loops]

  def compute_recurrence(u):
    # find_divergences(u, branches)
    pass

  trace_loop(cfg[0])
  loops = list(loops.values()); loops.reverse()
  if not loops:
    print("  No loops were found.")

  for level in loops:
    for u, branches in level:
      breaks = find_breakpoints(u, branches)
      CFG.visualize_cfg(cfg, f'cfg_{cfg.index(u)+1}.png')
      print(f"  Analyzing loop at label {cfg.index(u)+1}")
      if not breaks:
        print(f"    - There are no cycles and hence no breakpoints.")
        continue

      # end = CFG.NODE('END')
      # for v in u.diverge.enter:
      #   if v.exit == u: v.exit = end
      #   else: v.diverge = end
      #   if 

      # u.diverge
      # compute_recurrence(u, cfg)
      print(f"    + The breakpoints are at labels: {[cfg.index(brk)+1 for brk in breaks]}")

      # memoize the result
      i = cfg.index(u)
      cfg[i] = CFG.MEMO(cond=u.node.cond)
      cfg[i].enter, cfg[i].exit = u.enter, u.diverge
      for w in cfg[i].enter:
        if w.exit == u: w.exit = cfg[i]
        else: w.diverge = cfg[i]      

  # print(f"{loops}")
  CFG.visualize_cfg(cfg, 'cfg_end.png')

# Test on a simple program
if __name__ == '__main__':
  from while_parser import WhileParser
  parser = WhileParser()
  
  code = """
    def func (a b c) -> (x y) {
      x := a + 1;
      y := b + 3;
      if x == y {a := 4}
      else {b := 5;}
      z := 3;
      while true {
        x := y;
        if x == y + 1 {a := 4}
        else {b := 5;}
        m := 3;
        if x == y {x := y;}
        else {y := 3;}
        while m < 3 {
          if x == m {break;}
          if x == m + 1 {x := m + 1;}
        }
        for i in [x .. b+4] {
          x := x + i;
          if x == i {break;}
          else {x := x; break;}
        }
        m := 3;
      }
    }
  """

  ast = parser.parse(code)
  cfg = CFG.construct_cfg(ast)
  analyze(cfg)
  
  # from sympy import Symbol
  # from sympy.parsing.sympy_parser import parse_expr
  # i = Symbol("i")
  # k = Symbol("k")
  # m = Symbol("m")
  # d,h = BigO(), BigO()
  # d[i] = k; d[k] = parse_expr("2"); d[m]
  # h[i] = i+1; h[k] = parse_expr("1")
  # print(d,h)
  # print(h(d))

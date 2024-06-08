import argparse
parser = argparse.ArgumentParser(description="Extended While Language Parser and Analyzer")
parser.add_argument("file", help="A .ewl file to be parsed")
parser.add_argument("-a", "--ast", dest="ast", action="store_true",
                    help="Generate the abstract syntax tree for the eWL program.")
parser.add_argument("-c", "--cfg", dest="cfg", action="store_true",
                    help="Generate the control flow graph for the eWL program.")
parser.add_argument("-z", "--analyze", dest="analyze", action="store_true",
                    help="Analyze the eWL program's recursive structure.")

args = parser.parse_args()
eWL = args.file
with open(eWL, 'r') as file:
  code = file.read()
cmd_ast = args.ast
cmd_cfg = args.cfg
cmd_analyze = args.analyze

from while_parser import WhileParser
from while_cfg import construct_cfg, visualize_cfg
from while_analysis import analyze

parser = WhileParser()
ast = parser.parse(code)
cfg = construct_cfg(ast)

if cmd_ast:
  print(f"The Abstract Syntax Tree for {eWL} is:\n")
  print(ast)
  print()

if cmd_cfg:
  print(f"The bytecode for {eWL} is:\n")
  print(cfg)
  visualize_cfg(cfg, "cfg.png")
  print()
  print(f"The control flow graph is stored in cfg.png")
  print()

if cmd_analyze:
  print(f"Recursive structure analysis for {eWL} is:\n")
  analyze(cfg)
  print()
  print(f"The steps in compressing the control flow graph is stored in cfg_<label>.png")
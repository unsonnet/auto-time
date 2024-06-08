# ------------------------------------------------------------
# while_tests.py
#
# unit tests for the extended WHILE language (un)parser
# ------------------------------------------------------------
from while_parser import WhileParser
from while_unparser import WhileUnparser

parser = WhileParser()
unparser = WhileUnparser()

class positive_tests(object):
  def test_01():
    print("Check def works")
    code = """
      def f01 (a b c) -> () {
        skip;
      }
    """
    ast = parser.parse(code)
    print(ast == parser.parse(unparser.unparse(ast)), end='\n\n')

  def test_02():
    print("Check assignment works")
    code = """
      def f02 (a) -> (x y) {
        x := a;
        y := x;
      }
    """
    ast = parser.parse(code)
    print(ast == parser.parse(unparser.unparse(ast)), end='\n\n')

  def test_03():
    print("Check PEMDAS works")
    code = """
      def f03 (a b) -> (x) {
        x := a + 2 * (b - 7);
      }
    """
    ast = parser.parse(code)
    print(ast == parser.parse(unparser.unparse(ast)), end='\n\n')

  def test_04():
    print("Check if/else works")
    code = """
      def f04 (a b) -> (x) {
        x := 1;
        if a < b {x := a}
        else {x := b;}
      }
    """
    ast = parser.parse(code)
    print(ast == parser.parse(unparser.unparse(ast)), end='\n\n')

  def test_05():
    print("Check while works")
    code = """
      def f05 (a b c) -> (x y) {
        x := a + b;
        y := 0;
        while x < c {
          x := 2 * x;
          y := y + 1;
        }
      }
    """
    ast = parser.parse(code)
    print(ast == parser.parse(unparser.unparse(ast)), end='\n\n')

  def test_06():
    print("Check for works")
    code = """
      def f06 (a b c) -> (x y z) {
        x := 0;
        y := 0;
        z := 0;
        for i in [a+b .. a*b+c] {
          x := i;
          y := i * i;
          z := x + y;
        }
      }
    """
    ast = parser.parse(code)
    print(ast == parser.parse(unparser.unparse(ast)), end='\n\n')

  def test_07():
    print("Check nested loops work")
    code = """
      def f07 (a b c) -> (x y z) {
        x := 0;
        y := 0;
        z := 0;
        for i in [a+b .. a*b+c] {
          x := i * i + 3;
          while x < c {
            y := x + 2;
            z := y * y;
          }
        }
      }
    """
    ast = parser.parse(code)
    print(ast == parser.parse(unparser.unparse(ast)), end='\n\n')

  def test_08():
    print("Check break/continue work")
    code = """
      def f08 (a b c) -> (x) {
        x := a;
        while true {
          x := x + b;
          if x < c {break;}
          else {continue;}
        }
      }
    """
    ast = parser.parse(code)
    print(ast == parser.parse(unparser.unparse(ast)), end='\n\n')


class negative_tests(object):
  def test_01():
    print("Fail check missing close brace")
    code = """
      def g01 (a) -> (x) {
        x := a + 1;
    """
    parser.parse(code)
  
  def test_02():
    print("Fail check missing ;")
    code = """
      def g02 (a) -> (x) {
        a := a + 1
        x := a;
      }
    """
    parser.parse(code)
  
  def test_03():
    print("Fail check reserved identifier")
    code = """
      def g03 (a) -> (x) {
        if := a + 1;
      }
    """
    parser.parse(code)
  
  def test_04():
    print("Fail check assigning bool")
    code = """
      def g04 (a b) -> (x) {
        x := a < b;
      }
    """
    parser.parse(code)
  
  def test_05():
    print("Fail check arithmetic loop condition")
    code = """
      def g05 (a b) -> (x) {
        while a + b {skip;}
      }
    """
    parser.parse(code)
  
  def test_06():
    print("Fail check break outside a loop")
    code = """
      def g06 (a b) -> (x) {
        break;
      }
    """
    parser.parse(code)
  
  def test_07():
    print("Fail check uninitialized variable")
    code = """
      def g07 (a b) -> (x) {
        x := y;
      }
    """
    parser.parse(code)
  
  def test_08():
    print("Fail check repeated input variable")
    code = """
      def g08 (a a) -> (x) {
        skip;
      }
    """
    parser.parse(code)
  
  def test_09():
    print("Fail check repeated output variable")
    code = """
      def g09 (a) -> (x x) {
        skip;
      }
    """
    parser.parse(code)
  
  def test_10():
    print("Fail check overloaded for loop index")
    code = """
      def g10 (i) -> () {
        for i in [0..1] {
          skip;
        }
      }
    """
    parser.parse(code)
  
  def test_11():
    print("Fail check uninitialized output")
    code = """
      def g11 (x) -> (y z) {
        skip;
      }
    """
    parser.parse(code)

# Run test suites
if __name__ == '__main__':
  # Run positive tests
  for test in dir(positive_tests):
    if not test.startswith('test_'): continue
    getattr(positive_tests, test)()
  
  # Run negative tests
  for test in dir(negative_tests):
    if not test.startswith('test_'): continue
    try: getattr(negative_tests, test)()
    except Exception as e: print(f'{type(e).__name__}: {e}\n')

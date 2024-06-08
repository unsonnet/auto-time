# The Extended While Language
This project contains a lexical tokenizer (*while_lexer.py*), parser (*while_parser.py*, *while_ast.py*), unparser (*while_unparser.py*), analyzer (*while_cfg.py*, *while_analysis.py*), and unit tests (*while_tests.py*) for the **extended WHILE language** (described below). The code was built and tested using **Python 3.11.5** with the **PLY 3.11** (Python Lex-Yacc) package for lexing / parsing, **SymPy** (Symbolic Python) package for doing symbolic algebra, and **PyGraphViz** (Python GraphViz Interface) package for visualizing the control flow graph (this requires GraphViz and a C/C++ compiler to be installed).

Earlier versions of Python with the corresponding PLY, SymPy, and PyGraphViz versions should also work.

### How To Run
Note, scripts in the extended while language have the .ewl extension. To parse and analyze one of these scripts, download the ewlc folder. Then in the command line, run the command

```python path/to/ewlc_folder path/to/ewl_script.ewl [options]```

You have three options:

* ``--ast`` (or ``-a``) to produce the abstract syntax tree
* ``--cfg`` (or ``-c``) to compile to bytecode and produce the control flow graph (requires GraphViz)
* ``--analyze`` (or ``-z``) to identify points in the control flow graph where a recursive equation needs to be set up and solved.

These three options are non-exclusive so they can be ran in parallel. If you would like to run the test suite, run the command

```python path/to/ewlc_folder/while_tests.py```

### The Grammar
The extended WHILE language is defined by the following grammar (starting at ``<prog>`` and taking ``E`` to be the empty string):

    <prog> ::= def <id> ( <vars> ) -> ( <vars> ) <body>
    <vars> ::= E | <id> <vars>

    <body> ::= { <exp> }
     <exp> ::= E | <stmt> | <ctrl> <exp> | <stmt> ; <exp>
    <stmt> ::= skip | <id> := <aexp> | break | continue
    <ctrl> ::= if <bexp> <body>
             | if <bexp> <body> else <body>
             | while <bexp> <body>
             | for <id> in [ <aexp> .. <aexp> ] <body>
    
    <aexp> ::= <term> | <aexp> + <term> | <aexp> - <term>
    <term> ::= <fact> | <term> * <fact> | <term> / <fact>
    <fact> ::= <id> | <num> | - <aexp> | ( <aexp> )

    <bexp> ::= true | false | <aexp> <rel> <aexp>
     <rel> ::= < | > | ==

where
1. ``<vars>`` is a non-repeating list of identifiers
2. ``break`` and ``continue`` only appear nested in a loop body
3. ``<num>`` is any nonnegative integer, and
4. ``<id>`` is any alphanumeric string starting with a letter and not matching any of the reserved identifiers (``def``, ``skip``, ``continue``, ``break``, ``if``, ``else``, ``while``, ``for``, ``in``, ``true``, ``false``).

Moreover, the extended WHILE language is lexically scoped. That is, variables only exist in the body that they are defined. One exception: the index associated with a ``for`` loop exists in the loop's body, not the parent body.

### Example Program
As an example of a program in the extended WHILE language, consider the following function (same demo in the *while_lexer.py*, *while_parser.py*, and *while_unparser.py* files):

    def func (a b c) -> (x y) {
      x := a + 1;
      y := b + 3;
      skip;
      if x == y {a := 4}
      else {b := 5;}
      while True {
        x := y;
        m := 3;
        for i in [x .. b+4] {
          x := x + i;
        }
        break;
      }
    }

### Syntactic Error Handling
For input that disobeys the grammar above, couple error messages may appear:

* If there is an unexpected token, parser will throw "`Token _ at line _ was unexpected`".
* If input ends abruptly, parser will throw "`Input ended unexpectedly`".

# Parser and Unparser
The main logic for the parser is stored in *while_parser.py* which goes through the code and constructs an abstract syntax tree whose components are defined in *while_ast.py*. The main logic for the unparser is stored in *while_ast.py* with the interface defined in *while_unparser.py*. The main reason for this is flexibility.

In particular, we implement the AST as user-defined class instances that behave like tuples when treated as an AST and from which can be compiled down to bytecode (assignments, jumps, and conditional jumps) to construct the control flow graph. This allows us to do computations within the AST for purposes of unparsing and then conversion to CFG for purposes of static analysis.

### AST Format
The abstract syntax tree (generated in *while_parser.py*) is formatted as a nested, labeled tuple structure where each tuple starts. Expressions are formatted as a BODY tuple containing a list of tuples representing each statement in the same order as the program. For example, the AST of the example program above is (indentation mine):

    DEF(
      func, [a, b, c], [x, y],
      BODY([
        ASSIGN(x, AEXP(a, +, 1)),
        ASSIGN(y, AEXP(b, +, 3)),
        SKIP(),
        IF(
          BEXP(x, ==, y),
          BODY([ASSIGN(a, 4)]),
          BODY([ASSIGN(b, 5)])
        ),
        WHILE(
          True,
          BODY([
            ASSIGN(x, y),
            ASSIGN(m, 3),
            FOR(
              i, x, AEXP(b, +, 4),
              BODY([
                ASSIGN(x, AEXP(x, +, i))
              ])
            ),
            BREAK()
          ])
        )
      ])
    )

### Unparser Logic
The unparser (available in *while_unparser.py* but implemented in *while_ast.py*) works by recursively going down the AST and formatting each tuple with the corresponding text. It adds semicolons and braces where needed. For simplicity, it explicitly includes all parentheses where possible to preserve order of operations. It also explicitly includes the ``else`` branch where appropriate. For example, unparsing the AST of the example program above produces (indentation mine):

    def func (a b c) -> (x y) {
      x := (a + 1);
      y := (b + 3);
      skip;
      if x == y {a := 4;}
      else {b := 5;}
      while true {
        x := y;
        m := 3;
        for i in [x..(b + 4)] {
          x := (x + i);
        }
        break;
      }
    }

which matches the original program almost exactly mod extra syntax that does not change the semantics of the program (like parentheses and semicolons).

# Static Analysis
The main static analysis question for the extended WHILE language is as follows:

> At each point in the program, what is the worst-case running time complexity up to that point?

To tackle this question, we can reduce it to the question:

> At each point in the program, what is the asymptotic value of each variable in terms of the input?

The reason the first question reduces down to the second is that we can create a dummy variable that keeps track of how many computations are being done in the program. By getting the asymptotic value of this counter, we get the running time complexity of the program.

## First Steps

However, in order for the analysis to work, we need to guarantee that the program is well-defined semantically. That is,

1. All variables are defined when used. This is a must analysis with the property space being the power set of variables. 
2. All `break`'s and `continue`'s are located within a loop body. And,
3. the corresponding control flow graph is a connected graph.

These can be thought of as their own static analysis questions which we tackle head on within the *while_parser.py*, *while_ast.py*, and *while_cfg.py* files respectively.

### Implementation

For determining what variables are defined at each point in the program, we use a symbol table during the parsing stage (encoded by the stack `self.context`) to keep track of what variables are defined and in which lexical scope. Whenever a new scope is entered (i.e. a pair of curly braces), we construct a new scope and push it into the stack. When we reach a use of a variable, we check the stack to see if it exists. Otherwise we throw an error.

For determining whether a `break` or `continue` is defined in a loop, we use a loop depth counter `self.loop_depth` (within *while_parser.py*) keeping track of how deep into a loop body we are in. We first initialize it to zero to mean that we are not in any loop_body and hence the above statements would be semantically inappropriate. When we enter a loop body, we increment the counter. When we reach a `break` or `continue`, we check if the loop counter is positive. If not, we throw an error.

Finally for determining whether the corresponding control flow graph is a connected graph, we trace the control flow graph using breadth-first search (within *while_cfg.py*).

### Semantic Error Handling

All of the above analysis can be thought of as semantic error handling. In particular,

For input that contains trivial semantic inconsistencies, a couple of possible error messages may appear:

* If a non-input variable is used before initialization, parser throws an error "`Variable _ at line _ is undefined`".
* If an output variable is not initalized in the function body (i.e. largest body), parser throws an error "`Output variables _ are undefined`". This is a conservative estimate so initializing an output variable in both branches of an `if` statement does not count.
* If a variable name repeats in the input or output variable, parser throws an error "`Input/Output variable _ at line _ is repeated`".
* If a `break` or `continue` statement is used outside of a loop body, parser throws an error "`Break/Continue at line _ is outside of a loop`".
* If index variable in `for` loop already defined, parser will throw `Index _ at line _ already exists`.

## Second Steps

To compute the asymptotic value of variables in terms of the input, we will pass variable assignments through the control flow graph (CFG), updating assignments where appropriate. For a CFG that is just a chain, we can just apply all the assignments in order. For a CFG that is a simple loop (that is, only one entry / exit point and no branching inside the loop), we can compute a single iteration then solve the recurrence equation up until the break condition. A control flow graph that is a composition of these two structures can be computed by recursively solving the subproblem.

However, branching and early loop termination (via breaks) are far more complicated and can introduce wildly different dynamics. Since our analysis question is finding an upper bound on the values of each variable, we can compute each branch separately and then pick the larger bound for each variable. Similarly for loops with breaks, we compute each possible exit condition separately and then pick the larger bound for each variable. Since our bounds can be modelled as complexity classes (which are sets of functions), we can think of our analysis as a may analysis with the join being union.

The above description means that we essentially grab a general control flow graph and then split it into multiple control flow graphs, each with a particular branch chosen or breakpoint chosen. To formalize this, we can extend our property space to be the powerset of mappings. Then the blocks in the control flow graph are as follows:

1. Assignments. These take in a set of mappings from each in-edge and unions them. Then they update each mapping with the corresponding assignment and pass it onto the out-edge.
2. If-Else Branch. These take in a set of mappings from each in-edge and unions them. Then they pass the full set to each out-edge.
3. Loop-Exit Branch. These take in a set of mappings from each in-edge and unions them. Then they update each mapping with the solution to the recurrence relation associated to the loop. Finally they pass it onto the out-edge that exits the loop.

The difficulty is in identifying the possible loop-exit branches. These are points in the program where the control flow both enters a loop then exits. The start of a while-loop and for-loop fall under this definition. But also if-Else branches (that are inside a loop) where only one of the branches directly leads to a break.

Due to time-constraints and difficulty in implementation, this project was able to solve the analysis question of finding loop-Exit branches (located in *while_analysis.py*) but not the value of variables analysis. We solve the identification problem by:

1. isolating while- (or for-) loops
2. backpropagating the node where the loop exits to into the loop body
3. if it reaches only one branch of a conditional, we stop the backpropagation
4. if it reaches both branches of a conditional, we continue the backpropagation
5. Once all backpropagation stops, the conditionals that have exactly one instance of the break will be relabeled as loop-exit branches.

# Unit Tests
There are two test suites (available in *while_tests.py*). The ``positive_tests`` class checks that valid programs are parsed/unparsed correctly. And the ``negative_tests`` class checks that invalid programs are correctly flagged as having a parsing error.

* For the positive tests, we check that the implementation satisfies the property ``parser(unparser(ast)) = ast``.
* For the negative tests, we check that the implementation throws an appropriate error.

After running the parser (either through ``while_parser.py``, ``while_unparser.py``, or ``while_tests.py``), full details of the parser's internal state and stack trace is dumped to a ``parser.out`` file. The syntax is described in the PLY documentation [https://ply.readthedocs.io/en/latest/].
from translator import LispParser


def print_translator():
    parser = LispParser()
    expression = ("(+ 2 3)"
                  "(loop ((= 4 3) if (> 7 8) (+ 4 5) (6)))")
    expression1 = ("((setq sum 53) (+ 2 3) (+ 4 5))")
    expression2 = ("(read_char a)")
    expression3 = ("(defun sum()("
                   "(+ 2 3))"
                   "sum())")
    expression4 = ("""((setq hello "hello,")
setq myName read_line
(print_line hello)
print_line myName)""")
    expression5 = ("""
(read_char a
    (loop (> a 0) (print_char a) (read_char a)))""")
    prob2 = """(setq one 1
    setq two 2
    setq sum 2 
    setq old 0
    (loop (< 1000000 two)
    (old two
    two (+ one two)
    one old
    if (= 0 (/ two 2) (sum + two)))))
    """
    parser.translate(expression5)
    for code in parser.code:
        print(code)


if __name__ == '__main__':
    print_translator()

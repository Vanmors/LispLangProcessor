import sys

import isa
from isa import Opcode
from registres import Registres


class LispParser:
    def __init__(self):
        self.code = [] * 1000
        self.label_index = 0
        self.pc = 0
        self.stack = []
        self.registres_var = {}
        self.registres_val = Registres()

    def translate(self, expression):
        self.registres_val.allocate_register("R1")
        self.registres_val.allocate_register("R2")
        self.registres_val.allocate_register("R3")
        self.registres_val.allocate_register("R4")
        self.registres_val.allocate_register("R5")
        self.registres_val.allocate_register("R6")
        self.registres_val.allocate_register("R7")
        self.registres_val.allocate_register("R8")
        self.registres_val.allocate_register("R9")
        self.registres_val.allocate_register("R10")

        tokens = expression.replace('(', ' ( ').replace(')', ' ) ').split()

        self.parse_tokens(tokens)

        self.code.append({"index": len(self.code) + 1, "opcode": Opcode.HLT})

    def parse_tokens(self, tokens):
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token == '(':
                # Начало нового блока
                new_i = self.parse_block(tokens, i)
                i = new_i - 1
            # elif token.isdigit() or (token[0] == '-' and token[1:].isdigit()):
            #     # Число
            #     self.code.append(
            #         {"index": len(self.code) + 1, "opcode": Opcode.LD, "register": f"R{len(self.code) + 1}",
            #          "arg": int(token)})
            elif token == "setq":
                new_i = self.create_variable(tokens, i)
                i = new_i
            elif token == "if":
                # Условный оператор
                new_i = self.parse_if(tokens, i)
                i = new_i - 1
            elif token == "loop":
                # Цикл
                new_i = self.parse_loop(tokens, i)
                i = new_i - 1
            elif token == "print_char":
                # Вывод
                new_i = self.parse_print_char(tokens, i)
                i = new_i
            elif token == "read_char":
                # Ввод
                new_i = self.parse_read_char(tokens, i)
                i = new_i
            elif token in ('+', '-', '*', '/', '>', '<', '='):
                # Арифметическая операция
                new_i = self.parse_arithmetic(tokens, i)
                i = new_i - 1
            elif token == "defun":
                # Инициализация функции
                new_i = self.parse_function_create(tokens, i)
                i = new_i - 1
            elif token == "read_line":
                new_i = self.parse_read_line(tokens, i)
                i = new_i - 1
            elif token == "print_line":
                new_i = self.parse_print_line(tokens, i)
                i = new_i
            elif token.isalpha():
                # Переменная или вызов функции
                if i + 1 < len(tokens) and tokens[i + 1] == '(' and (
                        tokens[i + 2].isalpha() or tokens[i + 2].isalpha() == ')'):
                    # Функция
                    new_i = self.parse_function_call(tokens, i)
                    i = new_i - 1
                else:
                    # Переменная
                    if tokens[i + 1] == '(':
                        new_i = self.parse_block(tokens, i + 1)
                        self.code.append(
                            {"index": len(self.code) + 1, "opcode": Opcode.LD,
                             "register": self.registres_var[tokens[i]],
                             "arg": "R10"})
                        i = new_i - 1
                    elif tokens[i + 1].isalpha():
                        self.code.append(
                            {"index": len(self.code) + 1, "opcode": Opcode.LD,
                             "register": self.registres_var[tokens[i]],
                             "arg": self.registres_var[tokens[i + 1]]})
                        i = i + 1
                    elif tokens[i + 1].isdigit():
                        self.code.append(
                            {"index": len(self.code) + 1, "opcode": Opcode.LD,
                             "register": self.registres_var[tokens[i]],
                             "arg": tokens[i + 1]})
                        i = i + 1
            i += 1

    def parse_arithmetic(self, tokens, index):
        # Арифметическое выражение
        arg1 = 0
        arg2 = 0
        operator = tokens[index]
        if tokens[index + 1].isalpha():
            arg1 = self.registres_var[tokens[index + 1]]
        if tokens[index + 2].isalpha():
            arg2 = self.registres_var[tokens[index + 2]]
        if tokens[index + 1].isdigit():
            number = self.registres_val.get_free_register()
            self.registres_val.put_in_register(number, tokens[index + 2])
            self.code.append(
                {"index": len(self.code) + 1, "opcode": Opcode.LD, "register": number,
                 "arg": int(tokens[index + 1])})
            arg1 = number
        if tokens[index + 2].isdigit():
            number = self.registres_val.get_free_register()
            self.registres_val.put_in_register(number, tokens[index + 2])
            self.code.append(
                {"index": len(self.code) + 1, "opcode": Opcode.LD, "register": number,
                 "arg": int(tokens[index + 2])})
            arg2 = number
        if (not tokens[index + 1].isalpha() and not tokens[index + 2].isalpha()):
            args_start_index = index + 1
            args_end_index = self.find_closing_bracket(tokens, args_start_index)
            args_tokens = tokens[args_start_index:args_end_index]
            self.parse_tokens(args_tokens)
            if (arg1 == 0):
                arg1 = "R10"
            else:
                arg2 = "R10"
        else:
            args_end_index = self.find_closing_bracket(tokens, index + 1)

        number = self.registres_val.get_free_register()
        self.registres_val.put_in_register(number, 0)

        if operator == '+':
            self.code.append({"index": len(self.code) + 1, "opcode": Opcode.ADD, "register": number,
                              "arg": [arg1, arg2]})
            self.code.append({"index": len(self.code) + 1, "opcode": Opcode.LD, "register": "R10",
                              "arg": number})
        elif operator == '-':
            self.code.append({"index": len(self.code) + 1, "opcode": Opcode.SUB, "register": number,
                              "arg": [arg1, arg2]})
            self.code.append({"index": len(self.code) + 1, "opcode": Opcode.LD, "register": "R10",
                              "arg": number})
        elif operator == '*':
            self.code.append({"index": len(self.code) + 1, "opcode": Opcode.MUL, "register": number,
                              "arg": [arg1, arg2]})
            self.code.append({"index": len(self.code) + 1, "opcode": Opcode.LD, "register": "R10",
                              "arg": number})
        elif operator == '/':
            self.code.append({"index": len(self.code) + 1, "opcode": Opcode.DIV, "register": number,
                              "arg": [arg1, arg2]})
            self.code.append({"index": len(self.code) + 1, "opcode": Opcode.LD, "register": "R10",
                              "arg": number})
        elif operator == '>':
            self.code.append({"index": len(self.code) + 1, "opcode": Opcode.CMP, "register": arg1,
                              "arg": arg2})
            self.code.append(
                {"index": len(self.code) + 1, "opcode": Opcode.JG, "arg": 0})
            self.stack.append(len(self.code))
        elif operator == '<':
            self.code.append({"index": len(self.code) + 1, "opcode": Opcode.CMP, "register": arg1,
                              "arg": arg2})
            self.code.append(
                {"index": len(self.code) + 1, "opcode": Opcode.JL, "arg": 0})
            self.stack.append(len(self.code))
        elif operator == '=':
            self.code.append({"index": len(self.code) + 1, "opcode": Opcode.CMP, "register": arg1,
                              "arg": arg2})
            self.code.append(
                {"index": len(self.code) + 1, "opcode": Opcode.JE, "arg": 0})
            self.stack.append(len(self.code))
        else:
            raise NotImplementedError(f"Unsupported arithmetic operator: {operator}")
        self.registres_val.clean_register(number)
        return args_end_index

    def create_variable(self, tokens, start_index):
        start_value = start_index + 2
        end_block = start_index + 1
        if (tokens[start_value][0] == '"'):
            substring = tokens[start_value][1:-1]
            number = self.registres_val.get_free_register()
            self.registres_var[tokens[start_index + 1]] = number
            for char in substring:
                self.code.append(
                    {"index": len(self.code) + 1, "opcode": Opcode.LD, "register": number,
                     "arg": ord(char)})
                self.code.append(
                    {"index": len(self.code) + 1, "opcode": Opcode.ST, "register": number,
                     "name": tokens[start_index + 1]})
            self.code.append(
                {"index": len(self.code) + 1, "opcode": Opcode.LD, "register": number,
                 "arg": 48})
            self.code.append(
                {"index": len(self.code) + 1, "opcode": Opcode.ST, "register": number,
                 "name": tokens[start_index + 1]})
            self.registres_val.clean_register(number)
            end_block = start_index + 2
        elif tokens[start_index + 2] == '(':
            condition_index = start_index + 1
            end_block = self.find_closing_bracket(tokens, condition_index)
            self.parse_tokens(tokens[condition_index:end_block])
        elif tokens[start_index + 2] not in {"read_line", "read_char"}:
            number = self.registres_val.get_free_register()
            self.registres_val.put_in_register(number, tokens[start_index + 2])
            self.registres_var[tokens[start_index + 1]] = number
            self.code.append(
                {"index": len(self.code) + 1, "opcode": Opcode.LD, "register": number,
                 "arg": int(tokens[start_index + 2])})
            end_block = start_index + 2

        return end_block

    def parse_block(self, tokens, start_index):
        # Находим соответствующую закрывающую скобку
        end_index = self.find_closing_bracket(tokens, start_index)

        # Рекурсивно обрабатываем внутренний блок
        inner_tokens = tokens[start_index + 1:end_index]
        # inner_tokens = tokens[start_index:end_index]
        self.parse_tokens(inner_tokens)
        return end_index

    def find_closing_bracket(self, tokens, start_index):
        depth = 1
        i = start_index
        for i in range(start_index, len(tokens)):
            if tokens[i] == '(':
                depth += 1
            elif tokens[i] == ')':
                depth -= 1
                if depth == 0:
                    return i
        if depth == 1:
            return i + 1
        raise ValueError("Unbalanced brackets.")

    def parse_function_create(self, tokens, start_index):
        # Имя функции
        function_name = tokens[start_index + 1]

        # Аргументы функции
        args_start_index = start_index + 3
        args_end_index = args_start_index
        while (tokens[args_end_index] != ')'):
            args_end_index += 1

        args_tokens = tokens[args_start_index:args_end_index]

        self.code.append(
            {"index": len(self.code) + 1, "opcode": Opcode.LD, "register": f"R{len(self.code) + 1}",
             "name": args_tokens[0]})

        end_block = self.parse_block(tokens, args_end_index + 1)

        end_label = f"end_block{self.label_index}"
        self.label_index += 1
        self.code.append({"index": len(self.code) + 1, "opcode": "LABEL", "label": end_label})
        return end_block

    def parse_function_call(self, token, start_index):
        self.code.append({"index": len(self.code) + 1, "opcode": Opcode.CALL, "label": token[start_index]})
        return start_index + 2

    def parse_if(self, tokens, if_index):
        # Условие
        condition_index = if_index + 2
        end_block = self.find_closing_bracket(tokens, condition_index)
        self.parse_tokens(tokens[condition_index:end_block])

        # Тело if-блока
        true_block_index = end_block + 1
        end_block = self.parse_block(tokens, true_block_index)

        # Метка конца блока
        self.code[self.stack.pop() - 1]["arg"] = len(self.code) + 1
        return end_block

    def parse_loop(self, tokens, loop_index):
        start_index = len(self.code) + 1
        # Условие
        condition_index = loop_index + 2
        end_block = self.find_closing_bracket(tokens, condition_index)
        self.parse_tokens(tokens[condition_index:end_block])

        # Тело цикла
        loop_body_index = condition_index + 4
        end_block = self.parse_block(tokens, loop_body_index)

        # Метка возврата к условию цикла
        loop_start_label = f"start_block{self.label_index}"
        # self.label_index += 1
        # self.code.append({"index": len(self.code) + 1, "opcode": Opcode.JMP, "label": loop_start_label})

        # Метка конца блока
        end_label = f"end_block{self.label_index}"
        self.label_index += 1
        self.code.append({"index": len(self.code) + 1, "opcode": Opcode.JMP, "arg": start_index})
        # print(self.stack.pop() - 1)
        self.code[self.stack.pop() - 1]["arg"] = len(self.code) + 1
        return end_block

    def parse_print_char(self, tokens, print_index):
        number_register = self.registres_var[tokens[print_index + 1]]
        self.code.append({"index": len(self.code) + 1, "opcode": Opcode.OUT, "register": number_register})
        self.registres_val.clean_register(number_register)
        return print_index + 2

    def parse_read_char(self, tokens, read_index):
        number = self.registres_val.get_free_register()
        self.registres_var[tokens[read_index + 1]] = number
        self.code.append({"index": len(self.code) + 1, "opcode": Opcode.IN, "register": number,
                          "name": tokens[read_index + 1]})
        self.registres_val.put_in_register(number, 0)
        return read_index + 2

    def parse_read_line(self, tokens, read_index):
        number = self.registres_val.get_free_register()
        start_index = len(self.code) + 1
        self.registres_var[tokens[read_index - 1]] = number
        self.code.append({"index": len(self.code) + 1, "opcode": Opcode.IN, "register": number})
        self.registres_val.put_in_register(number, 0)
        number2 = self.registres_val.get_free_register()
        self.registres_var[tokens[read_index - 1]] = number
        self.code.append({"index": len(self.code) + 1, "opcode": Opcode.LD, "register": number2,
                          "arg": 0})
        self.registres_val.put_in_register(number2, 0)
        self.code.append(
            {"index": len(self.code) + 1, "opcode": Opcode.CMP, "register": number, "arg": number2})
        self.code.append({"index": len(self.code) + 1, "opcode": Opcode.JG, "arg": 0})
        self.stack.append(len(self.code))
        self.code.append({"index": len(self.code) + 1, "opcode": Opcode.ST, "register": number,
                          "name": tokens[read_index - 1]})
        self.registres_val.clean_register(number)
        self.code.append({"index": len(self.code) + 1, "opcode": Opcode.JMP, "arg": start_index})

        self.code[self.stack.pop() - 1]["arg"] = len(self.code) + 1

        self.code.append({"index": len(self.code) + 1, "opcode": Opcode.ST, "register": number,
                          "name": tokens[read_index - 1]})
        self.registres_val.clean_register(number)
        self.registres_val.clean_register(number2)
        return read_index + 1

    def parse_print_line(self, tokens, print_index):
        self.code.append({"index": len(self.code) + 1, "opcode": Opcode.LD, "register": f"R0",
                          "arg": 0})
        start_index = len(self.code) + 1
        number = self.registres_val.get_free_register()
        self.registres_var[tokens[print_index + 1]] = number
        self.code.append(
            {"index": len(self.code) + 1, "opcode": Opcode.LD, "register": number,
             "name": tokens[print_index + 1]})
        self.registres_val.put_in_register(number, 0)
        number2 = self.registres_val.get_free_register()
        self.registres_var[tokens[print_index + 1]] = number
        self.code.append({"index": len(self.code) + 1, "opcode": Opcode.LD, "register": number2,
                          "arg": 0})
        self.registres_val.put_in_register(number2, 0)
        self.code.append(
            {"index": len(self.code) + 1, "opcode": Opcode.CMP, "register": number, "arg": number2})
        self.code.append({"index": len(self.code) + 1, "opcode": Opcode.JG, "arg": 0})
        self.stack.append(len(self.code))
        self.code.append({"index": len(self.code) + 1, "opcode": Opcode.OUT, "register": number})
        self.code.append({"index": len(self.code) + 1, "opcode": Opcode.INC, "register": "R0"})
        self.code.append({"index": len(self.code) + 1, "opcode": Opcode.JMP, "arg": start_index})
        self.code[self.stack.pop() - 1]["arg"] = len(self.code) + 1
        self.registres_val.clean_register(number)
        self.registres_val.clean_register(number2)
        return print_index + 1


def main(source, target):
    with open(source, encoding="utf-8") as f:
        source = f.read()

    parser = LispParser()
    parser.translate(source)

    # for code in parser.code:
    #     print(code)

    isa.write_code(target, parser.code)
    print("source LoC:", len(source.split("\n")), "code instr:", len(parser.code))


if __name__ == "__main__":
    # source = "lisp.txt"
    # target = "target.txt"
    assert len(sys.argv) == 3, "Wrong arguments: translator.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)

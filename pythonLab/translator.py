import sys

import isa
from isa import Opcode
from registres import Registres


class LispParser:
    def __init__(self):
        self.code = []
        self.label_index = 0
        self.pc = 0
        self.stack = []
        self.registres_var = {}
        self.registres_val = Registres()
        self.procedure_labels = {}

    def translate(self, expression):
        for i in range(1, 11):
            self.registres_val.allocate_register(f"R{i}")

        tokens = expression.replace("(", " ( ").replace(")", " ) ").split()
        self.parse_tokens(tokens)

        self.code.append({"index": len(self.code) + 1, "opcode": Opcode.HLT})

    def parse_tokens(self, tokens: list):
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token == "(":
                # Начало нового блока
                new_i = self.parse_block(tokens, i)
                i = new_i - 1
            elif token == "setq":
                new_i = self.create_variable(tokens, i)
                i = new_i
            elif token == "if":
                # Условный оператор
                new_i = self.parse_if(tokens, i)
                i = new_i - 1
            elif token == "while":
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
            elif token in ("+", "-", "*", "/", ">", "<", "=", "mod"):
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
            elif token == "print_int":
                new_i = self.parse_print_int(tokens, i)
                i = new_i
            elif token.isdigit():
                self.code.append(
                    {"index": len(self.code) + 1, "opcode": Opcode.LD, "register": "R10",
                     "arg": int(token)}
                )
            elif token.isalpha():
                # Переменная или вызов функции
                if (
                        i + 1 < len(tokens)
                        and tokens[i + 1] == "("
                        and (tokens[i + 2].isalpha() or tokens[i + 2].isalpha() == ")")
                ):
                    # Функция
                    new_i = self.parse_function_call(tokens, i)
                    i = new_i - 1
                else:
                    # Переменная
                    new_i = self.update_variable(tokens, i)
                    i = new_i
            i += 1

    def parse_arithmetic(self, tokens: list, index: int) -> int:
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
                {"index": len(self.code) + 1, "opcode": Opcode.LD, "register": number, "arg": int(tokens[index + 1])}
            )
            arg1 = number
        if tokens[index + 2].isdigit():
            number = self.registres_val.get_free_register()
            self.registres_val.put_in_register(number, tokens[index + 2])
            self.code.append(
                {"index": len(self.code) + 1, "opcode": Opcode.LD, "register": number, "arg": int(tokens[index + 2])}
            )
            arg2 = number
        if not tokens[index + 1].isalpha() and not tokens[index + 2].isalpha():
            args_start_index = index + 1
            args_end_index = self.find_closing_bracket(tokens, args_start_index)
            args_tokens = tokens[args_start_index:args_end_index]
            self.parse_tokens(args_tokens)
            if arg1 == 0:
                arg1 = "R10"
            else:
                arg2 = "R10"
        else:
            args_end_index = self.find_closing_bracket(tokens, index + 1)

        number = self.registres_val.get_free_register()
        self.registres_val.put_in_register(number, 0)

        if operator == "+":
            self.arithmetic_operation(Opcode.ADD, number, arg1, arg2)
        elif operator == "-":
            self.arithmetic_operation(Opcode.SUB, number, arg1, arg2)
        elif operator == "*":
            self.arithmetic_operation(Opcode.MUL, number, arg1, arg2)
        elif operator == "/":
            self.arithmetic_operation(Opcode.DIV, number, arg1, arg2)
        elif operator == "mod":
            self.arithmetic_operation(Opcode.MOD, number, arg1, arg2)
        elif operator == ">":
            self.compare_operation(Opcode.JG, arg1, arg2)
        elif operator == "<":
            self.compare_operation(Opcode.JL, arg1, arg2)
        elif operator == "=":
            self.compare_operation(Opcode.JE, arg1, arg2)
        else:
            raise NotImplementedError(f"Unsupported arithmetic operator: {operator}")
        self.registres_val.clean_register(number)
        return args_end_index

    def arithmetic_operation(self, opcode: Opcode, number_register: str, arg1, arg2):
        self.code.append(
            {"index": len(self.code) + 1, "opcode": opcode, "register": number_register, "arg": [arg1, arg2]}
        )
        self.code.append({"index": len(self.code) + 1, "opcode": Opcode.LD, "register": "R10", "arg": number_register})

    def compare_operation(self, opcode: Opcode, arg1, arg2):
        self.code.append({"index": len(self.code) + 1, "opcode": Opcode.CMP, "register": arg1, "arg": arg2})
        self.code.append({"index": len(self.code) + 1, "opcode": opcode, "arg": 0})
        self.stack.append(len(self.code))

    def create_variable(self, tokens: list, start_index: int) -> int:
        start_value = start_index + 2
        end_block = start_index + 1
        if tokens[start_value][0] == '"':
            substring = tokens[start_value][1:-1]
            number = self.registres_val.get_free_register()
            self.registres_var[tokens[start_index + 1]] = number
            for char in substring:
                self.code.append(
                    {"index": len(self.code) + 1, "opcode": Opcode.LD, "register": number, "arg": ord(char)}
                )
                self.code.append(
                    {
                        "index": len(self.code) + 1,
                        "opcode": Opcode.ST,
                        "register": number,
                        "name": tokens[start_index + 1],
                    }
                )
            self.code.append({"index": len(self.code) + 1, "opcode": Opcode.LD, "register": number, "arg": 0})
            self.code.append(
                {"index": len(self.code) + 1, "opcode": Opcode.ST, "register": number, "name": tokens[start_index + 1]}
            )
            self.registres_val.clean_register(number)
            end_block = start_index + 2
        elif tokens[start_index + 2] == "(":
            condition_index = start_index + 1
            end_block = self.find_closing_bracket(tokens, condition_index)
            self.parse_tokens(tokens[condition_index:end_block])
        elif tokens[start_index + 2] not in {"read_line", "read_char"}:
            number = self.registres_val.get_free_register()
            self.registres_val.put_in_register(number, tokens[start_index + 2])
            self.registres_var[tokens[start_index + 1]] = number
            self.code.append(
                {
                    "index": len(self.code) + 1,
                    "opcode": Opcode.LD,
                    "register": number,
                    "arg": int(tokens[start_index + 2]),
                }
            )
            end_block = start_index + 2

        return end_block

    def update_variable(self, tokens: list, start_index: int) -> int:
        end_block = start_index + 1
        if tokens[start_index + 1] == "(":
            new_i = self.parse_block(tokens, start_index + 1)
            self.code.append(
                {
                    "index": len(self.code) + 1,
                    "opcode": Opcode.LD,
                    "register": self.registres_var[tokens[start_index]],
                    "arg": "R10",
                }
            )
            end_block = new_i - 1
        elif tokens[start_index + 1].isalpha():
            self.code.append(
                {
                    "index": len(self.code) + 1,
                    "opcode": Opcode.LD,
                    "register": self.registres_var[tokens[start_index]],
                    "arg": self.registres_var[tokens[start_index + 1]],
                }
            )
        elif tokens[start_index + 1].isdigit():
            self.code.append(
                {
                    "index": len(self.code) + 1,
                    "opcode": Opcode.LD,
                    "register": self.registres_var[tokens[start_index]],
                    "arg": tokens[start_index + 1],
                }
            )
        return end_block

    def parse_block(self, tokens: list, start_index: int) -> int:
        # Находим соответствующую закрывающую скобку
        end_index = self.find_closing_bracket(tokens, start_index)

        # Рекурсивно обрабатываем внутренний блок
        inner_tokens = tokens[start_index + 1: end_index]
        self.parse_tokens(inner_tokens)
        return end_index

    def find_closing_bracket(self, tokens: list, start_index: int) -> int:
        depth = 1
        i = start_index
        for i in range(start_index, len(tokens)):
            if tokens[i] == "(":
                depth += 1
            elif tokens[i] == ")":
                depth -= 1
                if depth == 0:
                    return i
        if depth == 1:
            return i + 1
        raise ValueError("Unbalanced brackets.")

    def parse_function_create(self, tokens: list, start_index: int) -> int:
        # Имя функции
        procedure_name = tokens[start_index + 1]

        # Сохранение индекса начала в словарь процедур
        self.procedure_labels[procedure_name] = len(self.code) + 1
        # Аргументы функции
        start_body_procedure = start_index + 3

        end_block = self.parse_block(tokens, start_body_procedure + 1)

        end_label = f"end_block{self.label_index}"
        self.label_index += 1
        self.code.append({"index": len(self.code) + 1, "opcode": "LABEL", "label": end_label})
        return end_block

    def parse_function_call(self, token: list, start_index: int):
        self.code.append({"index": len(self.code) + 1, "opcode": Opcode.CALL, "label": token[start_index]})
        return start_index + 2

    def parse_if(self, tokens: list, if_index: int) -> int:
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

    def parse_loop(self, tokens: list, loop_index: int) -> int:
        start_index = len(self.code) + 1
        # Условие
        condition_index = loop_index + 2
        end_block = self.find_closing_bracket(tokens, condition_index)
        self.parse_tokens(tokens[condition_index:end_block])

        # Тело цикла
        loop_body_index = condition_index + 4
        end_block = self.parse_block(tokens, loop_body_index)

        # Метка конца блока
        self.label_index += 1
        self.code.append({"index": len(self.code) + 1, "opcode": Opcode.JMP, "arg": start_index})
        self.code[self.stack.pop() - 1]["arg"] = len(self.code) + 1
        return end_block

    def parse_print_char(self, tokens: list, print_index: int):
        number_register = self.registres_var[tokens[print_index + 1]]
        self.code.append({"index": len(self.code) + 1, "opcode": Opcode.OUT, "register": number_register})
        self.registres_val.clean_register(number_register)
        return print_index + 2

    def parse_read_char(self, tokens: list, read_index: int):
        number = self.registres_val.get_free_register()
        self.registres_var[tokens[read_index + 1]] = number
        self.code.append(
            {"index": len(self.code) + 1, "opcode": Opcode.IN, "register": number, "name": tokens[read_index + 1]}
        )
        self.registres_val.put_in_register(number, 0)
        return read_index + 2

    def parse_print_int(self, tokens: list, print_index: int):
        number_register = 0
        if tokens[print_index + 1] == "(":
            self.parse_block(tokens, print_index + 1)
            number_register = "R10"
        elif tokens[print_index + 1].isalpha():
            number_register = self.registres_var[tokens[print_index + 1]]
        elif tokens[print_index + 1].isdigit():
            number_register = self.registres_val.get_free_register()
            self.code.append(
                {"index": len(self.code) + 1, "opcode": Opcode.LD, "register": number_register,
                 "arg": tokens[print_index + 1]})
        self.code.append(
            {"index": len(self.code) + 1, "opcode": Opcode.OUT, "register": number_register, "type": "value"})
        self.registres_val.clean_register(number_register)
        return print_index + 2

    def parse_read_line(self, tokens: list, read_index: int) -> int:
        number = self.registres_val.get_free_register()
        start_index = len(self.code) + 1
        self.registres_var[tokens[read_index - 1]] = number
        self.code.append({"index": len(self.code) + 1, "opcode": Opcode.IN, "register": number})
        self.registres_val.put_in_register(number, 0)
        number2 = self.registres_val.get_free_register()
        self.registres_var[tokens[read_index - 1]] = number
        self.code.append({"index": len(self.code) + 1, "opcode": Opcode.LD, "register": number2, "arg": 0})
        self.registres_val.put_in_register(number2, 0)
        self.code.append({"index": len(self.code) + 1, "opcode": Opcode.CMP, "register": number, "arg": number2})
        self.code.append({"index": len(self.code) + 1, "opcode": Opcode.JG, "arg": 0})
        self.stack.append(len(self.code))
        self.code.append(
            {"index": len(self.code) + 1, "opcode": Opcode.ST, "register": number, "name": tokens[read_index - 1]}
        )
        self.registres_val.clean_register(number)
        self.code.append({"index": len(self.code) + 1, "opcode": Opcode.JMP, "arg": start_index})

        self.code[self.stack.pop() - 1]["arg"] = len(self.code) + 1

        self.code.append(
            {"index": len(self.code) + 1, "opcode": Opcode.ST, "register": number, "name": tokens[read_index - 1]}
        )
        self.registres_val.clean_register(number)
        self.registres_val.clean_register(number2)
        return read_index + 1

    def parse_print_line(self, tokens: list, print_index: int) -> int:
        self.code.append({"index": len(self.code) + 1, "opcode": Opcode.LD, "register": f"R0", "arg": 0})
        start_index = len(self.code) + 1
        number = self.registres_val.get_free_register()
        self.registres_var[tokens[print_index + 1]] = number
        self.code.append(
            {"index": len(self.code) + 1, "opcode": Opcode.LD, "register": number, "name": tokens[print_index + 1]}
        )
        self.registres_val.put_in_register(number, 0)
        number2 = self.registres_val.get_free_register()
        self.registres_var[tokens[print_index + 1]] = number
        self.code.append({"index": len(self.code) + 1, "opcode": Opcode.LD, "register": number2, "arg": 0})
        self.registres_val.put_in_register(number2, 0)
        self.code.append({"index": len(self.code) + 1, "opcode": Opcode.CMP, "register": number, "arg": number2})
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

    isa.write_code(target, parser.code)
    print("source LoC:", len(source.split("\n")), "code instr:", len(parser.code))


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: translator.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)

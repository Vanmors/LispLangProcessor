import json
from enum import Enum


class Opcode(Enum):
    LD: str = "LD"
    INC: str = "INC"
    ST: str = "ST"
    ADD: str = "ADD"
    SUB: str = "SUB"
    LT: str = "LT"
    GT: str = "GT"
    EQ: str = "EQ"
    MOD: str = "MOD"
    DIV: str = "DIV"
    MUL: str = "MUL"
    JZ: str = "JZ"
    JNZ: str = "JNZ"
    JMP: str = "JMP"
    POP: str = "POP"
    PUSH: str = "PUSH"
    CALL: str = "CALL"
    RET: str = "RET"
    IN: str = "IN"
    OUT: str = "OUT"
    HLT: str = "HLT"
    CMP: str = "CMP"
    JG: str = "JG"
    JE: str = "JE"
    JL: str = "JL"

    @staticmethod
    def getOp(operation: str):
        if operation == '*':
            return Opcode.MUL
        elif operation == '-':
            return Opcode.SUB
        elif operation == '+':
            return Opcode.ADD
        elif operation == '/':
            return Opcode.DIV

    def __str__(self) -> str:
        return self.value


class OpcodeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Opcode):
            return obj.value
        return super().default(obj)


def write_code(filename, code):
    with open(filename, "w", encoding="utf-8") as file:
        # Почему не: `file.write(json.dumps(code, indent=4))`?
        # Чтобы одна инструкция была на одну строку.
        buf = []
        for instr in code:
            buf.append(json.dumps(instr, cls=OpcodeEncoder))
        file.write("[" + ",\n ".join(buf) + "]")


def read_code(filename):

    with open(filename, encoding="utf-8") as file:
        code = json.loads(file.read())

    for instr in code:
        instr["opcode"] = Opcode(instr["opcode"])

    return code

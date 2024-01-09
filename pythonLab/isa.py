import json
from enum import Enum


class Opcode(Enum):
    LD: str = "LD"
    INC: str = "INC"
    ST: str = "ST"
    ADD: str = "ADD"
    SUB: str = "SUB"
    MOD: str = "MOD"
    DIV: str = "DIV"
    MUL: str = "MUL"
    JMP: str = "JMP"
    CALL: str = "CALL"
    IN: str = "IN"
    OUT: str = "OUT"
    HLT: str = "HLT"
    CMP: str = "CMP"
    JG: str = "JG"
    JE: str = "JE"
    JL: str = "JL"

    def __str__(self) -> str:
        return self.value


class OpcodeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Opcode):
            return obj.value
        return super().default(obj)


def write_code(filename: str, code: list):
    with open(filename, "w", encoding="utf-8") as file:
        buf = []
        for instr in code:
            buf.append(json.dumps(instr, cls=OpcodeEncoder))
        file.write("[" + ",\n ".join(buf) + "]")


def read_code(filename: str) -> list:
    with open(filename, encoding="utf-8") as file:
        code = json.loads(file.read())

    for instr in code:
        instr["opcode"] = Opcode(instr["opcode"])

    return code

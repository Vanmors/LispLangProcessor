import logging
import sys

from isa import Opcode, read_code


class DataPath:
    memory = None
    "Память данных. Инициализируется нулевыми значениями."

    alu = None
    "ALU. Инициализируется нулём."

    input_buffer = None
    "Буфер входных данных. Инициализируется входными данными конструктора."

    output_buffer = None
    "Буфер выходных данных."

    var_memory = None

    comparator = None

    def __init__(self, memory_size, input_buffer):
        assert memory_size > 0
        self.memory = []
        self.alu = 0
        self.registers = {}
        self.input_buffer = input_buffer
        self.output_buffer = []
        self.var_memory = {}
        self.comparator = 0

    def latch_register_memory(self, register: str, name: str):
        for instruction in self.memory:
            if not isinstance(instruction, int) and name in instruction:
                self.registers[register] = self.memory[instruction[name] + self.registers["R0"]]

    def increment(self, register: str):
        self.alu = 1
        self.registers[register] += self.alu

    def latch_register_input(self, register: str, value: int):
        if isinstance(value, int):
            self.registers[register] = value
        else:
            self.registers[register] = self.registers[value]

    def sum_alu(self, register1: str, register2: str):
        self.alu = self.registers[register1] + self.registers[register2]

    def signal_output(self, register: str, type_arg: str):
        value = self.registers[register]
        if type_arg == "value":
            logging.debug("output: %s << %s", repr("".join(self.output_buffer)), repr(str(value)))
            self.output_buffer.append(str(value))
        else:
            logging.debug("output: %s << %s", repr("".join(self.output_buffer)), repr(chr(value)))
            self.output_buffer.append(chr(value))

    def save_program_to_mem(self, program: list):
        for i in range(len(program)):
            self.memory.append(program[i])

    def save_to_mem(self, name: str, register: str):
        for instruction in self.memory:
            if not isinstance(instruction, int) and name in instruction:
                self.memory.append(self.registers[register])
                return
        self.memory.append({name: len(self.memory) + 1})
        self.memory.append(self.registers[register])

    def zero(self) -> int:
        return self.alu == 0

    def set_alu(self, register: str):
        self.alu = self.registers[register]

    def signal_input(self, register: str):
        if len(self.input_buffer) == 0:
            self.latch_register_input(register, 0)
            self.set_alu(register)
            return
        symbol = self.input_buffer.pop(0)
        symbol_code = ord(symbol)
        assert -128 <= symbol_code <= 127, "input token is out of bound: {}".format(symbol_code)
        self.registers[register] = symbol_code
        logging.debug("input: %s", repr(symbol))

    def compare_reg(self, register1: str, register2: str):
        self.set_alu(register1)
        if self.alu == self.registers[register2]:
            self.comparator = 0
        elif self.alu > self.registers[register2]:
            self.comparator = 1
        else:
            self.comparator = 2

    def get_comparator(self):
        return self.comparator

    def add_alu(self, register1: str, register2: str, register_out: str):
        self.registers[register_out] = self.registers[register1] + self.registers[register2]

    def div_alu(self, register1: str, register2: str, register_out: str):
        self.registers[register_out] = self.registers[register1] / self.registers[register2]

    def mod_alu(self, register1: str, register2: str, register_out: str):
        self.registers[register_out] = self.registers[register1] % self.registers[register2]

    def sub_alu(self, register1: str, register2: str, register_out: str):
        self.registers[register_out] = self.registers[register1] - self.registers[register2]

    def mul_alu(self, register1: str, register2: str, register_out: str):
        self.registers[register_out] = self.registers[register1] * self.registers[register2]


class ControlUnit:
    program_counter = None
    "Счётчик команд. Инициализируется нулём."

    data_path = None
    "Блок обработки данных."

    _tick = None
    "Текущее модельное время процессора (в тактах). Инициализируется нулём."

    def __init__(self, program, data_path):
        self.program_counter = 0
        self.data_path = data_path
        self._tick = 0

    def tick(self):
        self._tick += 1

    def current_tick(self):
        return self._tick

    def signal_latch_program_counter(self, sel_next):
        if sel_next:
            self.program_counter += 1
        else:
            instr = self.data_path.memory[self.program_counter]
            self.program_counter = instr["arg"] - 1

    def decode_and_execute_control_flow_instruction(self, instr, opcode):
        if opcode is Opcode.HLT:
            raise StopIteration()

        if opcode is Opcode.JMP:
            addr = instr["arg"] - 1
            self.program_counter = addr
            self.tick()

            return True
        if opcode is Opcode.JG:
            if self.data_path.get_comparator() == 1:
                self.signal_latch_program_counter(sel_next=True)
            else:
                self.signal_latch_program_counter(sel_next=False)
            self.tick()

        if opcode is Opcode.JL:
            if self.data_path.get_comparator() == 2:
                self.signal_latch_program_counter(sel_next=True)
            else:
                self.signal_latch_program_counter(sel_next=False)
            self.tick()

            return True
        if opcode is Opcode.JE:
            if self.data_path.get_comparator() == 0:
                self.signal_latch_program_counter(sel_next=True)
            else:
                self.signal_latch_program_counter(sel_next=False)
            self.tick()

            return True
        return False

    def decode_and_execute_instruction(self):
        instr = self.data_path.memory[self.program_counter]
        opcode = instr["opcode"]

        if self.decode_and_execute_control_flow_instruction(instr, opcode):
            return

        if opcode in {Opcode.IN}:
            self.data_path.signal_input(instr["register"])
            self.signal_latch_program_counter(sel_next=True)
            self.tick()

        elif opcode == Opcode.LD:
            try:
                self.data_path.latch_register_input(instr["register"], instr["arg"])
            except KeyError:
                self.data_path.latch_register_memory(instr["register"], instr["name"])
            self.signal_latch_program_counter(sel_next=True)
            self.tick()

        elif opcode == Opcode.INC:
            self.data_path.increment(instr["register"])
            self.signal_latch_program_counter(sel_next=True)
            self.tick()

        elif opcode is Opcode.OUT:
            if "type" in instr:
                self.data_path.signal_output(instr["register"], instr["type"])
            else:
                self.data_path.signal_output(instr["register"], None)
            self.signal_latch_program_counter(sel_next=True)
            self.tick()
        elif opcode == Opcode.CMP:
            self.data_path.compare_reg(instr["register"], instr["arg"])
            self.signal_latch_program_counter(sel_next=True)
            self.tick()
        elif opcode == Opcode.ST:
            self.data_path.save_to_mem(instr["name"], instr["register"])
            self.signal_latch_program_counter(sel_next=True)
            self.tick()
        elif opcode == Opcode.ADD:
            registers = instr["arg"]
            self.data_path.add_alu(registers[0], registers[1], instr["register"])
            self.signal_latch_program_counter(sel_next=True)
            self.tick()
        elif opcode == Opcode.DIV:
            registers = instr["arg"]
            self.data_path.div_alu(registers[0], registers[1], instr["register"])
            self.signal_latch_program_counter(sel_next=True)
            self.tick()
        elif opcode == Opcode.MOD:
            registers = instr["arg"]
            self.data_path.mod_alu(registers[0], registers[1], instr["register"])
            self.signal_latch_program_counter(sel_next=True)
            self.tick()
        elif opcode == Opcode.SUB:
            registers = instr["arg"]
            self.data_path.sub_alu(registers[0], registers[1], instr["register"])
            self.signal_latch_program_counter(sel_next=True)
            self.tick()
        elif opcode == Opcode.MUL:
            registers = instr["arg"]
            self.data_path.mul_alu(registers[0], registers[1], instr["register"])
            self.signal_latch_program_counter(sel_next=True)
            self.tick()

    def __repr__(self):
        """Вернуть строковое представление состояния процессора."""
        state_repr = "TICK: {:3} PC: {:3} ALU: {}".format(
            self._tick,
            self.program_counter,
            self.data_path.alu,
        )

        instr = self.data_path.memory[self.program_counter]
        opcode = instr["opcode"]
        instr_repr = str(opcode)

        if "register" in instr:
            instr_repr += " {}".format(instr["register"])

        if "name" in instr:
            instr_repr += " {}".format(instr["name"])

        return "{} \t{}".format(state_repr, instr_repr)


def simulation(code, input_tokens, memory_size, limit):
    data_path = DataPath(memory_size, input_tokens)
    control_unit = ControlUnit(code, data_path)
    instr_counter = 0

    data_path.save_program_to_mem(code)

    logging.debug("%s", control_unit)
    try:
        while instr_counter < limit:
            control_unit.decode_and_execute_instruction()
            instr_counter += 1
            logging.debug("%s", control_unit)
    except EOFError:
        logging.warning("Input buffer is empty!")
    except StopIteration:
        pass

    if instr_counter >= limit:
        logging.warning("Limit exceeded!")
    logging.info("output_buffer: %s", repr("".join(data_path.output_buffer)))
    return "".join(data_path.output_buffer), instr_counter, control_unit.current_tick()


def main(code_file, input_file):
    codes = read_code(code_file)

    with open(input_file, encoding="utf-8") as file:
        input_text = file.read()
        input_token = []
        for char in input_text:
            input_token.append(char)
    output, instr_counter, ticks = simulation(
        codes,
        input_token,
        100,
        1000,
    )
    print("".join(output))
    print("instr_counter: ", instr_counter, "ticks:", ticks)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    assert len(sys.argv) == 3, "Wrong arguments: machine.py <code_file> <input_file>"
    _, code_file, input_file = sys.argv
    main(code_file, input_file)

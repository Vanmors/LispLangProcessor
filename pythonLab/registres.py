class Registres:
    def __init__(self):
        self.registers = {}

    def allocate_register(self, reg_name=None):
        if reg_name:
            self.registers[reg_name] = None

    def get_register(self, variable_name: str):
        return self.registers.get(variable_name)

    def get_free_register(self) -> str:
        for i in range(len(self.registers)):
            if self.registers[f"R{i + 1}"] is None:
                return f"R{i + 1}"
        raise ValueError("Registers is over.")

    def put_in_register(self, register: str, value: int):
        self.registers[register] = value

    def clean_register(self, register):
        self.registers[register] = None

# Simulate EVM memory

class Memory():
    def __init__(self):
        self.data = {}
        self.size = 0

    def read(self, address):
        if address in self.data:
            return self.data[address]
        else:
            return 0

    def write(self, address, value):
        if address > self.size:
            self.size = address + 1
        self.data[address] = value

    def op(self, address, value, is_write):
        if is_write:
            assert(value >= 0 and value < 256)
            self.write(address, value)
        else:
            assert(self.read(address) == value)



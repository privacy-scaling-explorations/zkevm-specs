# Simulate EVM storage


class Storage:
    def __init__(self):
        self.data = {}
        self.size = 0

    def read(self, address):
        self.track_size(address)
        if address in self.data:
            return self.data[address]
        else:
            return 0

    def write(self, address, value):
        assert 0 <= value and value < 256
        self.track_size(address)
        self.data[address] = value

    def op(self, address, value, is_write):
        if is_write:
            self.write(address, value)
        else:
            assert self.read(address) == value

    def track_size(self, address):
        if address >= self.size:
            self.size = address + 1

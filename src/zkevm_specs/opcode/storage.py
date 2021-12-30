# Simulate EVM storage


# TODO: should be in state

class Storage:
    def __init__(self):
        self.data = {}

    def read(self, address):
        if address in self.data:
            return self.data[address]
        else:
            return 0

    def write(self, address, value):
        # assert 0 <= value and value < 256
        self.data[address] = value

    def op(self, address, value, is_write):
        if is_write:
            # TODO: revert
            self.write(address, value)
        else:
            assert self.read(address) == value

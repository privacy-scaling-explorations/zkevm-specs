# Simulate an Ethereum contract's storage.
# The storage consists of a key-value map where
# both the key and the value are 256 bit numbers.


class Storage:
    def __init__(self):
        self.data = {}

    def has_key(self, key):
        return key in self.data

    def read(self, key):
        if self.has_key(key):
            return self.data[key]
        return 0

    def write(self, key, value):
        assert 0 <= key and key < 2 ** 256
        assert 0 <= value and value < 2 ** 256
        self.data[key] = value

    def op(self, key, value, is_write):
        if is_write:
            self.write(key, value)
        else:
            assert self.read(key) == value

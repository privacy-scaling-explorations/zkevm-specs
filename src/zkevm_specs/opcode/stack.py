from ..encoding import U256, is_circuit_code

# Simulate evm stack and pop & dupx op code


class Stack():
    def __init__(self):
        self.items = [0] * 1024
        self.top = 1024

    def is_empty(self):
        return self.top == 1024

    def size(self):
        return 1024  # fixed size

    def push(self, evm_word):
        if self.top == 0:
            return  # or throw error

        self.top -= 1
        self.items[self.top] = evm_word

    def peek(self):
        # self.items.append(item)
        return self.items[self.top]
    
    # simulate evm pop op code
    def pop(self):
        if self.top == 1024:
            return  # or throw error

        self.items[self.top] = 0
        self.top += 1

    # simulate evm dupx op code from DUP1 to DUP16
    def dupx(self, pos):
        if pos < 1 or pos > 16:
            return  # or throw error

        evm_word = self.items[self.top + pos - 1]
        self.push(evm_word)

    # simulate evm swapx op code from swap1 to swap16
    def swapx(self, pos):
        if pos < 1 or pos > 16:
            return # or throw error

        top_word = self.items[self.top]
        swap_word = self.items[self.top + pos]
        self.items[self.top] = swap_word
        self.items[self.top + pos] = top_word


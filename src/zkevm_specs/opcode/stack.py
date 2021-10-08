from ..encoding import U256, is_circuit_code

# Simulate evm stack and pop & dupx op code 
class Stack():
    def __init__(self):
         self.items = [0] * 1024
         self.top = 1024

    def is_empty(self):
        return self.top == 1024

    def size(self):
        return 1024 # fixed size

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
            return # or throw error

        self.items[self.top] = 0
        self.top += 1

    # simulate evm dupx op code from DUP1 to DUP16
    def dupx(self, pos):
        if pos < 1 or pos > 16:
            return # or throw error

        evm_word = self.items[self.top + pos - 1]
        self.push(evm_word)

@is_circuit_code
def check_dupx():
    evm_stack = Stack()
    word1:U256 = 20
    word2:U256 = 30
    evm_stack.push(word1)
    evm_stack.push(word2)
    assert(word2 == evm_stack.peek())
    evm_stack.dupx(2)
    assert(word1 == evm_stack.peek())
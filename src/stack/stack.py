#from ./encoding/.U256

# Simulate evm stack
class Stack():
    def __init__(self):
         self.items = [0] * 1024
         self.top = 1024


    def is_empty(self):
        return self.top == 1024

    def size(self):
        return 1024 ## fixed size

    def push(self, evm_word):
        if self.top == 0:
            return  ## or throw error

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

    # simulate evm dupx op code
    def dupx(self, pos):
        if pos < 1 or pos > 16:
            return # or throw error

        evm_word = self.items[self.top + pos - 1]
        self.push(evm_word)


if __name__ == "__main__":
    evm_stack = Stack()
    word1 = 20
    word2 = 30
    evm_stack.push(word1)
    evm_stack.push(word2)
    assert(word2 == evm_stack.peek())
    evm_stack.dupx(2)
    assert(word1 == evm_stack.peek())
    evm_stack.pop()
    evm_stack.pop()
    evm_stack.pop()
    assert(evm_stack.is_empty())

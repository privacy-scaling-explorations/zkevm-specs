# AND op code

## Procedure  

A stack initalize empty with stack pointer to 1024, pop operation can only happen when stack is not empty, and it will increase by 1 of stack pointer.  

The And value will be dropped directly without no any more checking & utilizing.

## Constraints

1. opId = OpcodeId(0x16u8)
2. state transition:  
    - gc + 3
    - stack_pointer + 1
    - pc + 1
    - gas + 3


## Exceptions

1. stack underflow: when stack is empty
2. gas out: remaining gas is not enough   

```python
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
        self.top -= 3
        self.items[self.top] = evm_word[0]
        self.items[self.top - 1] =evm_word[1]
        self.items[self.top - 2] =evm_word[2]
    def peek(self):
        # self.items.append(item)
        return self.items[self.top]
    def pop(self):
        if self.top == 1024:
            return ## or throw error
        self.items[self.top] = 0
        self.items[self.top + 1] = 0
        self.items[self.top + 2] = 0
        self.top += 3
```
# POP op code

## Procedure
   A stack initalize empty with stack pointer to 1024,  pop operation can only happen when stack is not empty,  and it will increase by 1 of stack pointer.  
   the poped value will be dropped directly without no any more checking & utilizing.


## Constraints
   1. opId = OpcodeId(0x50)
   2. state transition:  
      gc + 1
      stack_pointer + 1
      pc + 1
      gas + 2

## Exceptions
   1. stack underflow: when stack is empty
   2. gas out: remaining gas is not enough 

## Stack pseudo code
```
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

    def pop(self):
        if self.top == 1024:
            return ## or throw error

        self.items[self.top] = 0
        self.top += 1
```
# DUPX op code
## Procedure
   dupx picks up value at 'x' position inside the stack, then push the value to stack. 

## Constraints
   1. opId = OpcodeId(0x80...0x16)
   2. state transition:  
      gc + 2 (read + write)
      stack_pointer - 1
      pc + 1
      gas + 3
   3. Bussmapping lookups:
      position 'x' range from [1..16]
      operand must come from position 'x' inside stack
      position 'x' value equals stack top value when this operation done

## Exceptions
   1. gas out: remaining gas is not enough 
   2. stack overflow: when stack is full, which means stack pointer is 0 before dupx
   code refer to src/stack/stack.py
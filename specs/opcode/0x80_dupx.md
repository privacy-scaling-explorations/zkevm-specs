# DUPX op code
## Procedure
   dupx represents op codes of dup1....dup16. which picks up value at 'x' position inside the stack, then push the value to stack.

## Constraints
   1. opId = OpcodeId(0x80...0x8F)
   2. state transition:  
       gc + 2 (read + write)  
      stack_pointer - 1  
      pc + 1  
      gas + 3  
   3. lookups: 1 range lookup + 2 bussmapping lookups:  
      position 'x' range from [1..16]  
      operand must come from position 'x' inside stack  
      position 'x' value equals stack top value when this operation done  

## Exceptions
   1. gas out: remaining gas is not enough
   2. stack overflow: when stack is full, which means stack pointer is 0 before dupx  
   3. stack underflow: when stack length is less than dup position 'x'  
 
## Code  
   refer to src/zkevm_specs/opcode/stack.py
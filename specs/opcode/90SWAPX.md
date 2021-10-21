# SWAPX op code
## Procedure
   Swapx represents op codes of swap1....swap16. which swaps the top of the stack with the 'x+1'th last element. For example, SWAP3 means swaping the top of the stack with the 4th last element

## Constraints
   1. opId = OpcodeId(0x90...0x9F)
   2. state transition:  
      gc + 4 (2 reads + 2 writes)  
      stack_pointer  
      pc + 1  
      gas + 3  
   3. lookups: 1 range lookup + 4 bussmapping lookups:    
      position 'x' range from [1..16]  
      first operand must come from top of stack   
      second operand must come from position 'x+1' inside stack  
      when this operation done, the top stack value must equals 'x+1'th value before
      when this operation done, the 'x+1'th stack value must equals the top value before

## Exceptions
   1. gas out:   
   remaining gas is not enough
   2. stack underflow:   
   when stack length is less than swap position 'x + 1', i.e stack have 3 elements but the op is swap3, swap4, ..., swap16. Underflow condition for `swap_x`: `0 <= x +  stack_pointer - 1024 <= 16`, which requires a `Range17` lookup check.
 
## Code  
   refer to src/zkevm_specs/opcode/stack.py
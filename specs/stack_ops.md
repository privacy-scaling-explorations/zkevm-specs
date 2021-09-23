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

## Others stack codes (dupx .etc)
# Coinbase op code

## Procedure

The `COINBASE` opcode get the coinbase address from current block and push to the stack

## EVM behavior

The `COINBASE` opcode loads an `address` (20 bytes of data) from block context.
then push the `address` to the stack.

## Circuit behavior

1. construct block context table 
2. do bussmapping lookup for stack write operation
3. other implicit check: bytes length

## Constraints

1. opId = 0x41
2. state transition:\
   gc + 1 ( 1 stack write)\
   stack_pointer - 1
   pc + 1\
   gas + 2
3. lookups:  2  
   `address` is on the top of stack  
   `address` is in block context table

5. others:  
   `address` is 20 bytes length

## Exceptions

1. gas out:\
   remaining gas is not enough
2. stack overflow:\
   stack is full, stack pointer = 0

## Code

Refer to src/zkevm_specs/evm/execution/coinbase.py

# MCOPY opcode

## Procedure

The `MCOPY` opcode pops `dest_offset`, `offset` and `size` from the stack.
It then copies `size` bytes in the current environment from memory at an `offset` to the memory at a `dest_offset`. For out-of-bounds scenarios - the memory is extended with respective gas cost applied.

The gas cost of `MCOPY` opcode consists of two parts:

1. A constant gas cost: `3 gas`
2. A dynamic gas cost: cost of memory expansion and copying (variable depending on the `size` copied to memory)

## Constraints

1. OpcodeId check

- opId == OpcodeId(0x5E)

2. State Transition

   1.
   2.
   3.

3. Lookups

   1.
   2.

## Exceptions

1. stack underflow: `1022 <= stack_pointer <= 1024`
2. out of gas: remaining gas is not enough

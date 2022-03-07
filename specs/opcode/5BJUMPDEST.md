# JUMPDEST opcode

## Procedure

JUMPDEST is a special opcode which only marks an address that can be jumped to. In other words, it is metadata to annotate possible jump destinations.

For example, in the below opcode sequences, JUMPDEST marks '004D' can be jumped to, if there is no JUMPDEST annotation, Jumping to '004D' will fail as jump opcode will require JUMPDEST as a valid destination.

```
      004D    5B  JUMPDEST  
      004E    34  CALLVALUE  
      004F    80  DUP1  
      0050    15  ISZERO  
      0051    60  PUSH1 0x58  
      0053    57  *JUMPI  
      0054    60  PUSH1 0x00  
      0056    80  DUP1  
      0057    FD  *REVERT  
      0058    5B  JUMPDEST  
      0059    50  POP  
      005A    60  PUSH1 0x62  
      005C    60  PUSH1 0x04  
      005E    35  CALLDATALOAD  
      005F    60  PUSH1 0x86  
      0061    56  *JUMP"  
```

## Constraints

1. opId = OpcodeId(0x5B)
2. state transition:
   - gc
   - stack_pointer
   - pc + 1
   - gas + 1
3. lookups:
   none (since there is no operands required)

## Exceptions

1. gas out:   remaining gas is not enough

## Code

none

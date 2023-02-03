# MLOAD & MSTORE & MSTORE8 opcodes

## Procedure

### EVM behavior

`MLOAD` loads a word (32 bytes of data) from memory. This is done by popping the `address` from the stack. The data at `[address, address + 31]` is then loaded from memory and pushed to the stack
`MSTORE` writes a word (32 bytes of data) to memory. This is done by popping two value, the `address` and then the `value`, from the stack. `value` is then written to memory at `[address, address + 31]`
`MSTORE8` works similarly to `MSTORE` except that only the LSB of `value` is written to `address`

1. A const gas cost: `3 gas`
2. A dynamic gas cost: a dynamic gas depends on the highest memory location accessed

The highest memory location is calculated as follows:

```
MLOAD, MSTORE: address + 32 (32 bytes are read/written)
MSTORE8: address + 1 (a byte is written)
```

The memory size is calculated as follows:

```
memory_size(address) := ceil(address/32)
```

The memory cost is calculated as follows:

```
Gmem := 3
memory_cost(memory_size) := Gmem * memory_size + floor(memory_size * memory_size / 512)
```

The gas cost charged for the op is the additional `memory_size` needed:

```
MLOAD/MSTORE: offset := 32, MSTORE8: offset := 1
next_memory_size := max(curr_memory_size, memory_size(address + offset))
memory_gas_cost := memory_cost(next_memory_size) - memory_cost(curr_memory_size)
```

### Circuit behavior

The `MemoryGadget` takes arguments `address: [u8;32]`, `value: [u8;32]`, `curr_memory_size: u64`, `opcode: u8`. There are also some additional helper inputs used by the general gadgets used for the implementation.

There is a check if `opcode` is `MLOAD`, `MSTORE` or `MSTORE8`, which is used to change some operations so the correct logic for each opcode is done.

The memory expansion calculations and the memory addressing use a partial address value consisting of the 5 LSBs of address. If any other of the higher bytes are used an out-of-gas exception is always thrown.

The new memory size and gas necessary for a potential memory expansion is calculated using the formulas above.

For the stack busmapping lookups, the top value is always the `address`. Then, depending on the opcode:

- `MLOAD`: `value` is pushed on top of the stack (`stack_offset == 0; is_write == true`)
- `MSTORE`/`MSTORE8`: `value` is popped from top of the stack (`stack_offset == 1; is_write == false`)

For `MLOAD`/`MSTORE` 32 memory busmapping lookups are used (1 lookup needed for each byte) to access the memory at `[address, address + 31]` using the byte values of `value`:

- `MLOAD`: the lookup is a read op (`is_write == false`)
- `MSTORE`/`MSTORE8`: the lookup is a write op (`is_write == true`)
  For `MSTORE8` a single busmapping lookup is used to write the LSB of `value` to `address`, but this lookup is done 32 times so we can reuse the same lookup constraints.

## Constraints

1. opcodeId checks
   1. opId === OpcodeId(0x51) for `MLOAD`
   2. opId === OpcodeId(0x52) for `MSTORE`
   3. opId === OpcodeId(0x53) for `MSTORE8`
2. state transition:
   - gc
     - `MLOAD`/`MSTORE`:  +34 (2 stack operations + 32 memory reads/writes)
     - `MSTORE8`: +3 (2 stack operations + 1 memory write)
   - stack_pointer
     - `MLOAD`: remains the same
     - `MSTORE`: -2
   - pc + 1
   - gas + 3 + `memory_gas_cost`
   - memory_size is set to `next_memory_size`
3. lookups:
   - `MLOAD`/`MSTORE`: 34 busmapping lookups, `MSTORE8`: 3 busmapping lookups
     - stack:
       - `address` is popped off the top of the stack
       - `value`
         - is pushed on top of the stack for `MLOAD`
         - is popped off the top of the stack for `MSTORE`/`MSTORE8`
     - memory:
       - `MLOAD`/`MSTORE`: The 32 bytes of `value` are read/written from/to memory at `address`.
       - `MSTORE8`: The LSB of `value` is written to `address`.
   - 29 fixed lookups

## Exceptions

1. stack underflow:
   - the stack is empty: `1024 == stack_pointer`
   - only for `MSTORE`/`MSTORE8`: contains a single value: `1023 == stack_pointer`
2. out of gas:
   - Any of other byte values of `address` other than the 5 LSBs are non-zero
   - The remaining gas after the opcode cost of `3` + the memory expansion gas cost is insufficient

## Code

Please refer to `src/zkevm-specs/opcode/mload_mstore.py`.

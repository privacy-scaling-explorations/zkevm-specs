# SLOAD & SSTORE

## Procedure

### EVM behavior

Storage is a key-value map where both the key and the values are words of 32
bytes.

The `SLOAD` opcode loads a word (32 bytes of data) from storage into the stack.
This is done by popping the `key` from the stack, and the value at
`STORAGE[key]` is then pushed onto the stack.

The `SSTORE` opcode writes a word (32 bytes of data) from the stack into
storage.  This is done by popping the `key` from the top and the `value` from
the second position of the stack, and then writing `STORAGE[key] = value`.

### Access Sets

As per [EIP-2929](https://eips.ethereum.org/EIPS/eip-2929), these two opcodes
update the `Touched Storage Slots` set with the address of the current execution
context and the accessed key as:

```
touched_storage_slots = touched_storage_slots ∪ { (context_address, target_storage_key) }
```

### Gas Costs and Refunds

Computing the gas costs for these opcodes requires knowing whether the slot
`(context_address, key)` has been touched during the current transaction using
the `Touched Storage Slots` set.  In case of an `SSTORE`, we also need to know
the current and original values of that key, where the original value is the
value in that key at the beginning of the transaction.

The [Yellow Paper](https://ethereum.github.io/yellowpaper/paper.pdf) defines the gas costs for these two opcodes as follows:

#### SLOAD 

- `G_warmaccess`, if the slot has been touched
- `G_coldsload`, otherwise

#### SSTORE

Let `v0` be the original value of the storage slot.
Let `v` be the current value.
Let `v'` be the new value.

`base_gas =`
- `0`, if the slot has been touched
- `G_coldsload`, otherwise

`extra_gas =`
- `G_warmaccess`, if `v = v' or v0 != v`
- `G_sset`, if `v != v' and v0 = v and v0 = 0`
- `G_sreset`, if `v != v' and v0 = v and v0 != 0`

The spent gas is `base_gas + extra_gas`.

`refund =`
- `R_sclear`, if `v0 != 0 and v = 0`
- `r_dirtyclear` + `r_dirtyreset`, if `v0 != 0 and v' = 0`
- `0`, otherwise

The refunded gas is `refund`.

where

`r_dirtyclear =`
- `-R_sclear`, if `v0 != 0 and v = 0`
- `R_sclear`, if `v0 != 0 and v' = 0`
- `0`, otherwise

`r_dirtyreset =`
- `G_sset - G_warmaccess`, if `v0 = v' and v0 = 0`
- `G_sreset - G_warmaccess`, if `v0 = v' and v0 != 0`
- `0`, otherwise

```
G_warmaccess = 100
G_coldsload = 2100
G_sset = 20000
G_sreset = 2900
R_sclear = 15000
```

### Circuit behavior

The `StorageGadget` takes arguments

- `opcode: u8`
- `key: [u8;32]`
- `new_value: [u8;32]`
- `original_value: [u8;32]`
- `current_value: [u8;32]`
- `is_storage_slot_touched: bool`

There is a check if `opcode` is `SLOAD` or `SSTORE`, which is used to change
some operations so the correct logic for each opcode is done.

The `storage_slot_touched` Access Set is necessary in order to compute the gas
and refund amounts using the procedure above, extracted from the Yellow Paper.

For the stack busmapping lookups, the top value is always the `key`. Then,
depending on the opcode:

- `SLOAD`: `new_value` is pushed on top of the stack (`stack_offset == 0; is_write == true`)
- `SSTORE`: `new_value` is popped from the top of the stack (`stack_offset == 1; is_write == false`)

For `SLOAD`/`SSTORE` 1 storage busmapping lookup is used to access the storage
at `[key]` using the byte values of `value`:

- `SLOAD`: the lookup is a read op (`is_write == false`)
- `SSTORE`: the lookup is a write op (`is_write == true`)

## Constraints

1. opcodeId checks
   1. opId == OpcodeId(0x54) for `SLOAD`
   2. opId == OpcodeId(0x55) for `SSTORE`
2. state transition:
   - gc
     - `SLOAD`/`SSTORE`: +3 (2 stack operations + 1 storage read/write)
   - stack_pointer
     - `SLOAD`: remains the same
     - `SSTORE`: -2
   - pc + 1
   - gas + `gas_cost` - `refund`
3. lookups:
   - `SLOAD`/`SSTORE`: 1 busmapping lookup
     - stack:
       - `key` is popped off the top of the stack
       - `value`
         - is pushed on top of the stack for `SLOAD`
         - is popped off the top of the stack for `SSTORE`
     - storage:
       - `SLOAD`/`SSTORE`: The 32 bytes of `value` are read/written from/to storage at `key`.
   - ?? fixed lookups

## Exceptions

1. stack underflow:
   - the stack is empty: `1024 == stack_pointer`
   - only for `SSTORE`: the stack contains a single value: `1023 == stack_pointer`
2. out of gas:
   - insufficient gas for read/write

## Code

Please refer to `src/zkevm-specs/opcode/sload_sstore.py`.
 

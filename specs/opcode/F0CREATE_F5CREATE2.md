# CREATE and CREATE2 opcodes

## Procedure

### EVM behavior

The `CREATE` and `CREATE2` opcodes create a new call context at a new address.
They transfer the specified amount of ether from the caller address to the new address and then execute the specified initialization code.
The bytecode of the new address will be updated to be the return bytes of this initialization code.

The following values are popped from the stack:
1. `value` - The amount of ether to transfer from the caller to the new address.
2. `offset` - The memory offset in the caller's memory where the initialization code starts.
3. `size` - The length of the initialization code, in bytes.
4. `salt` - Only for `CREATE2`: salt for the hash that will determine the new address.

If the initialization call is successful, the new address will be pushed to the stack. If not, 0 will be pushed instead.

The gadget does several things in the caller's call context:
1. Perform the following pre-checks: check the stack depth, validate the sender's balance, verify the sender's nonce, and ensure the existence of the contract address. If any of these checks fail, restore the caller's context.
2. Expands memory
3. Add `new_address` to the access list
4. Calculate gas cost for this step.
5. Uses EIP150 to calculate how much gas will remain in the caller's context.

The memory size is calculated as follows:

```
calc_memory_size(offset, length) := 0 if length == 0 else ceil((offset + length) / 32)
```

`new_address` is calculated as follows:

```
new_address := keccak256([0xff] + caller_address + salt + keccak256(initialization_bytecode)) if op_id == CREATE2 else rlp([caller_address, caller_address.nonce])
```

The memory expansion gas cost is:

```
MEMORY_EXPANSION_QUAD_DENOMINATOR := 512
MEMORY_EXPANSION_LINEAR_COEFF := 3
calc_memory_cost(memory_size) := MEMORY_EXPANSION_LINEAR_COEFF * memory_size + floor(memory_size * memory_size / MEMORY_EXPANSION_QUAD_DENOMINATOR)
```

The gas cost charged for the additional `memory_size` is:

```
next.memory_size := max(
    curr.memory_size,
    memory_size(offset, length),
)
memory_expansion_gas_cost := calc_memory_cost(next.memory_size) - memory_cost(curr.memory_size)
```

The `gas_cost` for the step is:

```
GAS_COST_CREATE := 32000
KECCAK_WORD_GAS_COST := 6
GAS_COST_INITCODE_WORD := 2  # EIP-3860

keccak_gas_cost = KECCAK_WORD_GAS_COST * size if op_id == CREATE2 else 0
initcode_gas_cost = GAS_COST_INITCODE_WORD * size
gas_cost = (
    GAS_COST_CREATE
    + memory_expansion_gas_cost
    + keccak_gas_cost
    + initcode_gas_cost
)
```

The `callee_gas_left` for new context by rule in EIP150 is calculated like this:

```
gas_available := curr.gas_left - gas_cost
callee_gas_left := min(gas_available - floor(gas_available / 64), gas)
```

In the initialization call context, it does:

1. Transfer `value` from the caller address to the new address
2. Executes the initialization bytecode
3. Update the bytecode of the new address to be the `return_data` of execution

### Circuit behavior

The circuit takes the starting `rw_counter` as next call's `call_id` to make sure each call has a unique `call_id`.

It pops 3 words for `CREATE` and 4 words for `CREATE2` from the stack.
In both cases, it then pushes 1 word to the stack.

If all the pre-checks pass, then
  - It checks that `callee.is_persistent = caller.is_persistent and caller.is_success`.
  - If the caller is not persistent, we need to propagate the `rw_counter_end_of_reversion` to make sure every state update in the new call has a corresponding reversion.
  - It stores the current call context by writing the current values `rw_table` and checks that the new call context is setup correctly by reading to `rw_table`, and then does a step state transition to the call and begins the execution o the initialization bytecode.
Otherwise, it restores the current call context.
## Code

Please refer to `src/zkevm_specs/evm/execution/create.py`.

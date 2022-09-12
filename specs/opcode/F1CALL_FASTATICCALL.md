# CALL and STATICCALL opcodes

## Procedure

### EVM behavior

The `CALL` opcode transfer specified amount of ether to callee and creates a new call context and switch to it. This is done by popping serveral words from stack:

1. `gas` - The amount of gas caller want to give to callee (capped by rule in EIP150)
2. `callee_address` - The ether recipient whose code is to be executed (by taking the 20 LSB of popped word)
3. `value` - The amount of ether to be transferred (non-existent for opcode `STATICCALL`)
4. `call_data_offset` - The offset of call_data chunk in caller's memory as call_data for callee
5. `call_data_length` - The length of call_data chunk
6. `return_data_offset` - The offset of return_data chunk in caller's memory, which will be set to return_data from callee after call
7. `return_data_length` - The length of return_data chunk

The `STATICCALL` opcode is equivalent to `CALL`, except that it does not allow any state modifying instructions (is_static == 1) or sending ether to callee in the sub context. It only pops 6 words from stack `gas`, `callee_address`, `call_data_offset`, `call_data_length`, `return_data_offset` and `return_data_length` (without the third popped word `value` for opcode `CALL`).

Before switching call context to the new one, it does several things:

1. Expand memory
2. Add `callee_address` into access list
3. Calculate `gas_cost` and check `gas_left` is enough
4. Calculate `callee_gas_left` for new context by rule in EIP150
5. Check `depth` is less than `1024`
6. Check `value` could be transfer (unnecessary for opcode `STATICCALL`)

The memory size is calculated as follows:

```
calc_memory_size(offset, length) := ceil((offset + length) / 32) if length != 0 else 0
```

The memory expansion gas cost is calculated like this:

```
MEMORY_EXPANSION_QUAD_DENOMINATOR := 512
MEMORY_EXPANSION_LINEAR_COEFF := 3
calc_memory_cost(memory_size) := MEMORY_EXPANSION_LINEAR_COEFF * memory_size + floor(memory_size * memory_size / MEMORY_EXPANSION_QUAD_DENOMINATOR)
```

The gas cost charged for the op is the additional `memory_size` needed:

```
next.memory_size := max(
    curr.memory_size,
    memory_size(call_data_offset, call_data_length),
    memory_size(return_data_offset, return_data_length),
)
memory_expansion_gas_cost := calc_memory_cost(next.memory_size) - memory_cost(curr.memory_size)
```

The `gas_cost` is calculated like this (has_value == 0 for opcode `STATICCALL`):

```
GAS_COST_WARM_ACCESS := 100
GAS_COST_ACCOUNT_COLD_ACCESS := 2600
GAS_COST_CALL_EMPTY_ACCOUNT := 25000
GAS_COST_CALL_WITH_VALUE := 9000
gas_cost = (
    GAS_COST_WARM_ACCESS
    + GAS_COST_WARM_ACCESS if is_warm_access else GAS_COST_ACCOUNT_COLD_ACCESS
    + has_value * (GAS_COST_CALL_WITH_VALUE + is_account_empty * GAS_COST_CALL_EMPTY_ACCOUNT)
    + memory_expansion_gas_cost
)
```

The `callee_gas_left` for new context by rule in EIP150 is calculated like this:

```
gas_available := curr.gas_left - gas_cost
callee_gas_left := min(gas_available - floor(gas_available / 64), gas)
```

After switching call context, it does:

1. Transfer `value` (unnecessary for opcode `STATICCALL`)
2. Execution
   1. If `callee_address` is a precompiled, it runs the pre-defined handler
   2. Otherwise, it takes callee's code for execution
3. Copy `return_data` of execution to caller specified memory chunk
4. Push `1` to stack if it succeeds, otherwise push `0` and revert everything done after switching call context

### Circuit behavior

The circuit takes current `rw_counter` as next call's `call_id` to make sure each call has a unique `call_id`.

It pops the 7 words for opcode `CALL` or 6 words for opcode `STATICCALL` from stack, and take `result` of execution from prover to and push it to stack instantly. The reason it pushes the `result` before execution is to avoid the redundancy that every terminating `ExecutionState` needs to do the push. And it can do this because the `result` will also be in call context and checked in terminating `ExecutionState`s.

It then checks the new call `is_persistent` only if current `is_persistent` and `result` of execution is success. If the new call is not persistent is due to current's call is not persistent, we need to propagate the `rw_counter_end_of_reversion` to make sure every state update has a corresponding reversion.

Finally it stores current call context by writting to `rw_table` and checks the new call context is setup correctly by reading to `rw_table`, then does step state transition to a initialized one and begin the execution.

In the end of execution, the terminating `ExecutionState` like `RETURN`, `REVERT` will copy the `return_data` to caller specified chunk.

## Code

Please refer to `src/zkevm_specs/evm/execution/call_staticcall.py`.

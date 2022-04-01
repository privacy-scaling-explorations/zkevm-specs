# CopyCodeToMemory

## Circuit Behaviour

`CopyCodeToMemory` is an internal execution state and doesn't correspond to an EVM opcode. It verifies that data from bytecode table has been written to memory. This gadget can in one iteration only copy `MAX_COPY_BYTES` number of bytes, hence for lengths longer than the bound the gadget loops itself until there are no more bytes to be copied.

The `CopyCodeToMemory` circuit uses the `BufferReaderGadget` to check if the access is out of bounds and needs 0 padding.

The `CopyCodeToMemory` circuit looks up the bytes read from buffer against both the bytecode table and the RW table (memory-write). An additional constraint checks whether or not the copying is finished, and if not, it constrains the next execution state to continue being `CopyCodeToMemory` while also adding constraints to the next step's auxiliary data.

## Constraints

We define `n_bytes_read` as the number of bytes read from the bytecode table. `n_bytes_read <= MAX_COPY_BYTES`.

We define `n_bytes_written` as the number of bytes written to the memory. `n_bytes_written <= MAX_COPY_BYTES`.

`n_bytes_read` differs from `n_bytes_written` in out-of-bound cases where nothing is read from the bytecode table but a `0` is written to memory.

1. State Transition:
   - rw_counter: `n_bytes_written`
2. Lookups:
   - `n_bytes_read` lookups from bytecode table
   - `n_bytes_written` lookups from RW table (memory-write)

## Exceptions

No exceptions for `CopyCodeToMemory` since it is an internal state.

## Code

Please refer to `src/zkevm_specs/evm/execution/copy_code_to_memory.py`.

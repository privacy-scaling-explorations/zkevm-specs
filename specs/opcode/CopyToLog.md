# CopyToLog

## Circuit behaviour

`CopyToLog` is an internal execution state and doesn't correspond to a EVM opcode. It copies
data from memory RW `Txlog` entries. This gadget needs to loop itself if it hasn't finished
the copy.

The `CopyToLog` circuit uses gadget `BufferReaderGadget` like `CopyToMemory`.

In the `CopyToLog` circuit, it needs to lookup the bytes that is read from the buffer according
to `BufferReaderGadget` in the memory. it needs to check if the copy is finished. If not, it constrains the
next execution state to still be `CopyToLog` and add extra constraints on the states in the next
`CopyToLog`.

## Constraints

Define two auxiliary variables:

- `nbytes_written`: the number of bytes written to `TxLog`. It could be either `MAX_COPY_BYTES`
  or number of bytes left to copy.
- `nbytes_read`: the number of bytes read from tx table or memory. It's no more than
  `nbytes_written`. `nbytes_read` is smaller than `nbytes_written` when there's out-of-bound
  access to the src buffer.

1. State transition:
   - rw_counter
     - from memory: + nbytes_written + nbytes_read
2. Lookups: nbytes_read + nbytes_written
   - from memory:
     - `nbytes_read` lookups from rw table (memory read)
     - `nbytes_written` lookups from rw table (TxLog write)

## Exceptions

No exceptions for `CopyToLog` as it's an internal state.

## Code

Please refer to `src/zkevm_specs/evm/execution/copy_to_log.py`.

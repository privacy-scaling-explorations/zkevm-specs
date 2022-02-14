# CopyToMemory

## Circuit behaviour

`CopyToMemory` is an internal execution state and doesn't correspond to a EVM opcode. It can copy
data from either tx or memory to memory. This gadget needs to loop itself if it hasn't finished
the copy.

The `CopyToMemory` circuit uses another gadget `BufferReaderGadget` to check if the access is out of
bound and needs 0 padding. The `BufferReaderGadget` couples every bytes accessed with `selectors`
that indicate whether a byte has value, and `bound_dist` that is defined as
`max(0, addr_end - addr)`. When `bound_dist[i] == 0`, it indicates that the buffer access at index
`i` is out of bound and therefore needs to pad 0. For `bound_dist[0]`, we need to constrain the
value using `min` gadget. But we only need to limit on the difference between two consecutive
`bound_dist` values for the rest of `bound_dist` array as we know its value decreases by 1 each
time until 0.

In the `CopyToMemory` circuit, it needs to lookup the bytes that is read from the buffer according
to `BufferReaderGadget` in the tx context table or memory table depending whether the src buffer
is from tx or memory. Last, it needs to check if the copy is finished. If not, it constrains the
next execution state to still be `CopyToMemory` and add extra constraints on the states in the next
`CopyToMemory`.

## Constraints

Define two auxiliary variables:
- `nbytes_written`: the number of bytes written to the memory. It could be either `MAX_COPY_BYTES`
    or number of bytes left to copy.
- `nbytes_read`: the number of bytes read from tx table or memory. It's no more than
    `nbytes_written`. `nbytes_read` is smaller than `nbytes_written` when there's out-of-bound
    access to the src buffer.

1. State transition:
   - rw_counter
        - from tx: + nbytes_written
        - from memory: + nbytes_written + nbytes_read
3. Lookups: nbytes_read + nbytes_written
   - from tx:
        - `nbytes_read` lookups from tx context table
        - `nbytes_written` lookups from rw table (memory write)
   - from memory:
        - `nbytes_read` lookups from rw table (memory read)
        - `nbytes_written` lookups from rw table (memory write)

## Exceptions

No exceptions for `CopyToMemory` as it's an internal state.

## Code

Please refer to `src/zkevm_specs/evm/execution/memory_copy.py`.

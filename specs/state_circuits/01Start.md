# Start

## Procedure

The `Start` checks the value to refund to the transaction sender.

### Circuit behavior

0. `field_tag`, `address` and `id`, `storage_key` are 0
1. `rw counter` is increased if it's not first row
2. `value` is 0
3. `initial value` is 0
4. `state root` is not changed if it's not first row

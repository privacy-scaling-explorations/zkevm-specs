# Copy Proof

The copy proof checks the values in the copy table and applies the lookup arguments to the corresponding tables to check if the value read from and write to data source is correct.
It also checks the padding behavior that the value read from an out-of-boundary address is 0.

## Circuit Layout

First, copy circuit contains 14 columns from the [copy table](./tables.md#copytable) with the same witness assignment.
Every two rows in the copy circuit represent a copy step where the first row is a read operation and the second is a write operation.
A copy event consists of multiple copy steps, which the first row in the copy event has `is_first` assigned to 1 and the last row has `is_last` assigned to 1.

In addition to the columns in the copy table, copy circuit adds a few auxiliary columns to help check the constraints.

- `is_memory`: indicates if `Type` is `Memory` using `IsZero` gadget.
- `is_bytecode`: indicates if `Type` is `Bytecode` using `IsZero` gadget.
- `is_tx_calldata`: indicates if `Type` is `TxCalldata` using `IsZero` gadget.
- `is_tx_log`: indicates if `Type` is `TxLog` using `IsZero` gadget.

## Circuit Constraints

The constraints are divided into three groups.

First, the circuit adds common constraints that applied to every rows in the circuit:

- Boolean check for `is_first`, and `is_last`
- Check `is_first == 0` when `q_step == 0`
- Check `is_last == 0` when `q_step == 1`
- Construct the IsZero gadget and constrain `is_memory`, `is_bytecode`, `is_tx_calldata`, and `is_tx_log`.
- The transition constraints from a copy step to the next step (with 2-row rotation), applied to all rows except the last two rows (the last step) in a copy event:
    - `Id`, `LogId`, `Type`, `AddressEnd` should be same between two steps.
    - `Address` increase by 1 in the next copy step.
- The transition constraints for `RwCounter` and `RwcIncreaseLeft` column
    - define `rw_diff` to be 1 if the `Type` is `Memory` or `TxLog` and `Padding` is 0 in the current row; otherwise 0.
    - when it's not the last row in a copy event (`is_last == 0`), `RwCounter` increases by `rw_diff` and `RwcIncreaseLeft` decrases by `rw_diff`.
    - when it's the last row in a copy event (`is_last == 1`), `RwcIncreaseLeft` is equal to `rw_diff`.

Second, the circuit adds the constraints for every copy step in the circuit, when `q_step` is 1.

- Look up the copy type pair `(Type, Type[1])` in a fixed table to make sure it's a valid copy step.
- Constrain the transition for `BytesLeft`
    - when it's not the last step (`is_last[1] != 1`), increase by 1 in the next step
    - otherwise, equals to 1.
- Constrain the write value equals to read value: `Value[1] == Value`
- Constrain `Value == 0` when `Padding == 1`.
- Construct the LT gadget to compare `Address` and `AddressEnd` in the read operation. If `Address >= AddressEnd`, constrain `Padding == 1`
- Constrain `Padding[1] == 0` as the write operation is never padded.

Third, the circuit adds the lookup arguments to the corresponding tables.

- When `Type` is `Memory` or `is_memory == 1` and `Padding == 0`, look up the `Value` to `rw_table` with `Memory` tag.
- When `Type` is `TxCalldata` or `is_tx_calldata == 1` and `Padding == 0`, look up the `Value` to `tx_table`.
- When `Type` is `Bytecode` or `is_bytecode == 1` and `Padding == 0`, look up the `Value` and `IsCode` to `bytecode_table`
- When `Type` is `TxLog` or `is_tx_log == 1`, look up the `Value` to `rw_table` with `TxLog` tag.

## Code

Please refer to `src/zkevm-specs/copy_circuit.py`

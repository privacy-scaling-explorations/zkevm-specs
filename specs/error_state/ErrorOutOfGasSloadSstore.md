# ErrorOutOfGasSloadSstore state for both SLOAD and SSTORE OOG errors

## Procedure

Handle the corresponding out of gas errors for both `SLOAD` and `SSTORE` opcodes.

### EVM behavior

For the current `go-ethereum` code, the out of gas error may occur for `constant gas` or `dynamic gas`.

#### SLOAD gas cost

For this gadget, SLOAD gas cost is calculated with EIP-2929 as:
```
if is_warm_access:
  gas_cost = GAS_COST_WARM_ACCESS # 100
else:
  gas_cost = COLD_SLOAD_COST # 2100
```

#### SSTORE gas cost

For this gadget, SSTORE gas cost is calculated with EIP-3529 as:
```
if value == value_prev:
  gas_cost = SLOAD_GAS # 100
else:
  if value_prev == original_value:
    if original_value == 0:
      gas_cost = SSTORE_SET_GAS # 20000
    else:
      gas_cost = SSTORE_RESET_GAS # 2900
  else:
    gas_cost = SLOAD_GAS # 100

if not is_warm_access:
  gas_cost += COLD_SLOAD_COST # 2100
```

#### SSTORE reentrancy sentry

For SSTORE, the OOG error occurs when the gas left is less than or equal to `SSTORE_SENTRY` (2300).

### Constraints

1. For SLOAD, constrain `gas_left < gas_cost`.
2. For SSTORE, constrain `gas_left < gas_cost` or `gas_left <= SSTORE_SENTRY`.
3. Only for SSTORE, constrain `is_static == false`.
4. Current call must fail.
5. If it's a root call, it transits to `EndTx`.
6. If it isn't a root call, it restores caller's context by reading to `rw_table`, then does step state transition to it.
7. Constrain `rw_counter_end_of_reversion = rw_counter_end_of_step + reversible_counter`.

### Lookups

7 bus-mapping lookups for SLOAD and 9 for SSTORE:

1. 5 call context lookups for `tx_id`, `is_static`, `callee_address`, `is_success` and `rw_counter_end_of_reversion`.
2. 1 stack read for `storage_key`.
3. 1 account storage access list read.
4. Only for SSTORE, 1 stack read for `value_to_store`.
5. Only for SSTORE, 1 account storage read.

## Code

Please refer to `src/zkevm_specs/evm/execution/error_oog_sload_sstore.py`.
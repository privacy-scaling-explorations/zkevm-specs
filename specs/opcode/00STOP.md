# STOP opcode

## Procedure

### EVM behavior

The `STOP` opcode terminates the call, then:

1. If it's a root call, it ends the execution.
2. Otherwise, it restores caller's context and switch to it.

### Circuit behavior

The circuit first checks the `result` in call context is indeed success. Then:

1. If it's a root call, it transits to `EndTx`.
2. Otherwise, it restores caller's context by reading to `rw_table`, then does step state transition to it.

## Code

Please refer to `src/zkevm_specs/evm/execution/stop.py`.

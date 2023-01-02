# ErrorInvalidOpcode state

## Procedure

`ErrorInvalidOpcode` may occur when invoked via `CALL`, `CALLCODE`, `DELEGATECALL`, `STATICCALL`, `CREATE` and `CREATE2`.

### EVM behavior

1. If it's a root call, it ends the execution.
2. Otherwise, it restores caller's context and switch to it.

### Constraints

1. Current opcode must be invalid. It verifies invalid bytes in any condition of:
   - `opcode > 0x20 && opcode < 0x30`
   - `opcode > 0x48 && opcode < 0x50`
   - `opcode > 0xA4 && opcode < 0xF0`
   - one of `[0x0C, 0x0D, 0x0E, 0x0F, 0x1E, 0x1F, 0x5C, 0x5D, 0x5E, 0x5F, 0xF6, 0xF7, 0xF8, 0xF9, 0xFB, 0xFC, 0xFE]`
2. Current call must be failed.
3. If it's a root call, it transits to `EndTx`.
4. if it is not root call, it restores caller's context by reading to `rw_table`, then does step state transition to it.

### Lookups

- Call Context lookup `CallContextFieldTag.IsSuccess`.

## Code

Please refer to `src/zkevm_specs/evm/execution/error_invalid_opcode.py`.

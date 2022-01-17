import pytest

from zkevm_specs.evm import (
    Block,
    Bytecode,
    CallContextFieldTag,
    ExecutionState,
    StepState,
    Opcode,
    RW,
    RWTableTag,
    Tables,
    Transaction,
    verify_steps,
)
from zkevm_specs.util import hex_to_word, RLCStore

# Start with different values for `gas` before calling the `GAS` opcode.
TESTING_DATA = tuple([i for i in range(2, 10)])


@pytest.mark.parametrize("gas", TESTING_DATA)
def test_gas(gas: int):
    rlc_store = RLCStore()

    tx = Transaction(gas=gas)

    block = Block()
    bytecode = Bytecode(f"{Opcode.GAS.hex()}00")
    bytecode_hash = rlc_store.to_rlc(bytecode.hash, 32)

    # since the GAS opcode returns the value of available gas after deducting the cost
    # of calling the GAS opcode itself, we should expect gas_left = gas - 2
    gas_left = gas - 2

    tables = Tables(
        block_table=set(block.table_assignments(rlc_store)),
        tx_table=set(tx.table_assignments(rlc_store)),
        bytecode_table=set(bytecode.table_assignments(rlc_store)),
        rw_table=set(
            [
                (3, RW.Read, RWTableTag.CallContext, 1, CallContextFieldTag.TxId, 1, 0, 0),
                (2, RW.Write, RWTableTag.Stack, 1, 1023, gas_left, 0, 0),
            ]
        ),
    )

    verify_steps(
        rlc_store=rlc_store,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.GAS,
                rw_counter=2,
                call_id=1,
                is_root=True,
                is_create=False,
                opcode_source=bytecode_hash,
                program_counter=0,
                stack_pointer=1024,
                gas_left=gas,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=3,
                call_id=1,
                is_root=True,
                is_create=False,
                opcode_source=bytecode_hash,
                program_counter=1,
                stack_pointer=1023,
                gas_left=gas_left,
            ),
        ],
    )

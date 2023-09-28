import pytest

from zkevm_specs.evm_circuit import (
    Block,
    Bytecode,
    ExecutionState,
    StepState,
    Tables,
    Transaction,
    verify_steps,
    RWDictionary,
)
from zkevm_specs.util import Word
from common import rand_range

# Start with different values for `gas` before calling the `GAS` opcode.
TESTING_DATA = tuple([i for i in range(2, 10)] + [rand_range(2**64) for i in range(0, 10)])


@pytest.mark.parametrize("gas", TESTING_DATA)
def test_gas(gas: int):
    tx = Transaction()

    bytecode = Bytecode().gas().stop()
    bytecode_hash = Word(bytecode.hash())

    # since the GAS opcode returns the value of available gas after deducting the cost
    # of calling the GAS opcode itself, we should expect gas_left = gas - 2
    gas_left = gas - 2

    tables = Tables(
        block_table=set(Block().table_assignments()),
        tx_table=set(tx.table_assignments()),
        withdrawal_table=set(),
        bytecode_table=set(bytecode.table_assignments()),
        rw_table=set(RWDictionary(2).stack_write(1, 1023, Word(gas_left)).rws),
    )

    verify_steps(
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.GAS,
                rw_counter=2,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
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
                code_hash=bytecode_hash,
                program_counter=1,
                stack_pointer=1023,
                gas_left=gas_left,
            ),
        ],
    )

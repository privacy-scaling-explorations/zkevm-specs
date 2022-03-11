import pytest

from zkevm_specs.evm import (
    Block,
    Bytecode,
    ExecutionState,
    StepState,
    Tables,
    Transaction,
    verify_steps,
    RWDictionary,
)
from zkevm_specs.util import rand_fq, rand_range, RLC

# Start with different values for `gas` before calling the `GAS` opcode.
TESTING_DATA = tuple([i for i in range(2, 10)] + [rand_range(2**64) for i in range(0, 10)])


@pytest.mark.parametrize("gas", TESTING_DATA)
def test_gas(gas: int):
    randomness = rand_fq()

    tx = Transaction()

    bytecode = Bytecode().gas().stop()
    bytecode_hash = RLC(bytecode.hash(), randomness)

    # since the GAS opcode returns the value of available gas after deducting the cost
    # of calling the GAS opcode itself, we should expect gas_left = gas - 2
    gas_left = gas - 2

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(tx.table_assignments(randomness)),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(RWDictionary(2).stack_write(1, 1023, RLC(gas_left, randomness)).rws),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.GAS,
                rw_counter=2,
                call_id=1,
                is_root=True,
                is_create=False,
                code_source=bytecode_hash,
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
                code_source=bytecode_hash,
                program_counter=1,
                stack_pointer=1023,
                gas_left=gas_left,
            ),
        ],
    )

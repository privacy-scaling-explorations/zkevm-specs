import pytest

from zkevm_specs.evm import (
    Bytecode,
    CallContextFieldTag,
    ExecutionState,
    StepState,
    RW,
    RWTableTag,
    Tables,
    Transaction,
    verify_steps,
)
from zkevm_specs.util import rand_fp, rand_address, RLC
from zkevm_specs.util.typing import U256
from zkevm_specs.util.param import N_BYTES_ACCOUNT_ADDRESS

TESTING_DATA = (
    0x00,
    0x10,
    0x302010,
    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
    rand_address(),
)


@pytest.mark.parametrize("origin", TESTING_DATA)
def test_origin(origin: U256):
    randomness = rand_fp()

    tx = Transaction(caller_address=origin)

    bytecode = Bytecode().origin().stop()
    bytecode_hash = RLC(bytecode.hash(), randomness)

    tables = Tables(
        block_table=set(),
        tx_table=set(tx.table_assignments(randomness)),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(
            [
                (
                    9,
                    RW.Read,
                    RWTableTag.CallContext,
                    1,
                    CallContextFieldTag.TxId,
                    0,
                    tx.id,
                    0,
                    0,
                    0,
                ),
                (
                    10,
                    RW.Write,
                    RWTableTag.Stack,
                    1,
                    1023,
                    0,
                    RLC(origin, randomness, N_BYTES_ACCOUNT_ADDRESS),
                    0,
                    0,
                    0,
                ),
            ]
        ),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.ORIGIN,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                code_source=bytecode_hash,
                program_counter=0,
                stack_pointer=1024,
                gas_left=2,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=11,
                call_id=1,
                is_root=True,
                is_create=False,
                code_source=bytecode_hash,
                program_counter=1,
                stack_pointer=1023,
                gas_left=0,
            ),
        ],
    )

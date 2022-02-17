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
from zkevm_specs.util import rand_fp, rand_range, RLC
from zkevm_specs.util.typing import U256

TESTING_DATA = (
    0x00,
    0x10,
    0x302010,
    0xF0FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF0F,
)


@pytest.mark.parametrize("gasprice", TESTING_DATA)
def test_gasprice(gasprice: U256):
    randomness = rand_fp()

    tx = Transaction(gas_price=gasprice)

    bytecode = Bytecode().gasprice().stop()
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
                    RLC(gasprice, randomness).value,
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
                execution_state=ExecutionState.GASPRICE,
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

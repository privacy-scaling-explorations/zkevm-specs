import pytest

from zkevm_specs.evm import (
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    RWTableTag,
    RW,
    Block,
    Bytecode,
    CallContextFieldTag,
    AccountFieldTag,
)
from zkevm_specs.util import rand_address, rand_word, rand_fp, RLC, U256, U160

TESTING_DATA = [(0, 0), (0, 10), (rand_address(), rand_word())]


@pytest.mark.parametrize("callee_address, balance", TESTING_DATA)
def test_selfbalance(callee_address: U160, balance: U256):
    randomness = rand_fp()

    bytecode = Bytecode().selfbalance()
    bytecode_hash = RLC(bytecode.hash(), randomness)

    rlc_balance = RLC(balance, randomness)

    tables = Tables(
        block_table=Block(),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(
            [
                # fmt: off
                (9, RW.Read, RWTableTag.CallContext, 1, CallContextFieldTag.CalleeAddress, 0, callee_address, 0, 0, 0),
                (10, RW.Read, RWTableTag.Account, callee_address, AccountFieldTag.Balance, 0, rlc_balance, rlc_balance, 0, 0, 0),
                (11, RW.Write, RWTableTag.Stack, 1, 1023, 0, rlc_balance, 0, 0, 0),
                # fmt: on
            ]
        ),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.SELFBALANCE,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                code_source=bytecode_hash,
                program_counter=0,
                stack_pointer=1024,
                gas_left=5,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=12,
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

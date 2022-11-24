import pytest

from zkevm_specs.evm import (
    ExecutionState,
    StepState,
    Opcode,
    verify_steps,
    Tables,
    Block,
    Bytecode,
    RWDictionary,
    CallContextFieldTag,
    AccountFieldTag,
)
from zkevm_specs.util import rand_fq, RLC
from itertools import chain
from collections import namedtuple


TESTING_DATA = (
    # balance | transfer value
    (200, 250),
    (1, 2),
)


@pytest.mark.parametrize("balance, transfer_value", TESTING_DATA)
def test_insufficient_balance(balance: int, transfer_value: int):
    randomness = rand_fq()

    block = Block()
    bytecode = Bytecode().call(0, 0xFC, transfer_value, 0, 0, 0, 0).stop()
    bytecode_hash = RLC(bytecode.hash(), randomness)

    tables = Tables(
        block_table=set(block.table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(
            RWDictionary(9)
            .stack_read(1, 1010, RLC(10000, randomness))  # gas
            .stack_read(1, 1011, RLC(0xFC, randomness))  # address
            .stack_read(1, 1012, RLC(transfer_value, randomness))  # value
            .stack_read(1, 1013, RLC(0, randomness))
            .stack_read(1, 1014, RLC(10, randomness))
            .stack_read(1, 1015, RLC(0, randomness))
            .stack_read(1, 1016, RLC(0, randomness))
            .stack_write(1, 1016, RLC(0, randomness))
            .call_context_read(1, CallContextFieldTag.CalleeAddress, 0xFE)
            .account_read(0xFE, AccountFieldTag.Balance, RLC(balance, randomness))
            .rws
        ),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.ErrorInsufficientBalance,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=231,
                stack_pointer=1010,
                gas_left=8,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                program_counter=232,
                rw_counter=19,
                call_id=1,
                stack_pointer=1016,
                gas_left=0,
            ),
        ],
    )


CallContext = namedtuple(
    "CallContext",
    [
        "is_root",
        "is_create",
        "program_counter",
        "stack_pointer",
        "gas_left",
        "memory_size",
        "reversible_write_counter",
    ],
    defaults=[True, False, 232, 1023, 10, 0, 0],
)

TESTING_DATA_NOT_ROOT = ((CallContext(), 100, 101),)

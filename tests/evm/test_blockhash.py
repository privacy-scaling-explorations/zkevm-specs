import pytest

from zkevm_specs.evm_circuit import (
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    Block,
    Bytecode,
    RWDictionary,
)
from zkevm_specs.util import rand_fq, RLC, U64, U256, Sequence, keccak256

TESTING_DATA = [
    # valid range
    (3, [keccak256(bytes(i)) for i in range(3)], 1, True),
    (261, [keccak256(bytes(i)) for i in range(5, 261)], 260, True),
    # invalid range
    (3, [keccak256(bytes(i)) for i in range(3)], 4, False),
    (258, [keccak256(bytes(i)) for i in range(256)], 1, False),
]


@pytest.mark.parametrize("current_number, history_hashes, block_number, is_valid", TESTING_DATA)
def test_blockhash(
    current_number: U64, history_hashes: Sequence[U256], block_number: U64, is_valid: bool
):
    block = Block(number=current_number, history_hashes=history_hashes)
    randomness = rand_fq()
    bytecode = Bytecode().blockhash()

    bytecode_hash = RLC(bytecode.hash(), randomness)

    result = keccak256(bytes(block_number)) if is_valid else 0

    call_id = 1
    rw_table = set(
        RWDictionary(8)
        .stack_read(call_id, 1023, RLC(block_number, randomness))
        .stack_write(call_id, 1023, RLC(result, randomness))
        .rws
    )

    tables = Tables(
        block_table=set(block.table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=rw_table,
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.BLOCKHASH,
                rw_counter=8,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=0,
                stack_pointer=1023,
                gas_left=20,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=10,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=1,
                stack_pointer=1023,
                gas_left=0,
            ),
        ],
    )

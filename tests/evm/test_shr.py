import pytest

from zkevm_specs.evm import (
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    Block,
    Bytecode,
    RWDictionary,
)
from zkevm_specs.util import (
    rand_fq,
    rand_range,
    rand_word,
    RLC,
    U256,
)


TESTING_DATA = (
    (0xABCD, 8),
    (0x1234, 7),
    (0x8765, 17),
    (0x4321, 0),
    (0xFFFF, 256),
    ((1 << 256) - 1, 63),
    ((1 << 256) - 1, 128),
    ((1 << 256) - 1, 129),
)


@pytest.mark.parametrize("value, shift", TESTING_DATA)
def test_shr(value: U256, shift: int):
    result = value >> shift if shift <= 255 else 0

    randomness = rand_fq()
    value = RLC(value, randomness)
    shift = RLC(shift, randomness)
    result = RLC(result, randomness)

    bytecode = Bytecode().push32(value).push32(shift).shr().stop()
    bytecode_hash = RLC(bytecode.hash(), randomness)

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(
            RWDictionary(9)
            .stack_read(1, 1022, value)
            .stack_read(1, 1023, shift)
            .stack_write(1, 1023, result)
            .rws
        ),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.SHR,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                code_source=bytecode_hash,
                program_counter=66,
                stack_pointer=1022,
                gas_left=3,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=11,
                call_id=1,
                is_root=True,
                is_create=False,
                code_source=bytecode_hash,
                program_counter=67,
                stack_pointer=1023,
                gas_left=0,
            ),
        ],
    )

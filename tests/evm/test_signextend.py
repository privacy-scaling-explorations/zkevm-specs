import pytest
import random
from common import rand_word
from zkevm_specs.evm_circuit import (
    Bytecode,
    ExecutionState,
    StepState,
    Tables,
    verify_steps,
    RWDictionary,
)
from zkevm_specs.util import Word, U256


def generate_tests_data():
    test_data = []
    for _ in range(32):
        byte_num = random.randint(0, 32)
        value = rand_word()
        if byte_num > 31:
            test_data.append((byte_num, value, value))
        else:
            value_bytes = value.to_bytes(32, "big")
            value_bytes = value_bytes[31 - int(byte_num) :]
            sign_bit = value_bytes[0] >> 7
            if sign_bit == 0:
                test_data.append((byte_num, value, int.from_bytes(value_bytes, "big")))
            else:
                num_bytes_prepend = 32 - (byte_num + 1)
                result = int.from_bytes(bytearray([0xFF] * num_bytes_prepend) + value_bytes, "big")
                test_data.append((byte_num, value, result))
    return test_data


@pytest.mark.parametrize("b, x, y", generate_tests_data())
def test_pop(b: U256, x: U256, y: U256):
    bytecode = Bytecode().signextend(b, x).stop()
    bytecode_hash = Word(bytecode.hash())

    tables = Tables(
        block_table=set(),
        tx_table=set(),
        withdrawal_table=set(),
        bytecode_table=set(bytecode.table_assignments()),
        rw_table=set(
            RWDictionary(1)
            .stack_read(1, 1022, Word(b))
            .stack_read(1, 1023, Word(x))
            .stack_write(1, 1023, Word(y))
            .rws
        ),
    )

    verify_steps(
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.SIGNEXTEND,
                rw_counter=1,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=66,
                stack_pointer=1022,
                gas_left=5,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=4,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=67,
                stack_pointer=1023,
                gas_left=0,
            ),
        ],
    )

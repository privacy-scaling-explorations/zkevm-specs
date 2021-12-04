import pytest

from zkevm_specs.evm import (
    ExecutionState,
    StepState,
    Opcode,
    verify_steps,
    Tables,
    RWTableTag,
    RW,
    Block,
    Bytecode,
)
from zkevm_specs.util import rand_bytes, RLCStore


TESTING_DATA = tuple(
    [
        (Opcode.PUSH1, bytes([1])),
        (Opcode.PUSH2, bytes([2, 1])),
        (Opcode.PUSH31, bytes([i for i in range(31, 0, -1)])),
        (Opcode.PUSH32, bytes([i for i in range(32, 0, -1)])),
    ]
    + [(Opcode(Opcode.PUSH1 + i), rand_bytes(i + 1)) for i in range(32)]
)


@pytest.mark.parametrize("opcode, value_be_bytes", TESTING_DATA)
def test_push(opcode: Opcode, value_be_bytes: bytes):
    rlc_store = RLCStore()

    value = rlc_store.to_rlc(bytes(reversed(value_be_bytes)))

    bytecode = Bytecode(f"{opcode.hex()}{value_be_bytes.hex()}00")
    bytecode_hash = rlc_store.to_rlc(bytecode.hash, 32)

    tables = Tables(
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(rlc_store)),
        rw_table=set(
            [
                (8, RW.Write, RWTableTag.Stack, 1, 1023, value, 0, 0),
            ]
        ),
    )

    verify_steps(
        rlc_store=rlc_store,
        block=Block(),
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.PUSH,
                rw_counter=8,
                call_id=1,
                is_root=True,
                is_create=False,
                opcode_source=bytecode_hash,
                program_counter=0,
                stack_pointer=1024,
                gas_left=3,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                opcode_source=bytecode_hash,
                program_counter=1 + len(value_be_bytes),
                stack_pointer=1023,
                gas_left=0,
            ),
        ],
    )

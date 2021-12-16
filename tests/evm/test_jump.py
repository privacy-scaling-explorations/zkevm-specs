import pytest

from typing import Optional
from zkevm_specs.evm import (
    ExecutionState,
    StepState,
    Opcode,
    verify_steps,
    Tables,
    RWTableTag,
    RW,
    Bytecode,
)
from zkevm_specs.util import hex_to_word, rand_bytes, RLCStore


TESTING_DATA = (
    (Opcode.JUMP, bytes([7])),
)


@pytest.mark.parametrize("opcode, dest_bytes", TESTING_DATA)
def test_jump(opcode: Opcode, dest_bytes: bytes):
    rlc_store = RLCStore()
    # dest = rlc_store.to_rlc(dest_bytes)
    dest = rlc_store.to_rlc(bytes(reversed(dest_bytes)))

    # dest_bytes = instruction.rlc_to_bytes(dest, 32)

    # print(dest)
    # Jumps to PC=7
    # PUSH1 80 PUSH1 40 PUSH1 07 JUMP JUMPDEST STOP
    bytecode = Bytecode(f"6080604060{dest_bytes.hex()}565b00")
    bytecode_hash = rlc_store.to_rlc(bytecode.hash, 32)

    tables = Tables(
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(rlc_store)),
        rw_table=set(
            [
                (9, RW.Read, RWTableTag.Stack, 1, 1021, dest, 0, 0),
            ]
        ),
    )

    verify_steps(
        rlc_store=rlc_store,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.JUMP,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                opcode_source=bytecode_hash,
                program_counter=6,
                stack_pointer=1021,
                gas_left=8,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=10,
                call_id=1,
                is_root=True,
                is_create=False,
                opcode_source=bytecode_hash,
                program_counter=int.from_bytes(dest_bytes, "little"),
                stack_pointer=1022,
                gas_left=0,
            ),
        ],
    )

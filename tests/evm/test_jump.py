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
from zkevm_specs.util import rand_fp, RLC


TESTING_DATA = ((Opcode.JUMP, bytes([7])),)


@pytest.mark.parametrize("opcode, dest_bytes", TESTING_DATA)
def test_jump(opcode: Opcode, dest_bytes: bytes):
    randomness = rand_fp()
    dest = RLC(bytes(reversed(dest_bytes)), randomness)

    block = Block()
    # Jumps to PC=7
    # PUSH1 80 PUSH1 40 PUSH1 07 JUMP JUMPDEST STOP
    bytecode = Bytecode().push1(0x80).push1(0x40).push1(dest_bytes).jump().jumpdest().stop()
    bytecode_hash = RLC(bytecode.hash(), randomness)

    tables = Tables(
        block_table=set(block.table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(
            [
                (9, RW.Read, RWTableTag.Stack, 1, 1021, 0, dest, 0, 0, 0),
            ]
        ),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.JUMP,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                code_source=bytecode_hash,
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
                code_source=bytecode_hash,
                program_counter=int.from_bytes(dest_bytes, "little"),
                stack_pointer=1022,
                gas_left=0,
            ),
        ],
    )

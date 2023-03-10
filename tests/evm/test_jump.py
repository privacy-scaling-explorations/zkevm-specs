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
)
from zkevm_specs.util import Word


TESTING_DATA = ((Opcode.JUMP, 7),)


@pytest.mark.parametrize("opcode, dest", TESTING_DATA)
def test_jump(opcode: Opcode, dest: int):
    dest_bytes = dest.to_bytes(1, "little")
    block = Block()
    # Jumps to PC=7
    # PUSH1 80 PUSH1 40 PUSH1 07 JUMP JUMPDEST STOP
    bytecode = Bytecode().push1(0x80).push1(0x40).push1(dest_bytes).jump().jumpdest().stop()
    bytecode_hash = Word(bytecode.hash())

    tables = Tables(
        block_table=set(block.table_assignments()),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments()),
        rw_table=set(RWDictionary(9).stack_read(1, 1021, Word(dest)).rws),
    )

    verify_steps(
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.JUMP,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
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
                code_hash=bytecode_hash,
                program_counter=int.from_bytes(dest_bytes, "little"),
                stack_pointer=1022,
                gas_left=0,
            ),
        ],
    )

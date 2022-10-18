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
)
from zkevm_specs.util import rand_fq, RLC


TESTING_DATA = ((Opcode.JUMP, bytes([5])),)


@pytest.mark.parametrize("opcode, dest_bytes", TESTING_DATA)
def test_invalid_jump_root(opcode: Opcode, dest_bytes: bytes):
    randomness = rand_fq()
    dest = RLC(bytes(reversed(dest_bytes)), randomness)

    block = Block()
    # dest is invalid for error case
    # PUSH1 80 PUSH1 40 PUSH1 07 JUMP JUMPDEST STOP
    bytecode = Bytecode().push1(0x80).push1(0x40).push1(dest_bytes).jump().jumpdest().stop()
    bytecode_hash = RLC(bytecode.hash(), randomness)

    tables = Tables(
        block_table=set(block.table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(
            RWDictionary(9)
            .stack_read(1, 1021, dest)
            .call_context_read(1, CallContextFieldTag.IsSuccess, 0)
            .rws
        ),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.ErrorInvalidJump,
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
                execution_state=ExecutionState.EndTx,
                rw_counter=11,
                call_id=1,
                gas_left=0,
            ),
        ],
    )

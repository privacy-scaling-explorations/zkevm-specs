import pytest

from zkevm_specs.evm_circuit import (
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


TESTING_DATA = ((Opcode.JUMPI, 40, 7),)


@pytest.mark.parametrize("opcode, cond, dest", TESTING_DATA)
def test_jumpi_cond_nonzero(opcode: Opcode, cond: int, dest: int):
    dest_bytes = dest.to_bytes(1, "little")

    block = Block()
    # Jumps to PC=7 because the condition (40) is nonzero.
    # PUSH1 80 PUSH1 40 PUSH1 07 JUMPI JUMPDEST STOP
    bytecode = Bytecode().push1(0x80).push1(0x40).push1(dest_bytes).jumpi().jumpdest().stop()
    bytecode_hash = Word(bytecode.hash())

    tables = Tables(
        block_table=set(block.table_assignments()),
        tx_table=set(),
        withdrawal_table=set(),
        bytecode_table=set(bytecode.table_assignments()),
        rw_table=set(
            RWDictionary(9).stack_read(1, 1021, Word(dest)).stack_read(1, 1022, Word(cond)).rws
        ),
    )

    verify_steps(
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.JUMPI,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=6,
                stack_pointer=1021,
                gas_left=10,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=11,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=int.from_bytes(dest_bytes, "little"),
                stack_pointer=1023,
                gas_left=0,
            ),
        ],
    )


TESTING_DATA_ZERO_COND = ((Opcode.JUMPI, 0, 8),)


@pytest.mark.parametrize("opcode, cond, dest", TESTING_DATA_ZERO_COND)
def test_jumpi_cond_zero(opcode: Opcode, cond: int, dest: int):
    dest_bytes = dest.to_bytes(1, "little")
    cond_bytes = cond.to_bytes(1, "little")

    block = Block()
    # Jumps to PC=7 because the condition (0) is zero.
    # PUSH1 80 PUSH1 0 PUSH1 08 JUMPI STOP
    bytecode = Bytecode().push1(0x80).push1(cond_bytes).push1(dest_bytes).jumpi().stop()
    bytecode_hash = Word(bytecode.hash())

    tables = Tables(
        block_table=set(block.table_assignments()),
        tx_table=set(),
        withdrawal_table=set(),
        bytecode_table=set(bytecode.table_assignments()),
        rw_table=set(
            RWDictionary(9).stack_read(1, 1021, Word(dest)).stack_read(1, 1022, Word(cond)).rws
        ),
    )

    verify_steps(
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.JUMPI,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=6,
                stack_pointer=1021,
                gas_left=10,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=11,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=7,
                stack_pointer=1023,
                gas_left=0,
            ),
        ],
    )

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
from zkevm_specs.util import RLC
from common import rand_fq


TESTING_DATA = ((Opcode.JUMPI, bytes([40]), bytes([7])),)


@pytest.mark.parametrize("opcode, cond_bytes, dest_bytes", TESTING_DATA)
def test_jumpi_cond_nonzero(opcode: Opcode, cond_bytes: bytes, dest_bytes: bytes):
    randomness = rand_fq()
    cond = RLC(bytes(reversed(cond_bytes)), randomness)
    dest = RLC(bytes(reversed(dest_bytes)), randomness)

    block = Block()
    # Jumps to PC=7 because the condition (40) is nonzero.
    # PUSH1 80 PUSH1 40 PUSH1 07 JUMPI JUMPDEST STOP
    bytecode = Bytecode().push1(0x80).push1(0x40).push1(dest_bytes).jumpi().jumpdest().stop()
    bytecode_hash = RLC(bytecode.hash(), randomness)

    tables = Tables(
        block_table=set(block.table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(RWDictionary(9).stack_read(1, 1021, dest).stack_read(1, 1022, cond).rws),
    )

    verify_steps(
        randomness=randomness,
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


TESTING_DATA_ZERO_COND = ((Opcode.JUMPI, bytes([0]), bytes([8])),)


@pytest.mark.parametrize("opcode, cond_bytes, dest_bytes", TESTING_DATA_ZERO_COND)
def test_jumpi_cond_zero(opcode: Opcode, cond_bytes: bytes, dest_bytes: bytes):
    randomness = rand_fq()
    cond = RLC(bytes(reversed(cond_bytes)), randomness)
    dest = RLC(bytes(reversed(dest_bytes)), randomness)

    block = Block()
    # Jumps to PC=7 because the condition (0) is zero.
    # PUSH1 80 PUSH1 0 PUSH1 08 JUMPI STOP
    bytecode = Bytecode().push1(0x80).push1(cond_bytes).push1(dest_bytes).jumpi().stop()
    bytecode_hash = RLC(bytecode.hash(), randomness)

    tables = Tables(
        block_table=set(block.table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(RWDictionary(9).stack_read(1, 1021, dest).stack_read(1, 1022, cond).rws),
    )

    verify_steps(
        randomness=randomness,
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

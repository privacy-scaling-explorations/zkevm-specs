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
    Block,
    Bytecode,
)
from zkevm_specs.util import hex_to_word, rand_bytes, RLCStore


TESTING_DATA = ((Opcode.JUMPI, bytes([40]), bytes([7])),)


@pytest.mark.parametrize("opcode, cond_bytes, dest_bytes", TESTING_DATA)
def test_jumpi_cond_nonzero(opcode: Opcode, cond_bytes: bytes, dest_bytes: bytes):
    rlc_store = RLCStore()
    cond = rlc_store.to_rlc(bytes(reversed(cond_bytes)))
    dest = rlc_store.to_rlc(bytes(reversed(dest_bytes)))

    block = Block()
    # Jumps to PC=7 because the condition (40) is nonzero.
    # PUSH1 80 PUSH1 40 PUSH1 07 JUMPI JUMPDEST STOP
    bytecode = Bytecode(f"6080604060{dest_bytes.hex()}575b00")
    bytecode_hash = rlc_store.to_rlc(bytecode.hash, 32)

    tables = Tables(
        block_table=set(block.table_assignments(rlc_store)),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(rlc_store)),
        rw_table=set(
            [
                (9, RW.Read, RWTableTag.Stack, 1, 1021, 0, dest, 0, 0, 0),
                (10, RW.Read, RWTableTag.Stack, 1, 1022, 0, cond, 0, 0, 0),
            ],
        ),
    )

    verify_steps(
        rlc_store=rlc_store,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.JUMPI,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                opcode_source=bytecode_hash,
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
                opcode_source=bytecode_hash,
                program_counter=int.from_bytes(dest_bytes, "little"),
                stack_pointer=1023,
                gas_left=0,
            ),
        ],
    )


TESTING_DATA_ZERO_COND = ((Opcode.JUMPI, bytes([0]), bytes([8])),)


@pytest.mark.parametrize("opcode, cond_bytes, dest_bytes", TESTING_DATA_ZERO_COND)
def test_jumpi_cond_zero(opcode: Opcode, cond_bytes: bytes, dest_bytes: bytes):
    rlc_store = RLCStore()
    cond = rlc_store.to_rlc(bytes(reversed(cond_bytes)))
    dest = rlc_store.to_rlc(bytes(reversed(dest_bytes)))

    block = Block()
    # Jumps to PC=7 because the condition (0) is zero.
    # PUSH1 80 PUSH1 0 PUSH1 08 JUMPI STOP
    bytecode = Bytecode(f"6080600060{dest_bytes.hex()}575b00")
    bytecode_hash = rlc_store.to_rlc(bytecode.hash, 32)

    tables = Tables(
        block_table=set(block.table_assignments(rlc_store)),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(rlc_store)),
        rw_table=set(
            [
                (9, RW.Read, RWTableTag.Stack, 1, 1021, 0, dest, 0, 0, 0),
                (10, RW.Read, RWTableTag.Stack, 1, 1022, 0, cond, 0, 0, 0),
            ],
        ),
    )

    verify_steps(
        rlc_store=rlc_store,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.JUMPI,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                opcode_source=bytecode_hash,
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
                opcode_source=bytecode_hash,
                program_counter=7,
                stack_pointer=1023,
                gas_left=0,
            ),
        ],
    )

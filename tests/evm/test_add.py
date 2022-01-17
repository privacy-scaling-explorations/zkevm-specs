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


TESTING_DATA = (
    (Opcode.ADD, hex_to_word("030201"), hex_to_word("060504"), hex_to_word("090705")),
    (Opcode.SUB, hex_to_word("090705"), hex_to_word("060504"), hex_to_word("030201")),
    (Opcode.ADD, rand_bytes(), rand_bytes(), None),
    (Opcode.SUB, rand_bytes(), rand_bytes(), None),
)


@pytest.mark.parametrize("opcode, a_bytes, b_bytes, c_bytes", TESTING_DATA)
def test_add(opcode: Opcode, a_bytes: bytes, b_bytes: bytes, c_bytes: Optional[bytes]):
    rlc_store = RLCStore()

    a = rlc_store.to_rlc(a_bytes)
    b = rlc_store.to_rlc(b_bytes)
    c = (
        rlc_store.to_rlc(c_bytes)
        if c_bytes is not None
        else (rlc_store.add(a, b) if opcode == Opcode.ADD else rlc_store.sub(a, b))[0]
    )

    block = Block()
    bytecode = Bytecode(f"7f{b_bytes.hex()}7f{a_bytes.hex()}{opcode.hex()}00")
    bytecode_hash = rlc_store.to_rlc(bytecode.hash, 32)

    tables = Tables(
        block_table=set(block.table_assignments(rlc_store)),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(rlc_store)),
        rw_table=set(
            [
                (9, RW.Read, RWTableTag.Stack, 1, 1022, 0, a, 0, 0, 0),
                (10, RW.Read, RWTableTag.Stack, 1, 1023, 0, b, 0, 0, 0),
                (11, RW.Write, RWTableTag.Stack, 1, 1023, 0, c, 0, 0, 0),
            ]
        ),
    )

    verify_steps(
        rlc_store=rlc_store,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.ADD,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                opcode_source=bytecode_hash,
                program_counter=66,
                stack_pointer=1022,
                gas_left=3,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=12,
                call_id=1,
                is_root=True,
                is_create=False,
                opcode_source=bytecode_hash,
                program_counter=67,
                stack_pointer=1023,
                gas_left=0,
            ),
        ],
    )

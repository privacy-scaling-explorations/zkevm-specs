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


TESTING_DATA = ((Opcode.COINBASE, hex_to_word("030201")),)


@pytest.mark.parametrize("opcode, address", TESTING_DATA)
def test_coinbase(opcode: Opcode, address: bytes):
    rlc_store = RLCStore()

    coinbase_address = rlc_store.to_rlc(address)

    bytecode = Bytecode(f"{opcode.hex()}00")
    bytecode_hash = rlc_store.to_rlc(bytecode.hash, 32)
    # block = Block(coinbase_address, int(15e6), 10, 0, 0, int(1e9), [])
    block = Block(coinbase_address)
    tables = Tables(
        block_table=set(block.table_assignments(rlc_store)),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(rlc_store)),
        rw_table=set(
            [
                (9, RW.Write, RWTableTag.Stack, 1, 1023, coinbase_address, 0, 0),
            ]
        ),
    )

    verify_steps(
        rlc_store=rlc_store,
        block=block,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.COINBASE,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                opcode_source=bytecode_hash,
                program_counter=0,
                stack_pointer=1024,
                gas_left=2,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=10,
                call_id=1,
                is_root=True,
                is_create=False,
                opcode_source=bytecode_hash,
                program_counter=1,
                stack_pointer=1023,
                gas_left=0,
            ),
        ],
    )

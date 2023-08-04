import pytest

from zkevm_specs.evm_circuit import (
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    CallContextFieldTag,
    Block,
    Bytecode,
    RWDictionary,
    Opcode,
    Transaction,
)
from zkevm_specs.util import Word
from zkevm_specs.util.param import MAX_INIT_CODE_SIZE


def gen_calldata(bytes_len: int) -> bytes:
    calldata = []
    calldata.extend([int(Opcode.PUSH32)] * bytes_len)
    assert len(calldata) == bytes_len
    return bytes(calldata)


TESTING_DATA_IS_ROOT = (
    # gas cost: 32000 + 60 (memory expansion) + (320/32) * 2 = 32080
    # CREATE2 has extra keccak gas cost = (320/32) * 6 = 60
    (Opcode.CREATE, 320, 320, 32079, False),
    (Opcode.CREATE2, 320, 320, 32139, False),
    # bytecode size exceeds MAX_INIT_CODE_SIZE
    (Opcode.CREATE, 0, MAX_INIT_CODE_SIZE + 1, int(5e6), False),
    (Opcode.CREATE2, 0, MAX_INIT_CODE_SIZE + 1, int(5e6), False),
    # hit insufficient gas and MAX_INIT_CODE_SIZE
    (Opcode.CREATE, 0, MAX_INIT_CODE_SIZE + 1, int(3e6), False),
    (Opcode.CREATE2, 0, MAX_INIT_CODE_SIZE + 1, int(3e6), False),
    ## Same cases, with is_root set to True
    # gas cost: 53000 + 320 * 16 + (320/32) * 2 = 58140
    (Opcode.CREATE, 320, 320, 58139, True),
    (Opcode.CREATE2, 320, 320, 58199, True),
    # To generate a size of (MAX_INIT_CODE_SIZE + 1) calldata would cause memory corrupted in the local env.
    # So, to make ci and local test works, we ignore the cases if overflowed calldata needed.
    # Those cases were verified by changing MAX_INIT_CODE_SIZE to a smaller number, like 320
    # (Opcode.CREATE, 0, MAX_INIT_CODE_SIZE + 1, int(5e6), True),
    # (Opcode.CREATE2, 0, MAX_INIT_CODE_SIZE + 1, int(5e6), True),
)


@pytest.mark.parametrize("opcode, offset, length, gas_left, is_root", TESTING_DATA_IS_ROOT)
def test_error_oog_create(opcode: Opcode, offset: int, length: int, gas_left: int, is_root: bool):
    reversible_write_counter = 2
    rw_counter = 14
    caller_id = 1 if is_root is True else 2
    is_create2 = opcode == Opcode.CREATE2
    if is_create2:
        bytecode = Bytecode().push32(1).push32(offset).push32(length).push32(123).create2()
        pc = 132
        stack_pointer = 1020
    else:
        bytecode = Bytecode().push32(1).push32(offset).push32(length).create()
        pc = 99
        stack_pointer = 1021
    rw_table = (
        RWDictionary(rw_counter)
        .stack_read(caller_id, stack_pointer + 1, Word(offset))
        .stack_read(caller_id, stack_pointer + 2, Word(length))
    )
    bytecode_hash = Word(bytecode.hash())

    rw_table.call_context_read(caller_id, CallContextFieldTag.IsRoot, is_root)
    if is_root is True:
        tx = Transaction(id=1, call_data=gen_calldata(length if length < MAX_INIT_CODE_SIZE else 1))
        rw_table.call_context_read(caller_id, CallContextFieldTag.TxId, 1)

    rw_table.call_context_read(caller_id, CallContextFieldTag.IsSuccess, 0)

    if is_root is False:
        # fmt: off
        rw_table \
            .call_context_read(caller_id, CallContextFieldTag.CallerId, 1) \
            .call_context_read(1, CallContextFieldTag.IsRoot, False) \
            .call_context_read(1, CallContextFieldTag.IsCreate, True) \
            .call_context_read(1, CallContextFieldTag.CodeHash, bytecode_hash) \
            .call_context_read(1, CallContextFieldTag.ProgramCounter, pc + 1) \
            .call_context_read(1, CallContextFieldTag.StackPointer, 1024) \
            .call_context_read(1, CallContextFieldTag.GasLeft, 0) \
            .call_context_read(1, CallContextFieldTag.MemorySize, 0) \
            .call_context_read(1, CallContextFieldTag.ReversibleWriteCounter, reversible_write_counter) \
            .call_context_write(1, CallContextFieldTag.LastCalleeId, 2) \
            .call_context_write(1, CallContextFieldTag.LastCalleeReturnDataOffset, 0) \
            .call_context_write(1, CallContextFieldTag.LastCalleeReturnDataLength, 0)
        # fmt: on

    tables = Tables(
        block_table=set(Block().table_assignments()),
        tx_table=set(tx.table_assignments()) if is_root is True else set(),
        bytecode_table=set(bytecode.table_assignments()),
        rw_table=set(rw_table.rws),
    )

    verify_steps(
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.ErrorOutOfGasCREATE2,
                rw_counter=rw_counter,
                call_id=caller_id,
                is_root=is_root,
                is_create=True,
                code_hash=bytecode_hash,
                program_counter=pc,
                stack_pointer=stack_pointer,
                gas_left=gas_left,
                reversible_write_counter=reversible_write_counter,
            ),
            StepState(
                execution_state=ExecutionState.EndTx,
                rw_counter=rw_table.rw_counter + reversible_write_counter,
                call_id=1,
            )
            if is_root is True
            else StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=rw_table.rw_counter + reversible_write_counter,
                call_id=1,
                is_root=is_root,
                is_create=True,
                code_hash=bytecode_hash,
                program_counter=pc + 1,
                stack_pointer=1024,
                gas_left=0,
                memory_word_size=0,
                reversible_write_counter=reversible_write_counter,
            ),
        ],
    )

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
)
from zkevm_specs.util import Word


TESTING_DATA_IS_ROOT = (
    # dynamic gas cost for 32 bytes offset and 32 bytes data size is 9
    # constant gas cost of the following opcodes is 3
    (False, False, Opcode.CALLDATACOPY, 32, 32, 11),
    (False, False, Opcode.CODECOPY, 32, 32, 11),
    (False, False, Opcode.RETURNDATACOPY, 32, 32, 11),
    # EXTCODECOPY
    # constant gas cost of EXTCODECOPY is either 100 (warm access) or 2600 (cold access)
    (False, False, Opcode.EXTCODECOPY, 32, 32, 2608),
    (False, True, Opcode.EXTCODECOPY, 32, 32, 108),
    (True, False, Opcode.EXTCODECOPY, 32, 32, 2608),
    (True, True, Opcode.EXTCODECOPY, 32, 32, 108),
)


@pytest.mark.parametrize(
    "is_root, is_warm_access, opcode, offset, length, gas_left", TESTING_DATA_IS_ROOT
)
def test_error_oog_memory_copy(
    is_root: bool, is_warm_access: bool, opcode: Opcode, offset: int, length: int, gas_left: int
):
    caller_id = 1 if is_root else 2
    is_ext_code_copy = True if opcode == Opcode.EXTCODECOPY else False

    # root call and warm/cold access only occurred while EXTCODECOPY
    if is_root or is_warm_access:
        assert is_ext_code_copy

    if is_ext_code_copy:
        rw_counter = 9 if is_root else 20
        address = 0xCAFECAFE
        bytecode = Bytecode().extcodecopy()
        rw_table = (
            RWDictionary(rw_counter)
            .stack_read(caller_id, 1020, Word(address))
            .stack_read(caller_id, 1021, Word(offset))
            .stack_read(caller_id, 1022, Word(0))
            .stack_read(caller_id, 1023, Word(length))
        )
        # fmt: off
        rw_table \
            .call_context_read(caller_id, CallContextFieldTag.TxId, caller_id) \
            .call_context_read(caller_id, CallContextFieldTag.RwCounterEndOfReversion, 1) \
            .call_context_read(caller_id, CallContextFieldTag.IsPersistent, False) \
            .tx_access_list_account_write(caller_id, address, True, is_warm_access, rw_counter_of_reversion=1)
        # fmt: on
        stack_pointer = 1020
        pc = 133
    else:
        rw_counter = 3
        if opcode == Opcode.CALLDATACOPY:
            bytecode = Bytecode().calldatacopy()
        elif opcode == Opcode.CODECOPY:
            bytecode = Bytecode().codecopy()
        else:
            bytecode = Bytecode().returndatacopy()

        rw_table = (
            RWDictionary(rw_counter)
            .stack_read(caller_id, 1021, Word(offset))
            .stack_read(caller_id, 1022, Word(0))
            .stack_read(caller_id, 1023, Word(length))
        )
        stack_pointer = 1021
        pc = 100

    bytecode_hash = Word(bytecode.hash())

    rw_table.call_context_read(caller_id, CallContextFieldTag.IsSuccess, 0)

    # fmt: off
    if not is_root:
        memory_word_size = (
            0 if length == 0 else (offset + length + 31) // 32
        )
        rw_table \
            .call_context_read(2, CallContextFieldTag.CallerId, 1) \
            .call_context_read(1, CallContextFieldTag.IsRoot, is_root) \
            .call_context_read(1, CallContextFieldTag.IsCreate, False) \
            .call_context_read(1, CallContextFieldTag.CodeHash, bytecode_hash) \
            .call_context_read(1, CallContextFieldTag.ProgramCounter, pc) \
            .call_context_read(1, CallContextFieldTag.StackPointer, stack_pointer) \
            .call_context_read(1, CallContextFieldTag.GasLeft, gas_left) \
            .call_context_read(1, CallContextFieldTag.MemorySize, memory_word_size) \
            .call_context_read(1, CallContextFieldTag.ReversibleWriteCounter, 0) \
            .call_context_write(1, CallContextFieldTag.LastCalleeId, 2) \
            .call_context_write(1, CallContextFieldTag.LastCalleeReturnDataOffset, 0) \
            .call_context_write(1, CallContextFieldTag.LastCalleeReturnDataLength, 0)
    # fmt: on

    tables = Tables(
        block_table=set(Block().table_assignments()),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments()),
        rw_table=set(rw_table.rws),
    )

    verify_steps(
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.ErrorOutOfGasMemoryCopy,
                rw_counter=rw_counter,
                call_id=caller_id,
                is_root=is_root,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=0,
                stack_pointer=stack_pointer,
                gas_left=gas_left,
                reversible_write_counter=0,
            ),
            StepState(
                execution_state=ExecutionState.EndTx,
                rw_counter=rw_table.rw_counter,
                call_id=1,
                gas_left=0,
            )
            if is_root is True
            else StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=rw_table.rw_counter,
                call_id=1,
                is_root=False,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=pc,
                stack_pointer=stack_pointer,
                gas_left=gas_left,
                memory_word_size=memory_word_size,
                reversible_write_counter=0,
            ),
        ],
    )

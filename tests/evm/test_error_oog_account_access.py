from itertools import product
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
)
from zkevm_specs.evm_circuit.opcode import Opcode
from zkevm_specs.util import Word
from zkevm_specs.util.param import GAS_COST_ACCOUNT_COLD_ACCESS, GAS_COST_WARM_ACCESS


def gen_testing_data():
    opcodes = [Opcode.BALANCE, Opcode.EXTCODESIZE, Opcode.EXTCODEHASH]
    is_warm = [True, False]
    is_root = [True, False]
    return [
        (opcode, is_warm, is_root)
        for opcode, is_warm, is_root in product(opcodes, is_warm, is_root)
    ]


TESTING_DATA = gen_testing_data()


@pytest.mark.parametrize("opcode, is_warm, is_root", TESTING_DATA)
def test_error_oog_account_access(opcode: Opcode, is_warm: bool, is_root: bool):
    address = 0xCAFECAFE
    if opcode == Opcode.BALANCE:
        bytecode = Bytecode().push32(address).balance().stop()
    elif opcode == Opcode.EXTCODESIZE:
        bytecode = Bytecode().push32(address).extcodesize().stop()
    else:
        bytecode = Bytecode().push32(address).extcodehash().stop()
    bytecode_hash = Word(bytecode.hash())

    gas_left = GAS_COST_WARM_ACCESS - 1 if is_warm else GAS_COST_ACCOUNT_COLD_ACCESS - 1

    tx_id = 1
    reversible_write_counter = 2
    current_call_id = 1 if is_root else 2
    rw_counter = 14
    pc = 33
    stack_pointer = 1023
    rw_table = RWDictionary(rw_counter).stack_read(current_call_id, stack_pointer, Word(address))
    rw_table.call_context_read(current_call_id, CallContextFieldTag.TxId, tx_id)
    rw_table.tx_access_list_account_read(tx_id, address, is_warm)

    rw_table.call_context_read(current_call_id, CallContextFieldTag.IsSuccess, 0)

    if not is_root:
        # fmt: off
        rw_table \
            .call_context_read(current_call_id, CallContextFieldTag.CallerId, 1) \
            .call_context_read(1, CallContextFieldTag.IsRoot, False) \
            .call_context_read(1, CallContextFieldTag.IsCreate, False) \
            .call_context_read(1, CallContextFieldTag.CodeHash, bytecode_hash) \
            .call_context_read(1, CallContextFieldTag.ProgramCounter, pc + 1) \
            .call_context_read(1, CallContextFieldTag.StackPointer, 1024) \
            .call_context_read(1, CallContextFieldTag.GasLeft, gas_left) \
            .call_context_read(1, CallContextFieldTag.MemorySize, 0) \
            .call_context_read(1, CallContextFieldTag.ReversibleWriteCounter, reversible_write_counter) \
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
                execution_state=ExecutionState.ErrorOutOfGasAccountAccess,
                rw_counter=rw_counter,
                call_id=current_call_id,
                is_root=is_root,
                is_create=False,
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
                gas_left=0,
            )
            if is_root is True
            else StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=rw_table.rw_counter + reversible_write_counter,
                call_id=1,
                is_root=False,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=pc + 1,
                stack_pointer=1024,
                gas_left=gas_left,
                reversible_write_counter=reversible_write_counter,
            ),
        ],
    )

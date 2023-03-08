import pytest
from collections import namedtuple
from itertools import chain, product
from zkevm_specs.evm import (
    Account,
    AccountFieldTag,
    Block,
    Bytecode,
    CallContextFieldTag,
    ExecutionState,
    Opcode,
    RWDictionary,
    StepState,
    Tables,
    verify_steps,
)
from zkevm_specs.util import (
    RLC,
    rand_fq,
)
from common import CallContext

Stack = namedtuple(
    "Stack",
    ["gas", "value", "cd_offset", "cd_length", "rd_offset", "rd_length"],
    defaults=[100, 0, 64, 320, 0, 32],
)


def call_bytecode(opcode: Opcode, stack: Stack, callee: Account) -> Bytecode:
    if opcode == Opcode.CALL:
        bytecode = (
            Bytecode()
            .call(
                stack.gas,
                callee.address,
                stack.value,
                stack.cd_offset,
                stack.cd_length,
                stack.rd_offset,
                stack.rd_length,
            )
            .stop()
        )
    elif opcode == Opcode.CALLCODE:
        bytecode = (
            Bytecode()
            .callcode(
                stack.gas,
                callee.address,
                stack.value,
                stack.cd_offset,
                stack.cd_length,
                stack.rd_offset,
                stack.rd_length,
            )
            .stop()
        )
    elif opcode == Opcode.DELEGATECALL:
        bytecode = (
            Bytecode()
            .delegatecall(
                stack.gas,
                callee.address,
                stack.cd_offset,
                stack.cd_length,
                stack.rd_offset,
                stack.rd_length,
            )
            .stop()
        )
    elif opcode == Opcode.STATICCALL:
        bytecode = (
            Bytecode()
            .staticcall(
                stack.gas,
                callee.address,
                stack.cd_offset,
                stack.cd_length,
                stack.rd_offset,
                stack.rd_length,
            )
            .stop()
        )
    else:
        raise Exception("unreachable")

    return bytecode


def gen_testing_data():
    callee = Account(address=0xFF, code=Bytecode().stop(), balance=int(1e18))
    call_opcodes = [Opcode.CALL, Opcode.CALLCODE, Opcode.DELEGATECALL, Opcode.STATICCALL]
    call_contexts = [
        CallContext(gas_left=50, reversible_write_counter=2),
        CallContext(gas_left=100, reversible_write_counter=2),
    ]
    stacks = [
        Stack(gas=100, cd_offset=64, cd_length=320, rd_offset=0, rd_length=32),
    ]
    is_warm_accesses = [True, False]

    return [
        (
            callee,
            call_bytecode(opcode, stack, callee),
            caller_context,
            stack,
            opcode in [Opcode.CALL, Opcode.CALLCODE],
            is_warm_access,
        )
        for opcode, caller_context, stack, is_warm_access in product(
            call_opcodes, call_contexts, stacks, is_warm_accesses
        )
    ]


TESTING_DATA = gen_testing_data()


@pytest.mark.parametrize(
    "callee, caller_bytecode, caller_context, stack, has_value, is_warm_access", TESTING_DATA
)
def test_oog_call_root(
    callee: Account,
    caller_bytecode: Bytecode,
    caller_context: CallContext,
    stack: Stack,
    has_value: bool,
    is_warm_access: bool,
):
    randomness = rand_fq()
    caller_bytecode_hash = RLC(caller_bytecode.hash(), randomness)
    callee_bytecode_hash = RLC(callee.code_hash(), randomness)

    is_success = False
    program_counter = 231 if has_value else 198

    rw_dictionary = (
        RWDictionary(24)
        .call_context_read(1, CallContextFieldTag.TxId, 1)
        .stack_read(1, 1018 - has_value, RLC(stack.gas, randomness))
        .stack_read(1, 1019 - has_value, RLC(callee.address, randomness))
    )
    if has_value:
        rw_dictionary.stack_read(1, 1019, RLC(stack.value, randomness))
    # fmt: off
    rw_dictionary \
        .stack_read(1, 1020, RLC(stack.cd_offset, randomness)) \
        .stack_read(1, 1021, RLC(stack.cd_length, randomness)) \
        .stack_read(1, 1022, RLC(stack.rd_offset, randomness)) \
        .stack_read(1, 1023, RLC(stack.rd_length, randomness)) \
        .stack_write(1, 1023, RLC(is_success, randomness)) \
        .account_read(callee.address, AccountFieldTag.CodeHash, callee_bytecode_hash) \
        .tx_access_list_account_read(1, callee.address, is_warm_access) \
        .call_context_read(1, CallContextFieldTag.IsSuccess, 0)
    # fmt: on

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(
            chain(
                caller_bytecode.table_assignments(randomness),
                callee.code.table_assignments(randomness),
            )
        ),
        rw_table=set(rw_dictionary.rws),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.ErrorOutOfGasCall,
                rw_counter=24,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=caller_bytecode_hash,
                program_counter=program_counter,
                stack_pointer=1018 - has_value,
                gas_left=caller_context.gas_left,
                memory_word_size=caller_context.memory_word_size,
                reversible_write_counter=caller_context.reversible_write_counter,
            ),
            StepState(
                execution_state=ExecutionState.EndTx,
                rw_counter=rw_dictionary.rw_counter + caller_context.reversible_write_counter,
                call_id=1,
                gas_left=0,
            ),
        ],
    )


@pytest.mark.parametrize(
    "callee, caller_bytecode, caller_context, stack, has_value, is_warm_access", TESTING_DATA
)
def test_oog_call_not_root(
    callee: Account,
    caller_bytecode: Bytecode,
    caller_context: CallContext,
    stack: Stack,
    has_value: bool,
    is_warm_access: bool,
):
    randomness = rand_fq()

    caller_bytecode_hash = RLC(caller_bytecode.hash(), randomness)
    callee_bytecode_hash = RLC(callee.code_hash(), randomness)
    callee_reversible_write_counter = 2

    is_success = False
    program_counter = 231 if has_value else 198

    rw_dictionary = (
        RWDictionary(24)
        .call_context_read(2, CallContextFieldTag.TxId, 1)
        .stack_read(2, 1018 - has_value, RLC(stack.gas, randomness))
        .stack_read(2, 1019 - has_value, RLC(callee.address, randomness))
    )
    if has_value:
        rw_dictionary.stack_read(2, 1019, RLC(stack.value, randomness))
    # fmt: off
    rw_dictionary \
        .stack_read(2, 1020, RLC(stack.cd_offset, randomness)) \
        .stack_read(2, 1021, RLC(stack.cd_length, randomness)) \
        .stack_read(2, 1022, RLC(stack.rd_offset, randomness)) \
        .stack_read(2, 1023, RLC(stack.rd_length, randomness)) \
        .stack_write(2, 1023, RLC(is_success, randomness)) \
        .account_read(callee.address, AccountFieldTag.CodeHash, callee_bytecode_hash) \
        .tx_access_list_account_read(1, callee.address, is_warm_access) \
        .call_context_read(2, CallContextFieldTag.IsSuccess, 0) \
        .call_context_read(2, CallContextFieldTag.CallerId, 1) \
        .call_context_read(1, CallContextFieldTag.IsRoot, False) \
        .call_context_read(1, CallContextFieldTag.IsCreate, False) \
        .call_context_read(1, CallContextFieldTag.CodeHash, caller_bytecode_hash) \
        .call_context_read(1, CallContextFieldTag.ProgramCounter, program_counter + 1) \
        .call_context_read(1, CallContextFieldTag.StackPointer, 1023) \
        .call_context_read(1, CallContextFieldTag.GasLeft, caller_context.gas_left) \
        .call_context_read(1, CallContextFieldTag.MemorySize, caller_context.memory_word_size) \
        .call_context_read(1, CallContextFieldTag.ReversibleWriteCounter, caller_context.reversible_write_counter) \
        .call_context_write(1, CallContextFieldTag.LastCalleeId, 2) \
        .call_context_write(1, CallContextFieldTag.LastCalleeReturnDataOffset, 0) \
        .call_context_write(1, CallContextFieldTag.LastCalleeReturnDataLength, 0)
    # fmt: on

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(
            chain(
                caller_bytecode.table_assignments(randomness),
                callee.code.table_assignments(randomness),
            )
        ),
        rw_table=set(rw_dictionary.rws),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.ErrorOutOfGasCall,
                rw_counter=24,
                call_id=2,
                is_root=False,
                is_create=False,
                code_hash=caller_bytecode_hash,
                program_counter=program_counter,
                stack_pointer=1018 - has_value,
                gas_left=0,
                reversible_write_counter=callee_reversible_write_counter,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=rw_dictionary.rw_counter + callee_reversible_write_counter,
                call_id=1,
                is_root=False,
                is_create=False,
                code_hash=caller_bytecode_hash,
                program_counter=program_counter + 1,
                stack_pointer=1023,
                gas_left=caller_context.gas_left,
                memory_word_size=caller_context.memory_word_size,
                reversible_write_counter=caller_context.reversible_write_counter,
            ),
        ],
    )

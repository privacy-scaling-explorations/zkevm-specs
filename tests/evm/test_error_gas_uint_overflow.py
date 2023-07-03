from itertools import product
import pytest

from collections import namedtuple
from zkevm_specs.util import Word
from zkevm_specs.evm_circuit import (
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    CallContextFieldTag,
    Block,
    Transaction,
    Bytecode,
    Opcode,
    RWDictionary,
)
from zkevm_specs.util.arithmetic import FQ
from zkevm_specs.util.param import (
    GAS_COST_CREATION_TX,
    GAS_COST_TX,
    MAX_U64,
    TxDataNonZeroGasEIP2028,
)

CallContext = namedtuple(
    "CallContext",
    [
        "is_root",
        "is_create",
        "program_counter",
        "stack_pointer",
        "gas_left",
        "memory_word_size",
        "reversible_write_counter",
    ],
    defaults=[True, False, 232, 1023, 100, 100, 0],
)

Stack = namedtuple(
    "Stack",
    ["gas", "value", "cd_offset", "cd_length", "rd_offset", "rd_length"],
    defaults=[100, 64, 0, 2**64 - 1, 0, 2**64],
)

Op = namedtuple(
    "Op",
    ["opcode", "byte_code"],
)


def gen_calldata(overflow: bool, is_create: bool) -> bytes:
    gas = GAS_COST_CREATION_TX if is_create else GAS_COST_TX
    data_byte = int(Opcode.PUSH32)
    calldata = []

    if overflow is False:
        bytes_len = 1
    else:
        bytes_len = int((MAX_U64 - gas) / TxDataNonZeroGasEIP2028) + overflow
    calldata.extend([data_byte] * bytes_len)
    assert len(calldata) == bytes_len
    return bytes(calldata)


def gen_testing_data():
    call_context = CallContext()

    is_root = [True, False]

    opcodes = [
        # opcodes with 2 stack values
        Op(opcode=Opcode.SHA3, byte_code=Bytecode().sha3()),
        Op(opcode=Opcode.LOG0, byte_code=Bytecode().log0()),
        Op(opcode=Opcode.LOG1, byte_code=Bytecode().log1()),
        Op(opcode=Opcode.LOG2, byte_code=Bytecode().log2()),
        Op(opcode=Opcode.LOG3, byte_code=Bytecode().log3()),
        Op(opcode=Opcode.LOG4, byte_code=Bytecode().log4()),
        Op(opcode=Opcode.RETURN, byte_code=Bytecode().return_()),
        Op(opcode=Opcode.REVERT, byte_code=Bytecode().revert()),
        # opcodes with 3 stack values
        Op(opcode=Opcode.CALLDATACOPY, byte_code=Bytecode().calldatacopy()),
        Op(opcode=Opcode.RETURNDATACOPY, byte_code=Bytecode().returndatacopy()),
        Op(opcode=Opcode.CODECOPY, byte_code=Bytecode().codecopy()),
        # opcodes with 4 stack values
        Op(opcode=Opcode.EXTCODECOPY, byte_code=Bytecode().extcodecopy()),
        # Memory opcode with 1 stack value but no `length` field
        Op(opcode=Opcode.MLOAD, byte_code=Bytecode().mload()),
        # Memory opcode with 3 stack value but no `length` field
        Op(opcode=Opcode.MSTORE, byte_code=Bytecode().mstore()),
        Op(opcode=Opcode.MSTORE8, byte_code=Bytecode().mstore8()),
        # CREATE/CREATE2
        Op(opcode=Opcode.CREATE, byte_code=Bytecode().create()),
        Op(opcode=Opcode.CREATE2, byte_code=Bytecode().create2()),
        # CALL/DELEGATECALL/STATICCALL
        # Op(opcode=Opcode.CALL, byte_code=Bytecode().call()),
        Op(opcode=Opcode.DELEGATECALL, byte_code=Bytecode().delegatecall()),
        Op(opcode=Opcode.STATICCALL, byte_code=Bytecode().staticcall()),
    ]
    stacks = [
        Stack(gas=100, cd_offset=MAX_U64 + 1, cd_length=1, rd_offset=0, rd_length=32),
        Stack(gas=100, cd_offset=0, cd_length=MAX_U64 + 1, rd_offset=0, rd_length=32),
        Stack(gas=100, cd_offset=MAX_U64 + 1, cd_length=MAX_U64 + 1, rd_offset=0, rd_length=32),
    ]

    return [
        (
            call_context,
            is_root,
            opcode.opcode,
            opcode.byte_code,
            stack,
        )
        for is_root, opcode, stack, in product(is_root, opcodes, stacks)
    ]


TESTING_DATA = gen_testing_data()


@pytest.mark.parametrize("ctx, is_root, opcode, bytecode, stack", TESTING_DATA)
def test_error_gas_uint_overflow_root(
    ctx: CallContext,
    is_root: bool,
    opcode: Opcode,
    bytecode: Bytecode,
    stack: Stack,
):
    is_create = True if opcode in [Opcode.CREATE, Opcode.CREATE2] else False
    is_memory_op = True if opcode in [Opcode.MLOAD, Opcode.MSTORE, Opcode.MSTORE8] else False

    # Special case for memory opcode.
    # Bcs these memory operation has not `length`` field, we could only manipulate `offset` to make overflow.
    # Ignore the testing if it's not a root tx and cd_offset in TESTING_DATA is not overflowed.
    if is_root is False and is_memory_op and stack.cd_offset <= MAX_U64:
        return

    # Generate overflow case from calldata if memory offset and length are not able to make overflow error.
    need_overflow = (stack.cd_offset <= MAX_U64 and stack.cd_length <= MAX_U64) or is_memory_op

    # Special case for root txs
    # To generate an overflowed calldata would cause memory corrupted in the local env.
    # So, to make ci and local test works, we ignore the cases if overflowed calldata needed.
    # Those cases were verified by changing MAX_U64 to a smaller number, like 55,000
    if need_overflow:
        return
    tx = Transaction(id=1, call_data=gen_calldata(need_overflow, is_create))

    bytecode_hash = Word(bytecode.hash())
    caller_id = 1
    if is_root is False:
        caller_id = 2

    # fixed values
    memory_offset = 0x40
    any_address = 0xCAFECAFE
    value = 0x0
    salt = 0xABCD

    rw_table = (
        RWDictionary(25)
        .call_context_read(caller_id, CallContextFieldTag.CallDataLength, len(tx.call_data))
        .call_context_read(caller_id, CallContextFieldTag.TxId, tx.id)
        .call_context_read(caller_id, CallContextFieldTag.IsRoot, FQ(is_root))
    )

    stack_pointer = 1023
    # fmt: off
    if opcode in [
        Opcode.SHA3,
        Opcode.RETURN,
        Opcode.REVERT,
        Opcode.LOG0,
        Opcode.LOG1,
        Opcode.LOG2,
        Opcode.LOG3,
        Opcode.LOG4,
    ]:
        rw_table \
        .stack_read(caller_id, 1022, Word(stack.cd_offset)) \
        .stack_read(caller_id, 1023, Word(stack.cd_length))
        stack_pointer = 1022
    elif opcode in [Opcode.CALLDATACOPY, Opcode.RETURNDATACOPY, Opcode.CODECOPY]:
        rw_table \
        .stack_read(caller_id, 1021, Word(memory_offset)) \
        .stack_read(caller_id, 1022, Word(stack.cd_offset)) \
        .stack_read(caller_id, 1023, Word(stack.cd_length))
        stack_pointer = 1021
    elif opcode in [Opcode.EXTCODECOPY]:
        rw_table \
        .stack_read(caller_id, 1020, any_address) \
        .stack_read(caller_id, 1021, Word(memory_offset)) \
        .stack_read(caller_id, 1022, Word(stack.cd_offset)) \
        .stack_read(caller_id, 1023, Word(stack.cd_length))
        stack_pointer = 1020
    elif opcode in [Opcode.MLOAD]:
        rw_table.stack_read(caller_id, 1023, Word(stack.cd_offset))
    elif opcode in [Opcode.MSTORE, Opcode.MSTORE8]:
        rw_table \
        .stack_read(caller_id, 1022, Word(stack.cd_offset)) \
        .stack_read(caller_id, 1023, Word(value))
        stack_pointer = 1022
    elif opcode in [Opcode.CREATE]:
        rw_table \
        .stack_read(caller_id, 1021, Word(value)) \
        .stack_read(caller_id, 1022, Word(stack.cd_offset)) \
        .stack_read(caller_id, 1023, Word(stack.cd_length))
        stack_pointer = 1021
    elif opcode in [Opcode.CREATE2]:
        rw_table \
        .stack_read(caller_id, 1020, Word(value)) \
        .stack_read(caller_id, 1021, Word(stack.cd_offset)) \
        .stack_read(caller_id, 1022, Word(stack.cd_length)) \
        .stack_read(caller_id, 1023, Word(salt))
        stack_pointer = 1020
    elif opcode in [Opcode.CALL]:
        rw_table \
        .stack_read(caller_id, 1017, Word(stack.gas)) \
        .stack_read(caller_id, 1018, Word(any_address)) \
        .stack_read(caller_id, 1019, Word(value)) \
        .stack_read(caller_id, 1020, Word(stack.cd_offset)) \
        .stack_read(caller_id, 1021, Word(stack.cd_length)) \
        .stack_read(caller_id, 1022, Word(stack.rd_offset)) \
        .stack_read(caller_id, 1023, Word(stack.rd_length))
        stack_pointer = 1017
    elif opcode in [Opcode.DELEGATECALL, Opcode.STATICCALL]:
        rw_table \
        .stack_read(caller_id, 1018, Word(stack.gas)) \
        .stack_read(caller_id, 1019, Word(any_address)) \
        .stack_read(caller_id, 1020, Word(stack.cd_offset)) \
        .stack_read(caller_id, 1021, Word(stack.cd_length)) \
        .stack_read(caller_id, 1022, Word(stack.rd_offset)) \
        .stack_read(caller_id, 1023, Word(stack.rd_length))
        stack_pointer = 1018
    # fmt: on

    rw_table.call_context_read(caller_id, CallContextFieldTag.IsSuccess, 0)

    # fmt: off
    if is_root is False:
        rw_table \
            .call_context_read(caller_id, CallContextFieldTag.CallerId, 1) \
            .call_context_read(1, CallContextFieldTag.IsRoot, False) \
            .call_context_read(1, CallContextFieldTag.IsCreate, is_create) \
            .call_context_read(1, CallContextFieldTag.CodeHash, bytecode_hash) \
            .call_context_read(1, CallContextFieldTag.ProgramCounter, ctx.program_counter) \
            .call_context_read(1, CallContextFieldTag.StackPointer, 1023) \
            .call_context_read(1, CallContextFieldTag.GasLeft, ctx.gas_left) \
            .call_context_read(1, CallContextFieldTag.MemorySize, ctx.memory_word_size) \
            .call_context_read(1, CallContextFieldTag.ReversibleWriteCounter, ctx.reversible_write_counter) \
            .call_context_write(1, CallContextFieldTag.LastCalleeId, 2) \
            .call_context_write(1, CallContextFieldTag.LastCalleeReturnDataOffset, 0) \
            .call_context_write(1, CallContextFieldTag.LastCalleeReturnDataLength, 0)
    # fmt: on

    tables = Tables(
        block_table=set(Block().table_assignments()),
        tx_table=set(tx.table_assignments()),
        bytecode_table=set(bytecode.table_assignments()),
        rw_table=set(rw_table.rws),
    )

    verify_steps(
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.ErrorGasUintOverflow,
                rw_counter=25,
                call_id=1 if is_root is True else 2,
                is_root=is_root,
                is_create=is_create,
                code_hash=bytecode_hash,
                program_counter=0,
                stack_pointer=stack_pointer,
                gas_left=0,
                reversible_write_counter=0,
            ),
            (
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
                    is_create=is_create,
                    code_hash=bytecode_hash,
                    program_counter=ctx.program_counter,
                    stack_pointer=1023,
                    gas_left=ctx.gas_left,
                    memory_word_size=ctx.memory_word_size,
                    reversible_write_counter=ctx.reversible_write_counter,
                )
            ),
        ],
    )

import pytest

from typing import List
from common import CallContext
from zkevm_specs.ecc_circuit import EcMul
from zkevm_specs.evm_circuit import (
    Bytecode,
    CallContextFieldTag,
    ExecutionState,
    Precompile,
    RWDictionary,
    StepState,
    Tables,
    verify_steps,
)
from zkevm_specs.util import (
    Word,
    FQ,
)
from zkevm_specs.evm_circuit.table import EccOpTag, EccTableRow


def gen_testing_data():
    normal = (
        CallContext(),
        EcMul(
            p=(1, 2),
            s=7,
            out=(
                0x17072B2ED3BB8D759A5325F477629386CB6FC6ECB801BD76983A6B86ABFFE078,
                0x168ADA6CD130DD52017BB54BFA19377AADFE3BF05D18F41B77809F7F60D4AF9E,
            ),
        ),
        True,
    )
    infinite_p = (
        CallContext(),
        EcMul(
            p=(0, 0),
            s=7,
            out=(0, 0),
        ),
        True,
    )
    zero_s = (
        CallContext(),
        EcMul(
            p=(1, 2),
            s=0,
            out=(0, 0),
        ),
        True,
    )
    over_field_size_s = (
        CallContext(),
        EcMul(
            p=(1, 2),
            s=FQ.field_modulus + 7,
            out=(
                0x17072B2ED3BB8D759A5325F477629386CB6FC6ECB801BD76983A6B86ABFFE078,
                0x168ADA6CD130DD52017BB54BFA19377AADFE3BF05D18F41B77809F7F60D4AF9E,
            ),
        ),
        True,
    )
    invalid_pts = (
        CallContext(),
        EcMul(
            p=(2, 3),
            s=7,
            out=(0, 0),
        ),
        False,
    )

    return [normal, infinite_p, zero_s, over_field_size_s, invalid_pts]


TESTING_DATA = gen_testing_data()


@pytest.mark.parametrize(
    "caller_ctx, op, is_success",
    TESTING_DATA,
)
def test_ecMul(
    caller_ctx: CallContext,
    op: EcMul,
    is_success: bool,
):
    call_id = 1
    callee_id = 2
    gas_left = 1000

    call_data_offset = 0
    call_data_length = 96
    return_data_offset = 0
    return_data_length = 64 if is_success else 0

    aux_data = [
        Word(op.p[0]),
        Word(op.p[1]),
        Word(op.s),
        FQ(op.out[0]),
        FQ(op.out[1]),
    ]

    # assign ecc_table
    ecc_row: List[EccTableRow] = []
    ecc_row.append(
        EccTableRow(
            FQ(EccOpTag.Mul),
            Word(op.p[0]),
            Word(op.p[1]),
            Word(op.s),
            Word(0),
            FQ.zero(),
            FQ(op.out[0]),
            FQ(op.out[1]),
            FQ(is_success),
        )
    )

    code = (
        Bytecode()
        .call(
            gas_left,
            Precompile.BN254SCALARMUL,
            0,
            call_data_offset,
            call_data_length,
            return_data_offset,
            return_data_length,
        )
        .stop()
    )
    code_hash = Word(code.hash())

    rw_dictionary = (
        # fmt: off
        RWDictionary(1)
        .call_context_read(callee_id, CallContextFieldTag.IsSuccess, FQ(is_success))
        .call_context_read(callee_id, CallContextFieldTag.CalleeAddress, Word(Precompile.BN254SCALARMUL))
        # fmt: on
    )

    rw_dictionary = (
        # fmt: off
        rw_dictionary
        .call_context_read(callee_id, CallContextFieldTag.CallerId, call_id)
        .call_context_read(call_id, CallContextFieldTag.IsRoot, False)
        .call_context_read(call_id, CallContextFieldTag.IsCreate, False)
        .call_context_read(call_id, CallContextFieldTag.CodeHash, code_hash)
        .call_context_read(call_id, CallContextFieldTag.ProgramCounter, caller_ctx.program_counter)
        .call_context_read(call_id, CallContextFieldTag.StackPointer, caller_ctx.stack_pointer)
        .call_context_read(call_id, CallContextFieldTag.GasLeft, caller_ctx.gas_left)
        .call_context_read(call_id, CallContextFieldTag.MemorySize, caller_ctx.memory_word_size)
        .call_context_read(call_id, CallContextFieldTag.ReversibleWriteCounter, caller_ctx.reversible_write_counter)
        .call_context_write(call_id, CallContextFieldTag.LastCalleeId, callee_id)
        .call_context_write(call_id, CallContextFieldTag.LastCalleeReturnDataOffset, FQ(return_data_offset))
        .call_context_write(call_id, CallContextFieldTag.LastCalleeReturnDataLength, FQ(return_data_length))
        # fmt: on
    )

    tables = Tables(
        block_table=set(),
        tx_table=set(),
        withdrawal_table=set(),
        bytecode_table=set(code.table_assignments()),
        rw_table=set(rw_dictionary.rws),
        ecc_table=set(ecc_row),
    )

    verify_steps(
        tables,
        steps=[
            StepState(
                execution_state=ExecutionState.BN254_SCALAR_MUL,
                rw_counter=1,
                call_id=callee_id,
                is_root=False,
                code_hash=code_hash,
                program_counter=caller_ctx.program_counter - 1,
                stack_pointer=1023,
                memory_word_size=call_data_length,
                gas_left=gas_left,
                aux_data=aux_data,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=rw_dictionary.rw_counter,
                call_id=call_id,
                is_root=False,
                code_hash=code_hash,
                program_counter=caller_ctx.program_counter,
                stack_pointer=caller_ctx.stack_pointer,
                memory_word_size=caller_ctx.memory_word_size,
                gas_left=gas_left - Precompile.BN254SCALARMUL.base_gas_cost()
                if is_success
                else FQ(0),
            ),
        ],
    )

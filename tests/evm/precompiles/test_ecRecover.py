import pytest

from typing import List
from common import CallContext, rand_fq
from eth_keys import keys  # type: ignore
from eth_utils import keccak
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
from zkevm_specs.evm_circuit.execution.precompiles.ecrecover import SECP256K1N
from zkevm_specs.util import (
    Word,
    FQ,
)
from zkevm_specs.evm_circuit.table import SigTableRow


def gen_testing_data():
    # basic
    msg = "Hello World!"
    sk = keys.PrivateKey(rand_fq().n.to_bytes(32, "little"))
    address = sk.public_key.to_canonical_address()
    msg_hash = keccak(bytes(msg, "utf-8"))
    sig = sk.sign_msg_hash(msg_hash)
    v = sig.v
    r = sig.r
    s = sig.s

    # successful case
    normal = [CallContext(), msg_hash, v, r, s, address]

    # failure cases
    zero_addr = [CallContext(), msg_hash, v, r, s, bytes(0)]
    sig_r_over_ub = [CallContext(), msg_hash, v, SECP256K1N, s, bytes(0)]
    sig_s_over_ub = [CallContext(), msg_hash, v, r, SECP256K1N, bytes(0)]
    sig_r_zero = [CallContext(), msg_hash, v, 0, s, bytes(0)]
    sig_s_zero = [CallContext(), msg_hash, v, r, 0, bytes(0)]
    sig_v_29 = [CallContext(), msg_hash, v, SECP256K1N, s, bytes(0)]

    return [normal, zero_addr, sig_r_over_ub, sig_s_over_ub, sig_r_zero, sig_s_zero, sig_v_29]


TESTING_DATA = gen_testing_data()


@pytest.mark.parametrize(
    "caller_ctx, msg_hash, v, r, s, address",
    TESTING_DATA,
)
def test_ecRecover(
    caller_ctx: CallContext,
    msg_hash: bytes,
    v: int,
    r: int,
    s: int,
    address: bytes,
):
    call_id = 1
    callee_id = 2
    gas = Precompile.ECRECOVER.base_gas_cost()

    success = True if len(address) != 0 else False
    call_data_offset = 0
    call_data_length = 0x80
    return_data_offset = 0
    return_data_length = 0x20 if success else 0

    aux_data = [
        Word(msg_hash),
        Word(v + 27),
        Word(r),
        Word(s),
        FQ(int.from_bytes(address, "big")),
    ]

    # assign sig_table
    sig_row: List[SigTableRow] = []
    sig_row.append(
        SigTableRow(
            Word(msg_hash),
            FQ(v),
            Word(r),
            Word(s),
            FQ(int.from_bytes(address, "big")),
            FQ(success),
        )
    )

    code = (
        Bytecode()
        .call(
            gas,
            Precompile.ECRECOVER,
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
        .call_context_read(callee_id, CallContextFieldTag.IsSuccess, success)
        .call_context_read(callee_id, CallContextFieldTag.CalleeAddress, Word(Precompile.ECRECOVER))
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
        sig_table=set(sig_row),
    )

    verify_steps(
        tables,
        steps=[
            StepState(
                execution_state=ExecutionState.ECRECOVER,
                rw_counter=1,
                call_id=callee_id,
                is_root=False,
                code_hash=code_hash,
                program_counter=caller_ctx.program_counter - 1,
                stack_pointer=1023,
                memory_word_size=call_data_length,
                gas_left=gas,
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
                gas_left=0,
            ),
        ],
    )

import pytest

from typing import List
from common import CallContext, rand_fq
from zkevm_specs.ecc_circuit import EcPairing
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
from zkevm_specs.util.arithmetic import RLC
from zkevm_specs.util.param import Bn254PairingPerPointGas


def gen_testing_data():
    normal = (
        CallContext(),
        EcPairing(
            g1_pts=[
                (
                    0x2CF44499D5D27BB186308B7AF7AF02AC5BC9EEB6A3D147C186B21FB1B76E18DA,
                    0x2C0F001F52110CCFE69108924926E45F0B0C868DF0E7BDE1FE16D3242DC715F6,
                ),
                (
                    1,
                    0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45,
                ),
            ],
            g2_pts=[
                (
                    0x1FB19BB476F6B9E44E2A32234DA8212F61CD63919354BC06AEF31E3CFAFF3EBC,
                    0x22606845FF186793914E03E21DF544C34FFE2F2F3504DE8A79D9159ECA2D98D9,
                    0x2BD368E28381E8ECCB5FA81FC26CF3F048EEA9ABFDD85D7ED3AB3698D63E4F90,
                    0x2FE02E47887507ADF0FF1743CBAC6BA291E66F59BE6BD763950BB16041A0A85E,
                ),
                (
                    0x1971FF0471B09FA93CAAF13CBF443C1AEDE09CC4328F5A62AAD45F40EC133EB4,
                    0x091058A3141822985733CBDDDFED0FD8D6C104E9E9EFF40BF5ABFEF9AB163BC7,
                    0x2A23AF9A5CE2BA2796C1F4E453A370EB0AF8C212D9DC9ACD8FC02C2E907BAEA2,
                    0x23A8EB0B0996252CB548A4487DA97B02422EBC0E834613F954DE6C7E0AFDC1FC,
                ),
            ],
            out=1,
        ),
        True,
        True,
    )
    # p and q are valid points but p[0] == p[1] which causes e(p[0], g2[0]) != e(p[0], g2[1])
    failure_with_valid_input = (
        CallContext(),
        EcPairing(
            g1_pts=[
                (
                    0x2CF44499D5D27BB186308B7AF7AF02AC5BC9EEB6A3D147C186B21FB1B76E18DA,
                    0x2C0F001F52110CCFE69108924926E45F0B0C868DF0E7BDE1FE16D3242DC715F6,
                ),
                (
                    0x2CF44499D5D27BB186308B7AF7AF02AC5BC9EEB6A3D147C186B21FB1B76E18DA,
                    0x2C0F001F52110CCFE69108924926E45F0B0C868DF0E7BDE1FE16D3242DC715F6,
                ),
            ],
            g2_pts=[
                (
                    0x1FB19BB476F6B9E44E2A32234DA8212F61CD63919354BC06AEF31E3CFAFF3EBC,
                    0x22606845FF186793914E03E21DF544C34FFE2F2F3504DE8A79D9159ECA2D98D9,
                    0x2BD368E28381E8ECCB5FA81FC26CF3F048EEA9ABFDD85D7ED3AB3698D63E4F90,
                    0x2FE02E47887507ADF0FF1743CBAC6BA291E66F59BE6BD763950BB16041A0A85E,
                ),
                (
                    0x1971FF0471B09FA93CAAF13CBF443C1AEDE09CC4328F5A62AAD45F40EC133EB4,
                    0x091058A3141822985733CBDDDFED0FD8D6C104E9E9EFF40BF5ABFEF9AB163BC7,
                    0x2A23AF9A5CE2BA2796C1F4E453A370EB0AF8C212D9DC9ACD8FC02C2E907BAEA2,
                    0x23A8EB0B0996252CB548A4487DA97B02422EBC0E834613F954DE6C7E0AFDC1FC,
                ),
            ],
            out=0,
        ),
        True,
        False,
    )
    # valid input
    empty_input = (
        CallContext(),
        EcPairing(
            g1_pts=[],
            g2_pts=[],
            out=1,
        ),
        True,
        True,
    )
    # invalid p (1, 1)
    invalid_input = (
        CallContext(),
        EcPairing(
            g1_pts=[
                (
                    0x2CF44499D5D27BB186308B7AF7AF02AC5BC9EEB6A3D147C186B21FB1B76E18DA,
                    0x2C0F001F52110CCFE69108924926E45F0B0C868DF0E7BDE1FE16D3242DC715F6,
                ),
                (1, 1),
            ],
            g2_pts=[
                (
                    0x1FB19BB476F6B9E44E2A32234DA8212F61CD63919354BC06AEF31E3CFAFF3EBC,
                    0x22606845FF186793914E03E21DF544C34FFE2F2F3504DE8A79D9159ECA2D98D9,
                    0x2BD368E28381E8ECCB5FA81FC26CF3F048EEA9ABFDD85D7ED3AB3698D63E4F90,
                    0x2FE02E47887507ADF0FF1743CBAC6BA291E66F59BE6BD763950BB16041A0A85E,
                ),
                (
                    0x1971FF0471B09FA93CAAF13CBF443C1AEDE09CC4328F5A62AAD45F40EC133EB4,
                    0x091058A3141822985733CBDDDFED0FD8D6C104E9E9EFF40BF5ABFEF9AB163BC7,
                    0x2A23AF9A5CE2BA2796C1F4E453A370EB0AF8C212D9DC9ACD8FC02C2E907BAEA2,
                    0x23A8EB0B0996252CB548A4487DA97B02422EBC0E834613F954DE6C7E0AFDC1FC,
                ),
            ],
            out=0,
        ),
        False,
        False,
    )
    # invalid_input_size, only 320 bytes data given (should be 192*n bytes)
    invalid_input_size = (
        CallContext(),
        EcPairing(
            g1_pts=[
                (
                    0x2CF44499D5D27BB186308B7AF7AF02AC5BC9EEB6A3D147C186B21FB1B76E18DA,
                    0x2C0F001F52110CCFE69108924926E45F0B0C868DF0E7BDE1FE16D3242DC715F6,
                ),
                (
                    1,
                    0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45,
                ),
            ],
            g2_pts=[
                (
                    0x1FB19BB476F6B9E44E2A32234DA8212F61CD63919354BC06AEF31E3CFAFF3EBC,
                    0x22606845FF186793914E03E21DF544C34FFE2F2F3504DE8A79D9159ECA2D98D9,
                    0x2BD368E28381E8ECCB5FA81FC26CF3F048EEA9ABFDD85D7ED3AB3698D63E4F90,
                    0x2FE02E47887507ADF0FF1743CBAC6BA291E66F59BE6BD763950BB16041A0A85E,
                ),
                (
                    0x1971FF0471B09FA93CAAF13CBF443C1AEDE09CC4328F5A62AAD45F40EC133EB4,
                    0x091058A3141822985733CBDDDFED0FD8D6C104E9E9EFF40BF5ABFEF9AB163BC7,
                ),
            ],
            out=0,
        ),
        False,
        False,
    )

    return [normal, failure_with_valid_input, empty_input, invalid_input, invalid_input_size]


TESTING_DATA = gen_testing_data()

randomness_keccak = rand_fq()


@pytest.mark.parametrize(
    "caller_ctx, op, is_valid_data, is_success",
    TESTING_DATA,
)
def test_ecPairing(
    caller_ctx: CallContext,
    op: EcPairing,
    is_valid_data: bool,
    is_success: bool,
):
    call_id = 1
    callee_id = 2
    gas_left = 1000_000

    input_bytes = bytearray(b"")
    for p, q in zip(op.g1_pts, op.g2_pts):
        input_bytes.extend(p[0].to_bytes(32, "little"))
        input_bytes.extend(p[1].to_bytes(32, "little"))
        input_bytes.extend(q[0].to_bytes(32, "little"))
        input_bytes.extend(q[1].to_bytes(32, "little"))
        # special condition for invalid_input_size case
        if len(q) > 2:
            input_bytes.extend(q[2].to_bytes(32, "little"))
        if len(q) > 3:
            input_bytes.extend(q[3].to_bytes(32, "little"))
    input_size = len(input_bytes)
    pairs = int(input_size / 192)

    call_data_offset = 0
    call_data_length = input_size
    return_data_offset = 0
    return_data_length = 32
    gas_cost = Precompile.BN254PAIRING.base_gas_cost() + pairs * Bn254PairingPerPointGas

    input_rlc = RLC(bytes(reversed(input_bytes)), randomness_keccak, n_bytes=input_size).expr()
    aux_data = [
        FQ(input_rlc.n),
        FQ(pairs),
        FQ(is_valid_data),
        FQ(op.out),
    ]

    # assign ecc_table
    ecc_row: List[EccTableRow] = []
    ecc_row.append(
        EccTableRow(
            FQ(EccOpTag.Pairing),
            Word(0),
            Word(0),
            Word(0),
            Word(0),
            input_rlc,
            FQ.zero(),
            FQ(is_success),
            FQ(is_valid_data),
        )
    )

    code = (
        Bytecode()
        .call(
            gas_left,
            Precompile.BN254PAIRING,
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
        .call_context_read(callee_id, CallContextFieldTag.CallDataLength, FQ(call_data_length))
        .call_context_read(callee_id, CallContextFieldTag.CalleeAddress, Word(Precompile.BN254PAIRING))
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
                execution_state=ExecutionState.BN254_PAIRING,
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
                gas_left=gas_left - FQ(gas_cost) if is_success else FQ(0),
            ),
        ],
    )

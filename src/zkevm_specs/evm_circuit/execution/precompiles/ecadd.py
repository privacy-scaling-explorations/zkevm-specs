from zkevm_specs.evm_circuit.instruction import Instruction
from zkevm_specs.evm_circuit.table import (
    CallContextFieldTag,
    EccOpTag,
    FixedTableTag,
    RW,
)
from zkevm_specs.util import FQ, Word, Bn254AddGas


def ecAdd(instruction: Instruction):
    is_success = instruction.call_context_lookup(CallContextFieldTag.IsSuccess, RW.Read)
    address_word = instruction.call_context_lookup_word(CallContextFieldTag.CalleeAddress)
    address = instruction.word_to_address(address_word)
    instruction.fixed_lookup(
        FixedTableTag.PrecompileInfo,
        FQ(instruction.curr.execution_state),
        address,
        FQ(Bn254AddGas),
    )

    # Get p, q and out from aux_data
    px: Word = instruction.curr.aux_data[0]
    py: Word = instruction.curr.aux_data[1]
    qx: Word = instruction.curr.aux_data[2]
    qy: Word = instruction.curr.aux_data[3]
    outx: FQ = instruction.curr.aux_data[4]
    outy: FQ = instruction.curr.aux_data[5]

    # if is_success is false, outx and outy are zero
    if is_success == FQ.zero():
        instruction.constrain_zero(outx)
        instruction.constrain_zero(outy)

    # ecc table lookup
    instruction.ecc_lookup(FQ(EccOpTag.Add), px, py, qx, qy, FQ.zero(), outx, outy, is_success)

    # consume gas
    # consume all the gas if is_success is false
    gas_left = FQ.zero()
    if is_success == FQ(1):
        gas_left = instruction.curr.gas_left - FQ(Bn254AddGas)

    # Restore caller state to next StepState
    instruction.step_state_transition_to_restored_context(
        rw_counter_delta=instruction.rw_counter_offset,
        return_data_offset=FQ.zero(),
        return_data_length=FQ(64) if is_success == FQ(1) else FQ.zero(),
        gas_left=gas_left,
    )

from instruction import Instruction, Transition
from table import (
    CallContextFieldTag,
    FixedTableTag,
    RW,
)
from zkevm_specs.util import FQ, Word, EcrecoverGas

SECP256K1N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


def ecRecover(instruction: Instruction):
    is_success = instruction.call_context_lookup(CallContextFieldTag.IsSuccess, RW.Read)
    address_word = instruction.call_context_lookup_word(CallContextFieldTag.CalleeAddress)
    address = instruction.word_to_address(address_word)
    instruction.fixed_lookup(
        FixedTableTag.PrecompileInfo,
        FQ(instruction.curr.execution_state),
        address,
        FQ(EcrecoverGas),
    )

    # Get msg_hash, signature and recovered address from aux_data
    msg_hash = instruction.curr.aux_data[0]
    sig_v = instruction.curr.aux_data[1]
    sig_r = instruction.curr.aux_data[2]
    sig_s = instruction.curr.aux_data[3]
    recovered_addr = instruction.curr.aux_data[4]

    is_recovered = FQ(instruction.is_zero_word(recovered_addr) != FQ(0))

    # if the address is recovered, this call should be success either
    instruction.constrain_equal(is_success, is_recovered)

    # verify r and s
    sig_r_upper_bound, _ = instruction.compare_word(sig_r, Word(SECP256K1N))
    sig_s_upper_bound, _ = instruction.compare_word(sig_s, Word(SECP256K1N))
    sig_r_lower_bound, _ = instruction.compare_word(Word(1), sig_r)
    sig_s_lower_bound, _ = instruction.compare_word(Word(1), sig_s)
    valid_r_s = instruction.is_equal(
        sig_r_upper_bound + sig_s_upper_bound + sig_r_lower_bound + sig_s_lower_bound, FQ(4)
    )

    # verify v
    is_equal_27 = instruction.is_equal_word(sig_v, Word(27))
    is_equal_28 = instruction.is_equal_word(sig_v, Word(28))
    valid_v = instruction.is_equal(is_equal_27 + is_equal_28, FQ(1))

    if valid_r_s + valid_v == FQ(2):
        # sig table lookups
        instruction.sig_lookup(
            msg_hash, sig_v - FQ(27).expr(), sig_r, sig_s, recovered_addr, is_recovered
        )
    else:
        instruction.constrain_zero(is_recovered)
        instruction.constrain_zero(recovered_addr)

    # calculate gas cost
    gas_cost = EcrecoverGas if is_success == FQ(1) else instruction.curr.gas_left

    # Restore caller state to next StepState
    instruction.step_state_transition_to_restored_context(
        rw_counter_delta=instruction.rw_counter_offset,
        return_data_offset=FQ(0),
        return_data_length=32 if is_success == FQ(1) else 0,
        gas_left=Transition.delta(-gas_cost),
    )

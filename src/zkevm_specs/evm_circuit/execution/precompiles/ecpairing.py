from zkevm_specs.evm_circuit.instruction import Instruction
from zkevm_specs.evm_circuit.table import (
    CallContextFieldTag,
    EccOpTag,
    FixedTableTag,
)
from zkevm_specs.util import FQ, Word, Bn254PairingBaseGas, Bn254PairingPerPointGas

# Input is a multiple of 6 32-byte values, 6 * 32 = 192 (bytes)
BYTES_PER_PAIRING = 192


def ecPairing(instruction: Instruction):
    is_success = instruction.call_context_lookup(CallContextFieldTag.IsSuccess)
    calldata_len = instruction.call_context_lookup(CallContextFieldTag.CallDataLength)
    address_word = instruction.call_context_lookup_word(CallContextFieldTag.CalleeAddress)
    address = instruction.word_to_address(address_word)
    instruction.fixed_lookup(
        FixedTableTag.PrecompileInfo,
        FQ(instruction.curr.execution_state),
        address,
        FQ(Bn254PairingBaseGas),
    )

    # Get input_rlc and result
    input_rlc: FQ = instruction.curr.aux_data[0]
    input_pairs: FQ = instruction.curr.aux_data[1]
    is_valid_input: FQ = instruction.curr.aux_data[2]
    output: FQ = instruction.curr.aux_data[3]

    # if input data is valid, then it's a successful call even the pairing is failed.
    # ref: https://github.com/ethereum/execution-specs/blob/3fe6514f2d9d234e760d11af883a47c1263eff51/src/ethereum/shanghai/vm/precompiled_contracts/alt_bn128.py#L153-L156
    # see above link, there is no any error returns, no matter the pairing result is 1 or 0
    instruction.constrain_equal(is_success.expr(), is_valid_input)

    # invalid input data length
    if calldata_len.n % BYTES_PER_PAIRING != 0:
        instruction.constrain_equal(output, FQ.zero())
        instruction.constrain_equal(is_valid_input, FQ.zero())
    else:  # valid input length
        # data length is a multiple of 192 bytes
        instruction.constrain_equal(calldata_len, FQ(input_pairs.n * BYTES_PER_PAIRING))

        # if an empty input which is allowed, then output is 1 and input_rlc is 0
        if calldata_len == FQ.zero():
            instruction.constrain_zero(input_pairs)
            instruction.constrain_zero(input_rlc)
            instruction.constrain_equal(output, FQ.one())

    # ecc table lookup
    instruction.ecc_lookup(
        FQ(EccOpTag.Pairing),
        Word(0),
        Word(0),
        Word(0),
        Word(0),
        input_rlc,
        FQ.zero(),
        output,
        is_valid_input,
    )

    # consume all the gas if is_success is false
    gas_left = FQ.zero()
    if is_success == FQ(1):
        gas_left = (
            instruction.curr.gas_left
            - FQ(Bn254PairingBaseGas)
            - FQ(input_pairs.n * Bn254PairingPerPointGas)
        )

    # Restore caller state to next StepState
    instruction.step_state_transition_to_restored_context(
        rw_counter_delta=instruction.rw_counter_offset,
        return_data_offset=FQ.zero(),
        return_data_length=FQ(32) if is_valid_input == FQ(1) else FQ.zero(),
        gas_left=gas_left,
    )

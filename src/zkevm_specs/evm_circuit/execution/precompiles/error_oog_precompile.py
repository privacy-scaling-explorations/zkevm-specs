from zkevm_specs.evm_circuit.execution.precompiles.ecpairing import BYTES_PER_PAIRING
from zkevm_specs.evm_circuit.instruction import Instruction
from zkevm_specs.evm_circuit.precompile import Precompile
from zkevm_specs.evm_circuit.table import CallContextFieldTag
from zkevm_specs.util import FQ
from zkevm_specs.util.param import N_BYTES_GAS, Bn254PairingPerPointGas, IdentityPerWordGas


def error_oog_precompile(instruction: Instruction):
    address_word = instruction.call_context_lookup_word(CallContextFieldTag.CalleeAddress)
    address = instruction.word_to_address(address_word)
    calldata_len = instruction.call_context_lookup(CallContextFieldTag.CallDataLength)

    # the address must be one of precompiles
    instruction.constrain_equal(instruction.precompile(address), FQ.one())

    # TODO: Handle OOG of SHA256, RIPEMD160, BIGMODEXP and BLAKE2F.
    ### total gas cost
    # constant gas cost
    precompile = Precompile(address)
    gas_cost = precompile.base_gas_cost()
    # dynamic gas cost
    if precompile == Precompile.BN254PAIRING:
        pairs = calldata_len / BYTES_PER_PAIRING
        gas_cost += Bn254PairingPerPointGas * pairs
    elif precompile == Precompile.DATACOPY:
        gas_cost += instruction.memory_copier_gas_cost(calldata_len, FQ(0), IdentityPerWordGas)

    # check gas left is less than total gas required
    insufficient_gas, _ = instruction.compare(instruction.curr.gas_left, gas_cost, N_BYTES_GAS)
    instruction.constrain_equal(insufficient_gas, FQ(1))

    instruction.constrain_error_state(
        instruction.rw_counter_offset + instruction.curr.reversible_write_counter
    )

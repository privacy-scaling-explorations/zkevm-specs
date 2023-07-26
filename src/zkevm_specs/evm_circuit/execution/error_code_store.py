from zkevm_specs.evm_circuit.table import RW
from zkevm_specs.util.param import (
    GAS_COST_CODE_DEPOSIT,
    MAX_CODE_SIZE,
    N_BYTES_MEMORY_ADDRESS,
    N_BYTES_STACK,
)
from ...util import FQ
from ..instruction import Instruction
from ..opcode import Opcode
from ...util import N_BYTES_GAS


def error_code_store(instruction: Instruction):
    # retrieve op code associated to oog constant error
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.RETURN)

    # the call must be coming from CREATE or CREATE2
    instruction.constrain_equal(FQ(instruction.curr.is_create), FQ(1))

    # pop length (which is the bytecode size) from stack
    return_length_word = instruction.stack_lookup(RW.Read, 1)
    return_length = instruction.word_to_fq(return_length_word, N_BYTES_MEMORY_ADDRESS)

    # check if bytecode size exceeds MAX_CODE_SIZE
    over_max_code_size, _ = instruction.compare(FQ(MAX_CODE_SIZE), return_length, N_BYTES_STACK)

    # check gas left is less than total gas required
    gas_cost_code_store = FQ(GAS_COST_CODE_DEPOSIT) * return_length
    insufficient_gas, _ = instruction.compare(
        instruction.curr.gas_left, gas_cost_code_store, N_BYTES_GAS
    )

    # make sure this call hits at least one of [CodeStoreOutOfGas, MaxCodeSizeExceeded]
    instruction.constrain_not_zero(insufficient_gas + over_max_code_size)

    instruction.constrain_error_state(
        1 + instruction.rw_counter_offset + instruction.curr.reversible_write_counter.n
    )

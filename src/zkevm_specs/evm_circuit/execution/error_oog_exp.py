from zkevm_specs.util.param import (
    GAS_COST_EXP_PER_BYTE,
    GAS_COST_LOG,
    GAS_COST_LOGDATA,
    GAS_COST_SLOW,
    N_BYTES_MEMORY_ADDRESS,
)
from ...util import FQ
from ..instruction import Instruction
from ..opcode import Opcode
from ...util import N_BYTES_GAS


def error_oog_exp(instruction: Instruction):
    # retrieve op code associated to oog constant error
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.EXP)

    instruction.stack_pop()
    exponent = instruction.stack_pop()

    # get total gas cost
    exponent_byte_size = instruction.byte_size(exponent)
    dynamic_gas_cost = GAS_COST_EXP_PER_BYTE * exponent_byte_size

    # check gas left is less than total gas required
    gas_not_enough, _ = instruction.compare(
        instruction.curr.gas_left, dynamic_gas_cost + GAS_COST_SLOW, N_BYTES_GAS
    )
    instruction.constrain_equal(gas_not_enough, FQ(1))

    instruction.constrain_error_state(instruction.rw_counter_offset + 1)

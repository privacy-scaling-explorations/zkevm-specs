from zkevm_specs.evm_circuit.table import RW
from zkevm_specs.util.param import (
    GAS_COST_EXP_PER_BYTE,
    GAS_COST_SLOW,
)
from ...util import FQ
from ..instruction import Instruction
from ..opcode import Opcode
from ...util import N_BYTES_GAS


def error_oog_exp(instruction: Instruction):
    # retrieve op code associated to oog exp error
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.EXP)

    exponent = instruction.stack_lookup(RW.Read, 1)

    # get total gas cost
    exponent_byte_size = instruction.byte_size(exponent)
    dynamic_gas_cost = GAS_COST_EXP_PER_BYTE * exponent_byte_size

    # check gas left is less than total gas required
    insufficient_gas, _ = instruction.compare(
        instruction.curr.gas_left, dynamic_gas_cost + GAS_COST_SLOW, N_BYTES_GAS
    )
    instruction.constrain_equal(insufficient_gas, FQ(1))

    instruction.constrain_error_state(
        instruction.rw_counter_offset + instruction.curr.reversible_write_counter
    )

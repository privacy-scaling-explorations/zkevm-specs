from zkevm_specs.evm_circuit.table import RW
from zkevm_specs.util.param import GAS_COST_CREATE
from ...util import FQ
from ..instruction import Instruction
from ..opcode import Opcode
from ...util import N_BYTES_GAS


def error_oog_dynamic_memory_expansion(instruction: Instruction):
    # retrieve op code associated to oog error
    opcode = instruction.opcode_lookup(True)
    is_return, is_revert = instruction.multiple_select(opcode, (Opcode.RETURN, Opcode.REVERT))

    # Constrain opcode must be RETURN or REVERT.
    instruction.constrain_equal(is_return + is_revert, FQ(1))

    # get gas cost of memory expansion
    offset_word = instruction.stack_pop()
    size_word = instruction.stack_pop()
    offset, size = instruction.memory_offset_and_length(offset_word, size_word)
    (_, memory_expansion_gas_cost) = instruction.memory_expansion(offset, size)

    # check gas left is less than total gas required
    gas_not_enough, _ = instruction.compare(
        instruction.curr.gas_left, memory_expansion_gas_cost, N_BYTES_GAS
    )
    instruction.constrain_equal(gas_not_enough, FQ(1))

    instruction.constrain_error_state(
        instruction.rw_counter_offset + instruction.curr.reversible_write_counter
    )

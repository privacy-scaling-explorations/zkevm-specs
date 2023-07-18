from zkevm_specs.util.param import GAS_COST_CREATE, N_BYTES_MEMORY_ADDRESS
from ...util import FQ
from ..instruction import Instruction
from ..opcode import Opcode
from ...util import N_BYTES_GAS


def error_oog_dynamic_memory_expansion(instruction: Instruction):
    # retrieve op code associated to oog constant error
    opcode = instruction.opcode_lookup(True)
    is_create, is_create2, is_return, is_revert = instruction.multiple_select(
        opcode, (Opcode.CREATE, Opcode.CREATE2, Opcode.RETURN, Opcode.REVERT)
    )

    # Constrain opcode must be one of CREATE, CREATE2, RETURN or REVERT.
    instruction.constrain_equal(is_create + is_create2 + is_return + is_revert, FQ(1))

    if is_create + is_create2 == FQ(1):
        instruction.stack_pop()
        offset_word = instruction.stack_pop()
        size_word = instruction.stack_pop()
        constant_gas = GAS_COST_CREATE
    else:
        offset_word = instruction.stack_pop()
        size_word = instruction.stack_pop()
        constant_gas = 0

    # get gas cost of memory expansion
    offset = instruction.word_to_fq(offset_word, N_BYTES_MEMORY_ADDRESS)
    size = instruction.word_to_fq(size_word, N_BYTES_MEMORY_ADDRESS)
    (_, memory_expansion_gas_cost) = instruction.memory_expansion(offset, size)

    # check gas left is less than total gas required
    gas_not_enough, _ = instruction.compare(
        instruction.curr.gas_left, constant_gas + memory_expansion_gas_cost, N_BYTES_GAS
    )
    instruction.constrain_equal(gas_not_enough, FQ(1))

    instruction.constrain_error_state(instruction.rw_counter_offset)

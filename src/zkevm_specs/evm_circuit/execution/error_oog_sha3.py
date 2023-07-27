from zkevm_specs.util.param import (
    GAS_COST_COPY_SHA3,
    GAS_COST_SHA3,
    N_BYTES_MEMORY_WORD_SIZE,
)
from ...util import FQ
from ..instruction import Instruction
from ..opcode import Opcode
from ...util import N_BYTES_GAS


def error_oog_sha3(instruction: Instruction):
    # retrieve op code associated to oog constant error
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.SHA3)

    # pop `offset` and `size`
    offset_word = instruction.stack_pop()
    size_word = instruction.stack_pop()
    memory_offset, copy_size = instruction.memory_offset_and_length(offset_word, size_word)

    # dynamic gas cost includes memory_expansion_cost + GAS_COST_COPY_SHA3 * minimum_word_size
    _, memory_expansion_cost = instruction.memory_expansion_dynamic_length(memory_offset, copy_size)
    minimum_word_size, _ = instruction.constant_divmod(
        copy_size.expr() + 31, FQ(32), N_BYTES_MEMORY_WORD_SIZE
    )
    dynamic_gas = minimum_word_size * FQ(GAS_COST_COPY_SHA3) + memory_expansion_cost

    # check gas left is less than total gas required
    insufficient_gas, _ = instruction.compare(
        instruction.curr.gas_left, FQ(GAS_COST_SHA3) + dynamic_gas, N_BYTES_GAS
    )
    instruction.constrain_equal(insufficient_gas, FQ(1))

    instruction.constrain_error_state(
        instruction.rw_counter_offset + instruction.curr.reversible_write_counter
    )
